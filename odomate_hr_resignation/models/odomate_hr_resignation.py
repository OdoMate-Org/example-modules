from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

RESIGNATION_STATES = [
    ('draft', "Draft"),
    ('confirmed', "Confirmed"),
    ('manager_approved', "Manager Approved"),
    ('clearance', "Clearance"),
    ('released', "Released"),
    ('refused', "Refused"),
    ('withdrawn', "Withdrawn"),
]

OPEN_STATES = ('draft', 'confirmed', 'manager_approved', 'clearance')
CLOSED_STATES = ('refused', 'withdrawn')

IMMUTABLE_AFTER_RELEASE = (
    'employee_id',
    'date_notified',
    'notice_period_days',
    'proposed_last_working_day',
    'last_working_day',
    'last_working_day_manual',
    'reason',
    'departure_reason_id',
    'release_date',
    'clearance_line_ids',
)


class OdomateHrResignation(models.Model):
    _name = 'odomate.hr.resignation'
    _description = 'Employee Resignation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_notified desc, id desc'

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: _("New"),
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Employee",
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string="Department",
        related='employee_id.department_id',
        store=True,
        readonly=True,
    )
    job_id = fields.Many2one(
        comodel_name='hr.job',
        string="Job Position",
        related='employee_id.job_id',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    date_notified = fields.Date(
        string="Notification Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        help="Date on which the employee informed the company.",
    )
    notice_period_days = fields.Integer(
        string="Notice Period (Days)",
        compute='_compute_notice_period_days',
        store=True,
        readonly=True,
        help="Contractual notice period taken from the employee's current "
             "version at the moment this resignation was created.",
    )
    proposed_last_working_day = fields.Date(
        string="Proposed Last Working Day",
        compute='_compute_proposed_last_working_day',
        store=True,
        readonly=True,
    )
    last_working_day = fields.Date(
        string="Last Working Day",
        tracking=True,
        help="Mirrors the proposed date until somebody edits it; from then on "
             "it is kept as entered.",
    )
    last_working_day_manual = fields.Boolean(
        string="Last Working Day Set Manually",
        default=False,
        copy=False,
    )
    reason = fields.Text(string="Reason", required=True)
    departure_reason_id = fields.Many2one(
        comodel_name='hr.departure.reason',
        string="Departure Reason",
        required=True,
        ondelete='restrict',
    )
    state = fields.Selection(
        selection=RESIGNATION_STATES,
        string="Status",
        default='draft',
        required=True,
        copy=False,
        tracking=True,
    )
    refusal_reason = fields.Text(string="Refusal Reason", readonly=True, copy=False)
    release_date = fields.Date(string="Release Date", readonly=True, copy=False)

    outstanding_property_count = fields.Integer(
        string="Outstanding Property",
        compute='_compute_outstanding_property_count',
    )

    exit_survey_id = fields.Many2one(
        comodel_name='survey.survey',
        string="Exit Interview",
    )
    exit_survey_input_id = fields.Many2one(
        comodel_name='survey.user_input',
        string="Exit Interview Answer",
        compute='_compute_exit_survey_input_id',
    )
    exit_survey_sent = fields.Boolean(
        string="Exit Interview Sent",
        compute='_compute_exit_survey_input_id',
    )
    exit_survey_answered = fields.Boolean(
        string="Exit Interview Answered",
        compute='_compute_exit_survey_input_id',
    )

    clearance_line_ids = fields.One2many(
        comodel_name='odomate.hr.resignation.clearance.line',
        inverse_name='resignation_id',
        string="Clearance Checklist",
        copy=False,
    )
    clearance_progress = fields.Float(
        string="Clearance Progress",
        compute='_compute_clearance_progress',
    )

    _one_open_resignation_per_employee = models.UniqueIndex(
        "(employee_id) WHERE state NOT IN ('refused', 'withdrawn')",
        "This employee already has a resignation that is not refused or withdrawn.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends('employee_id', 'employee_id.version_id', 'employee_id.version_id.notice_period')
    def _compute_notice_period_days(self):
        for resignation in self:
            version = resignation.employee_id.version_id
            resignation.notice_period_days = version.notice_period or 0

    @api.depends('date_notified', 'notice_period_days')
    def _compute_proposed_last_working_day(self):
        for resignation in self:
            if resignation.date_notified:
                resignation.proposed_last_working_day = fields.Date.add(
                    resignation.date_notified, days=resignation.notice_period_days or 0
                )
            else:
                resignation.proposed_last_working_day = False

    @api.depends('employee_id')
    def _compute_outstanding_property_count(self):
        for resignation in self:
            resignation.outstanding_property_count = len(
                resignation._get_outstanding_custody()
            )

    @api.depends('employee_id', 'exit_survey_id')
    def _compute_exit_survey_input_id(self):
        UserInput = self.env['survey.user_input'].sudo()
        for resignation in self:
            user_input = UserInput.browse()
            partner = resignation._get_exit_survey_partner()
            if resignation.exit_survey_id and partner:
                user_input = UserInput.search(
                    [
                        ('survey_id', '=', resignation.exit_survey_id.id),
                        ('partner_id', '=', partner.id),
                    ],
                    order='id desc',
                    limit=1,
                )
            resignation.exit_survey_input_id = user_input
            resignation.exit_survey_sent = bool(user_input)
            resignation.exit_survey_answered = user_input.state == 'done'

    @api.depends('clearance_line_ids', 'clearance_line_ids.state')
    def _compute_clearance_progress(self):
        for resignation in self:
            lines = resignation.clearance_line_ids
            cleared = lines.filtered(lambda line: line.state == 'cleared')
            resignation.clearance_progress = (
                100.0 * len(cleared) / len(lines) if lines else 0.0
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_outstanding_custody(self):
        """Live read of the custody register. Never written to by this module."""
        self.ensure_one()
        if not self.employee_id:
            return self.env['odomate.hr.custody'].sudo().browse()
        return self.env['odomate.hr.custody'].sudo().search(
            [
                ('employee_id', '=', self.employee_id.id),
                ('state', '=', 'approved'),
            ],
            order='return_date, id',
        )

    def _get_exit_survey_partner(self):
        self.ensure_one()
        employee = self.employee_id
        return employee.user_partner_id or employee.work_contact_id

    def _describe_outstanding_custody(self, custody_records):
        lines = []
        for custody in custody_records:
            lines.append(_(
                "- %(item)s (handover %(reference)s, due %(due_date)s)",
                item=custody.item_id.display_name or custody.reason or '',
                reference=custody.name,
                due_date=fields.Date.to_string(custody.return_date) or _("n/a"),
            ))
        return "\n".join(lines)

    def _is_hr_user(self):
        return self.env.user.has_group('hr.group_hr_user')

    def _get_line_manager_user(self):
        self.ensure_one()
        return self.employee_id.parent_id.user_id

    def _get_hr_responsible_user(self):
        self.ensure_one()
        return (
            self.employee_id.sudo().hr_responsible_id
            or self.employee_id.sudo().parent_id.user_id
            or self.env.user
        )

    def _close_open_activities(self, feedback):
        """Cancel every approval activity this module scheduled on the record."""
        for resignation in self:
            if resignation.activity_ids:
                resignation.activity_unlink(['mail.mail_activity_data_todo'])
                resignation.message_post(body=feedback)
        return True

    def _check_release_blockers(self):
        """Return the distinct, human-readable reasons blocking the release.

        Both checks are independent on purpose: the custody read is live, the
        checklist read is stored, and they are allowed to disagree.
        """
        self.ensure_one()
        blockers = []
        custody_records = self._get_outstanding_custody()
        if custody_records:
            blockers.append(_(
                "%(employee)s is still registered as holding company property. "
                "The custody register reports the following as not returned:\n%(items)s",
                employee=self.employee_id.display_name,
                items=self._describe_outstanding_custody(custody_records),
            ))
        open_lines = self.clearance_line_ids.filtered(
            lambda line: line.state != 'cleared'
        )
        if open_lines:
            labels = dict(
                self.env['odomate.hr.resignation.clearance.line']
                ._fields['state']._description_selection(self.env)
            )
            details = []
            for line in open_lines:
                details.append(_(
                    "- %(item)s (%(status)s, %(responsible)s)",
                    item=line.clearance_item_id.display_name,
                    status=labels.get(line.state, line.state),
                    responsible=line.responsible_user_id.display_name,
                ))
            details = "\n".join(details)
            blockers.append(_(
                "The exit clearance checklist is not complete. "
                "The following entries are still open:\n%(items)s",
                items=details,
            ))
        return blockers

    def _sync_last_working_day(self):
        """Mirror the proposal until a human has taken the date over."""
        for resignation in self:
            if resignation.last_working_day_manual or resignation.state == 'released':
                continue
            if resignation.last_working_day != resignation.proposed_last_working_day:
                resignation.with_context(
                    odomate_auto_last_working_day=True
                ).write({'last_working_day': resignation.proposed_last_working_day})
        return True

    # ------------------------------------------------------------------
    # ORM
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _("New")) == _("New"):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'odomate.hr.resignation'
                ) or _("New")
            if vals.get('last_working_day'):
                vals.setdefault('last_working_day_manual', True)
        self._check_no_open_resignation([
            vals['employee_id'] for vals in vals_list
            if vals.get('employee_id')
            and vals.get('state', 'draft') not in CLOSED_STATES
        ])
        resignations = super().create(vals_list)
        resignations._sync_last_working_day()
        return resignations

    def write(self, vals):
        frozen = [name for name in IMMUTABLE_AFTER_RELEASE if name in vals]
        if frozen:
            released = self.filtered(lambda record: record.state == 'released')
            if released:
                raise UserError(_(
                    "%(reference)s has already been released. Its dates, reason and "
                    "clearance checklist cannot be changed any more.",
                    reference=", ".join(released.mapped('name')),
                ))
        auto = self.env.context.get('odomate_auto_last_working_day')
        if 'last_working_day' in vals and 'last_working_day_manual' not in vals and not auto:
            vals = dict(vals, last_working_day_manual=True)
        result = super().write(vals)
        if not auto and {'date_notified', 'employee_id'} & set(vals):
            self._sync_last_working_day()
        return result

    @api.model
    def _check_no_open_resignation(self, employee_ids, exclude_ids=()):
        """Mirror the partial unique index in Python, before the row reaches
        the database. The index stays the authority under concurrency; this is
        what turns a raw integrity error into a readable message, and it also
        catches duplicates inside a single create batch."""
        seen = set()
        for employee_id in employee_ids:
            if employee_id in seen:
                raise ValidationError(_(
                    "%(employee)s cannot have two resignations recorded at once.",
                    employee=self.env['hr.employee'].sudo().browse(
                        employee_id
                    ).display_name,
                ))
            seen.add(employee_id)
        if not seen:
            return True
        domain = [
            ('employee_id', 'in', list(seen)),
            ('state', 'not in', list(CLOSED_STATES)),
        ]
        if exclude_ids:
            domain.append(('id', 'not in', list(exclude_ids)))
        clash = self.env['odomate.hr.resignation'].sudo().search(domain, limit=1)
        if clash:
            raise ValidationError(_(
                "%(employee)s already has a resignation that is neither refused "
                "nor withdrawn (%(reference)s). Close that one before recording "
                "a new one.",
                employee=clash.employee_id.display_name,
                reference=clash.name,
            ))
        return True

    @api.constrains('employee_id', 'state')
    def _check_single_open_resignation(self):
        open_records = self.filtered(
            lambda record: record.state not in CLOSED_STATES and record.employee_id
        )
        if open_records:
            self._check_no_open_resignation(
                open_records.mapped('employee_id').ids,
                exclude_ids=open_records.ids,
            )

    @api.constrains('date_notified', 'last_working_day')
    def _check_dates(self):
        for resignation in self:
            if (
                resignation.last_working_day
                and resignation.date_notified
                and resignation.last_working_day < resignation.date_notified
            ):
                raise ValidationError(_(
                    "The last working day cannot be earlier than the notification date."
                ))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_confirm(self):
        for resignation in self:
            if resignation.state != 'draft':
                raise UserError(_("Only a draft resignation can be confirmed."))
            resignation.state = 'confirmed'
            manager_user = resignation._get_line_manager_user()
            if resignation.company_id.resignation_manager_approval_required and manager_user:
                responsible = manager_user
                summary = _("Approve the resignation of %s",
                            resignation.employee_id.display_name)
            else:
                responsible = resignation._get_hr_responsible_user()
                summary = _("HR review of the resignation of %s",
                            resignation.employee_id.display_name)
            if responsible:
                resignation.activity_schedule(
                    'mail.mail_activity_data_todo',
                    date_deadline=resignation.last_working_day
                    or resignation.proposed_last_working_day,
                    user_id=responsible.id,
                    summary=summary,
                    note=_(
                        "Notified on %(notified)s, proposed last working day "
                        "%(last_day)s.",
                        notified=fields.Date.to_string(resignation.date_notified),
                        last_day=fields.Date.to_string(resignation.last_working_day) or _("n/a"),
                    ),
                )
        return True

    def action_manager_approve(self):
        for resignation in self:
            if resignation.state != 'confirmed':
                raise UserError(_(
                    "Only a confirmed resignation can be approved by the manager."
                ))
            manager_user = resignation._get_line_manager_user()
            if not (self.env.su or resignation._is_hr_user()
                    or self.env.user == manager_user):
                raise AccessError(_(
                    "Only %(manager)s or an HR officer can approve this resignation.",
                    manager=manager_user.display_name or _("the employee's manager"),
                ))
            resignation._close_open_activities(_("Approved by the manager."))
            resignation.state = 'manager_approved'
            hr_user = resignation._get_hr_responsible_user()
            if hr_user:
                resignation.activity_schedule(
                    'mail.mail_activity_data_todo',
                    date_deadline=resignation.last_working_day,
                    user_id=hr_user.id,
                    summary=_("Start the exit clearance for %s",
                              resignation.employee_id.display_name),
                )
        return True

    def action_hr_approve(self):
        for resignation in self:
            if not (self.env.su or resignation._is_hr_user()):
                raise AccessError(_(
                    "Only an HR officer can approve a resignation and open the "
                    "exit clearance."
                ))
            if resignation.state not in ('confirmed', 'manager_approved'):
                raise UserError(_(
                    "Only a confirmed or manager-approved resignation can be "
                    "approved by HR."
                ))
            if not resignation.last_working_day:
                resignation.with_context(
                    odomate_auto_last_working_day=True
                ).last_working_day = resignation.proposed_last_working_day
            resignation._close_open_activities(_("Approved by HR."))
            resignation._build_clearance_lines()
            resignation.state = 'clearance'
        return True

    def _build_clearance_lines(self):
        self.ensure_one()
        Line = self.env['odomate.hr.resignation.clearance.line']
        items = self.env['odomate.hr.clearance.item'].search(
            [
                ('active', '=', True),
                '|',
                ('company_id', '=', False),
                ('company_id', '=', self.company_id.id),
            ],
            order='sequence, id',
        )
        fallback_user = self.env.user
        already_covered = self.clearance_line_ids.clearance_item_id
        vals_list = [
            {
                'resignation_id': self.id,
                'clearance_item_id': item.id,
                'sequence': item.sequence,
                'responsible_user_id': (item.responsible_user_id or fallback_user).id,
            }
            for item in items
            if item not in already_covered
        ]
        lines = Line.create(vals_list) if vals_list else Line.browse()

        custody_records = self._get_outstanding_custody()
        if custody_records:
            property_item = self.env.ref(
                'odomate_hr_resignation.clearance_item_company_property',
                raise_if_not_found=False,
            )
            if not property_item or not property_item.active:
                property_item = items[:1]
            if property_item:
                lines |= Line.create({
                    'resignation_id': self.id,
                    'clearance_item_id': property_item.id,
                    'sequence': 1,
                    'responsible_user_id': (
                        property_item.responsible_user_id or fallback_user
                    ).id,
                    'state': 'blocked',
                    'remark': _(
                        "Company property still registered to this employee when HR "
                        "approved the resignation:\n%(items)s",
                        items=self._describe_outstanding_custody(custody_records),
                    ),
                })
            else:
                self.message_post(body=_(
                    "No clearance item is configured, so the outstanding company "
                    "property could not be snapshotted. The release check still "
                    "reads the custody register live."
                ))

        for line in lines:
            line.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=self.last_working_day,
                user_id=line.responsible_user_id.id,
                summary=_(
                    "Exit clearance: %(item)s for %(employee)s",
                    item=line.clearance_item_id.display_name,
                    employee=self.employee_id.display_name,
                ),
            )
        return lines

    def _apply_refusal(self, reason):
        self.ensure_one()
        if self.state not in ('draft', 'confirmed', 'manager_approved'):
            raise UserError(_(
                "Only a resignation that HR has not approved yet can be refused."
            ))
        self._close_open_activities(_("Resignation refused."))
        self.write({'state': 'refused', 'refusal_reason': reason})
        self.message_post(body=_("Resignation refused: %s", reason))
        return True

    def _release(self):
        self.ensure_one()
        if self.state != 'clearance':
            raise UserError(_(
                "Only a resignation whose exit clearance has been opened can be "
                "released."
            ))
        blockers = self._check_release_blockers()
        if blockers:
            raise UserError("\n\n".join(blockers))

        release_date = (
            self.last_working_day
            or self.proposed_last_working_day
            or fields.Date.context_today(self)
        )
        employee = self.employee_id
        employee.write({
            'departure_date': release_date,
            'departure_reason_id': self.departure_reason_id.id,
            'departure_description': self.reason,
        })
        version = employee.version_id
        if version and version.contract_date_start:
            version.write({'contract_date_end': release_date})
        elif version:
            self.message_post(body=_(
                "The current employee version has no contract start date, so no "
                "contract end date was set on it."
            ))
        employee.action_archive()

        user = employee.user_id
        root_id = self.env.ref('base.user_root').id
        if user and user.active and user.id not in (root_id, self.env.uid):
            user.sudo().write({'active': False})

        self.write({'state': 'released', 'release_date': release_date})
        self._close_open_activities(_("Resignation released."))
        self.clearance_line_ids.activity_unlink(['mail.mail_activity_data_todo'])
        self.message_post(body=_(
            "Released on %(release_date)s. The employee record has been archived.",
            release_date=fields.Date.to_string(release_date),
        ))
        return True

    def action_open_refuse_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Refuse Resignation"),
            'res_model': 'odomate.hr.resignation.refuse',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_resignation_id': self.id},
        }

    def action_withdraw(self):
        for resignation in self:
            if resignation.state == 'released':
                raise UserError(_(
                    "%(reference)s has already been released and can no longer be "
                    "withdrawn.",
                    reference=resignation.name,
                ))
            if resignation.state in CLOSED_STATES:
                raise UserError(_("This resignation is already closed."))
            resignation._close_open_activities(_("Resignation withdrawn."))
            resignation.state = 'withdrawn'
            resignation.message_post(body=_(
                "Resignation withdrawn. The employee record is left untouched."
            ))
        return True

    def action_release(self):
        for resignation in self:
            if not (self.env.su or resignation._is_hr_user()):
                raise AccessError(_("Only an HR officer can release an employee."))
            resignation._release()
        return True

    def action_send_exit_interview(self):
        self.ensure_one()
        if self.state not in ('manager_approved', 'clearance', 'released'):
            raise UserError(_(
                "The exit interview can only be sent once the resignation has been approved."
            ))
        if not self.exit_survey_id:
            raise UserError(_("Select an exit interview survey first."))
        partner = self._get_exit_survey_partner()
        if not partner:
            raise UserError(_(
                "%(employee)s has no work contact or user, so no exit interview "
                "invitation can be addressed.",
                employee=self.employee_id.display_name,
            ))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Send Exit Interview"),
            'res_model': 'survey.invite',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_survey_id': self.exit_survey_id.id,
                'default_partner_ids': partner.ids,
                'default_existing_mode': 'resend',
            },
        }

    def action_open_exit_interview_answer(self):
        self.ensure_one()
        if not self.exit_survey_input_id:
            raise UserError(_("The exit interview has not been answered yet."))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Exit Interview Answer"),
            'res_model': 'survey.user_input',
            'res_id': self.exit_survey_input_id.id,
            'view_mode': 'form',
        }

    def action_open_outstanding_property(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Outstanding Company Property"),
            'res_model': 'odomate.hr.custody',
            'view_mode': 'list,form',
            'domain': [
                ('employee_id', '=', self.employee_id.id),
                ('state', '=', 'approved'),
            ],
            'context': {'create': False},
        }

    # ------------------------------------------------------------------
    # Cron
    # ------------------------------------------------------------------
    @api.model
    def _cron_release_resignations(self):
        candidates = self.search([
            ('state', '=', 'clearance'),
            ('last_working_day', '!=', False),
            ('last_working_day', '<=', fields.Date.context_today(self)),
        ])
        for resignation in candidates:
            if resignation._check_release_blockers():
                continue
            resignation._release()
        return True

    # ------------------------------------------------------------------
    # Demo
    # ------------------------------------------------------------------
    @api.model
    def _populate_demo_data(self):
        """Attach demo resignations to whichever employees this database has.

        Demo employee XML ids differ between Odoo builds, so the records are
        resolved at load time instead of being referenced statically.
        """
        Employee = self.env['hr.employee']
        reason = self.env['hr.departure.reason'].search([], limit=1)
        if not reason:
            reason = self.env['hr.departure.reason'].create({'name': "Resigned"})
        today = fields.Date.context_today(self)
        taken = self.search([('state', 'not in', list(CLOSED_STATES))]).employee_id

        custody = self.env['odomate.hr.custody'].sudo().search(
            [('state', '=', 'approved')], order='return_date, id', limit=1
        )
        holder = custody.employee_id if custody.employee_id not in taken else Employee
        if holder:
            resignation = self.create({
                'employee_id': holder.id,
                'company_id': holder.company_id.id,
                'date_notified': today - timedelta(days=20),
                'reason': "Relocating to another city; leaving on good terms.",
                'departure_reason_id': reason.id,
            })
            resignation.action_confirm()
            resignation.action_manager_approve()
            resignation.action_hr_approve()
            taken |= holder

        # A plain draft resignation to exercise the list/statusbar.
        draft_employee = Employee.search([('id', 'not in', taken.ids)], limit=1)
        if draft_employee:
            self.create({
                'employee_id': draft_employee.id,
                'company_id': draft_employee.company_id.id,
                'date_notified': today - timedelta(days=2),
                'reason': "Accepted an offer elsewhere.",
                'departure_reason_id': reason.id,
            })
            taken |= draft_employee

        # A fully released resignation, walked through the SAME workflow the
        # button uses so all release side-effects actually run (departure fields
        # written on hr.employee, contract ended, employee + login archived).
        # The employee must hold no outstanding approved custody, otherwise the
        # live release check would (correctly) block the release.
        custody_holders = self.env['odomate.hr.custody'].sudo().search(
            [('state', '=', 'approved')]
        ).employee_id
        retiree = Employee.search(
            [('id', 'not in', (taken | custody_holders).ids)], limit=1
        )
        if retiree:
            release_date = today - timedelta(days=5)
            released = self.create({
                'employee_id': retiree.id,
                'company_id': retiree.company_id.id,
                'date_notified': today - timedelta(days=65),
                'last_working_day': release_date,
                'reason': "Retirement after many years of service.",
                'departure_reason_id': reason.id,
            })
            released.action_confirm()
            if released.state == 'confirmed':
                released.action_hr_approve()
            released.clearance_line_ids.write({
                'state': 'cleared',
                'cleared_date': release_date,
            })
            released._release()
        return True
