from odoo import Command, _, api, fields, models
from odoo.exceptions import AccessError, UserError

SYSTRAY_LIMIT = 20


class OdomateHrAnnouncement(models.Model):
    _name = 'odomate.hr.announcement'
    _description = 'HR Announcement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, date_start desc, id desc'
    _rec_name = 'title'

    reference = fields.Char(string='Reference', readonly=True, copy=False, default='/')
    title = fields.Char(string='Title', required=True, tracking=True)
    body = fields.Html(string='Announcement')
    category_id = fields.Many2one(
        comodel_name='odomate.hr.announcement.category',
        string='Category',
        ondelete='set null',
    )
    priority = fields.Selection(
        selection=[
            ('0', 'Low'),
            ('1', 'Normal'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Priority',
        default='1',
        required=True,
    )
    date_start = fields.Date(
        string='Display From',
        required=True,
        default=fields.Date.context_today,
        help="First day the announcement is visible to its audience.",
    )
    date_end = fields.Date(
        string='Display Until',
        required=True,
        help="Last day the announcement is visible to its audience.",
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('to_approve', 'Waiting for Approval'),
            ('published', 'Published'),
            ('refused', 'Refused'),
            ('expired', 'Expired'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
        tracking=True,
    )
    audience = fields.Selection(
        selection=[
            ('all', 'Everyone'),
            ('employee', 'Selected Employees'),
            ('department', 'Selected Departments'),
            ('job', 'Selected Job Positions'),
        ],
        string='Audience',
        default='all',
        required=True,
    )
    employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        relation='odomate_hr_announcement_employee_rel',
        column1='announcement_id',
        column2='employee_id',
        string='Employees',
        domain="[('company_id', '=', company_id)]",
    )
    department_ids = fields.Many2many(
        comodel_name='hr.department',
        relation='odomate_hr_announcement_department_rel',
        column1='announcement_id',
        column2='department_id',
        string='Departments',
        domain="[('company_id', '=', company_id)]",
        help="Only employees of these exact departments are addressed; "
             "sub-departments are not included.",
    )
    job_ids = fields.Many2many(
        comodel_name='hr.job',
        relation='odomate_hr_announcement_job_rel',
        column1='announcement_id',
        column2='job_id',
        string='Job Positions',
        domain="[('company_id', '=', company_id)]",
    )
    acknowledged_employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        relation='odomate_hr_announcement_ack_employee_rel',
        column1='announcement_id',
        column2='employee_id',
        string='Acknowledged By',
        copy=False,
        groups='hr.group_hr_user',
        help="Employees who pressed the Acknowledge button. This records the "
             "button press only; it is not a statement that the announcement "
             "was read and understood.",
    )
    acknowledged_count = fields.Integer(
        string='Acknowledged',
        compute='_compute_audience_figures',
        groups='hr.group_hr_user',
    )
    audience_count = fields.Integer(
        string='Audience Size',
        compute='_compute_audience_figures',
        groups='hr.group_hr_user',
    )
    pending_employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Has Not Acknowledged',
        compute='_compute_audience_figures',
        groups='hr.group_hr_user',
    )
    is_acknowledged_by_me = fields.Boolean(
        string='Acknowledged By Me',
        compute='_compute_is_acknowledged_by_me',
    )
    is_for_me = fields.Boolean(
        string='Addressed To Me',
        compute='_compute_is_for_me',
        search='_search_is_for_me',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    refuse_reason = fields.Text(string='Refusal Reason', readonly=True, copy=False)

    _check_dates = models.Constraint(
        'CHECK(date_start <= date_end)',
        "The display start date must be on or before the display end date.",
    )

    # -------------------------------------------------------------------------
    # Audience resolution - the single definition reused by the record rule,
    # the systray, hr.employee.notice_count and pending_employee_ids.
    # -------------------------------------------------------------------------

    @api.model
    def _get_current_employee(self):
        """Return the caller's own hr.employee.public records (never raises)."""
        return self.env['hr.employee.public'].search([('user_id', '=', self.env.uid)])

    @api.model
    def _get_user_audience_profile(self):
        employees = self._get_current_employee()
        return {
            'employee_ids': employees.ids,
            'department_ids': employees.department_id.ids,
            'job_ids': employees.job_id.ids,
            'company_ids': employees.company_id.ids or self.env.user.company_id.ids,
        }

    @api.model
    def _audience_match_domain(self, profile):
        return [
            '|', '|', '|',
            '&', ('audience', '=', 'all'), ('company_id', 'in', profile['company_ids']),
            '&', ('audience', '=', 'employee'), ('employee_ids', 'in', profile['employee_ids']),
            '&', ('audience', '=', 'department'), ('department_ids', 'in', profile['department_ids']),
            '&', ('audience', '=', 'job'), ('job_ids', 'in', profile['job_ids']),
        ]

    @api.model
    def _visible_domain(self):
        today = fields.Date.to_string(fields.Date.context_today(self))
        return [
            ('state', '=', 'published'),
            ('date_start', '<=', today),
            ('date_end', '>=', today),
        ]

    @api.model
    def _get_notice_domain(self, profile=None):
        if profile is None:
            profile = self._get_user_audience_profile()
        return self._visible_domain() + self._audience_match_domain(profile)

    def _get_audience_employees(self):
        self.ensure_one()
        Employee = self.env['hr.employee']
        if self.audience == 'all':
            return Employee.search([('company_id', '=', self.company_id.id)])
        if self.audience == 'employee':
            return self.employee_ids
        if self.audience == 'department' and self.department_ids:
            return Employee.search([
                ('company_id', '=', self.company_id.id),
                ('department_id', 'in', self.department_ids.ids),
            ])
        if self.audience == 'job' and self.job_ids:
            return Employee.search([
                ('company_id', '=', self.company_id.id),
                ('job_id', 'in', self.job_ids.ids),
            ])
        return Employee

    # -------------------------------------------------------------------------
    # Computed fields
    # -------------------------------------------------------------------------

    @api.depends('audience', 'employee_ids', 'department_ids', 'job_ids',
                 'acknowledged_employee_ids', 'company_id')
    def _compute_audience_figures(self):
        for announcement in self:
            employees = announcement._get_audience_employees()
            acknowledged = announcement.acknowledged_employee_ids
            announcement.audience_count = len(employees)
            announcement.acknowledged_count = len(acknowledged)
            announcement.pending_employee_ids = employees - acknowledged

    @api.depends('reference', 'title')
    def _compute_display_name(self):
        for announcement in self:
            reference = announcement.reference
            if reference and reference != '/':
                announcement.display_name = f"{reference} - {announcement.title or ''}".strip(' -')
            else:
                announcement.display_name = announcement.title or ''

    @api.depends_context('uid')
    @api.depends('acknowledged_employee_ids')
    def _compute_is_acknowledged_by_me(self):
        my_employee_ids = set(self._get_current_employee().ids)
        for announcement in self:
            acknowledged = set(announcement.sudo().acknowledged_employee_ids.ids)
            announcement.is_acknowledged_by_me = bool(my_employee_ids & acknowledged)

    @api.depends_context('uid')
    @api.depends('state', 'date_start', 'date_end', 'audience', 'employee_ids',
                 'department_ids', 'job_ids', 'company_id')
    def _compute_is_for_me(self):
        addressed = self.filtered_domain(self._get_notice_domain())
        for announcement in self:
            announcement.is_for_me = announcement in addressed

    def _search_is_for_me(self, operator, value):
        if operator in ('in', 'not in'):
            wanted = True in value
            negated = operator == 'not in'
        elif operator in ('=', '!='):
            wanted = bool(value)
            negated = operator == '!='
        else:
            return NotImplemented
        domain = self._get_notice_domain()
        if wanted != negated:
            return domain
        # sudo() here only avoids re-entering the record rule that calls this
        # method; the result is used solely as an id exclusion list.
        return [('id', 'not in', self.sudo().search(domain).ids)]

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('reference') or vals['reference'] == '/':
                vals['reference'] = self.env['ir.sequence'].sudo().next_by_code(
                    'odomate.hr.announcement') or '/'
        return super().create(vals_list)

    def copy_data(self, default=None):
        default = dict(default or {})
        default.setdefault('state', 'draft')
        default.setdefault('refuse_reason', False)
        return super().copy_data(default)

    # -------------------------------------------------------------------------
    # Workflow
    # -------------------------------------------------------------------------

    def action_send_for_approval(self):
        for announcement in self:
            if announcement.state != 'draft':
                raise UserError(_(
                    "Only a draft announcement can be sent for approval."))
        self.write({'state': 'to_approve'})
        self._schedule_approval_activity()
        return True

    def _schedule_approval_activity(self):
        manager_group = self.env.ref('hr.group_hr_manager', raise_if_not_found=False)
        if not manager_group:
            return
        managers = manager_group.sudo().all_user_ids.filtered(lambda user: user.active)
        if not managers:
            return
        for announcement in self:
            approver = managers.filtered(
                lambda user: announcement.company_id in user.company_ids
            )[:1] or managers[:1]
            announcement.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=approver.id,
                summary=_("Approve announcement %s", announcement.title),
            )

    def action_publish(self):
        if not self.env.user.has_group('hr.group_hr_manager'):
            raise AccessError(_(
                "Only an HR Administrator can publish an announcement."))
        for announcement in self:
            if announcement.state != 'to_approve':
                raise UserError(_(
                    "Only an announcement waiting for approval can be published."))
        self.write({'state': 'published'})
        return True

    def action_refuse(self):
        self.ensure_one()
        if self.state != 'to_approve':
            raise UserError(_(
                "Only an announcement waiting for approval can be refused."))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Refuse Announcement"),
            'res_model': 'odomate.hr.announcement.refuse',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_announcement_id': self.id},
        }

    def action_reset_to_draft(self):
        for announcement in self:
            if announcement.state not in ('refused', 'expired'):
                raise UserError(_(
                    "Only a refused or expired announcement can be reset to draft."))
        self.write({'state': 'draft', 'refuse_reason': False})
        return True

    def action_acknowledge(self):
        self.ensure_one()
        self.check_access('read')
        employee = self._get_current_employee()[:1]
        if not employee:
            raise UserError(_(
                "Your user account is not linked to an employee record, "
                "so the acknowledgement cannot be recorded."))
        employee_id = employee.employee_id.id or employee.id
        privileged = self.sudo()
        if employee_id not in privileged.acknowledged_employee_ids.ids:
            privileged.write({
                'acknowledged_employee_ids': [Command.link(employee_id)],
            })
        return True

    def action_open_pending_employees(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Has Not Acknowledged"),
            'res_model': 'hr.employee',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.pending_employee_ids.ids)],
        }

    # -------------------------------------------------------------------------
    # Scheduled action
    # -------------------------------------------------------------------------

    @api.model
    def _cron_expire_announcements(self):
        today = fields.Date.context_today(self)
        outdated = self.search([
            ('state', '=', 'published'),
            ('date_end', '<', today),
        ])
        if outdated:
            outdated.with_context(tracking_disable=True).write({'state': 'expired'})
        return True

    # -------------------------------------------------------------------------
    # Systray
    # -------------------------------------------------------------------------

    @api.model
    def get_systray_notices(self):
        profile = self._get_user_audience_profile()
        addressed = self.search(self._get_notice_domain(profile))
        pending = addressed.filtered(lambda a: not a.is_acknowledged_by_me)
        announcements = [{
            'id': announcement.id,
            'title': announcement.title,
            'category': announcement.category_id.name or '',
            'date_start': fields.Date.to_string(announcement.date_start),
            'priority': announcement.priority,
        } for announcement in pending[:SYSTRAY_LIMIT]]

        reminders = []
        if self.env.user.has_group('hr.group_hr_user'):
            for reminder in self.env['odomate.hr.reminder'].search([]):
                count = reminder._get_match_count()
                if count:
                    reminders.append({
                        'id': reminder.id,
                        'name': reminder.name,
                        'count': count,
                    })

        return {
            'announcements': announcements,
            'reminders': reminders,
            'announcement_count': len(pending),
            'reminder_count': len(reminders),
            'total_count': len(pending) + len(reminders),
        }

    @api.model
    def action_open_my_notices(self):
        action = self.env['ir.actions.act_window']._for_xml_id(
            'odomate_hr_notices.action_odomate_hr_announcement_my')
        return action
