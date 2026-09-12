import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

TARGET_TO_CURRENT = {
    'new_department_id': 'current_department_id',
    'new_job_id': 'current_job_id',
    'new_work_location_id': 'current_work_location_id',
    'new_parent_id': 'current_parent_id',
    'new_company_id': 'current_company_id',
}

TARGET_TO_VERSION = {
    'new_department_id': 'department_id',
    'new_job_id': 'job_id',
    'new_work_location_id': 'work_location_id',
}

TARGET_TO_EMPLOYEE = {
    'new_parent_id': 'parent_id',
    'new_company_id': 'company_id',
}

LOCKED_AFTER_APPLY = ('state', 'effective_date', 'employee_id') + tuple(TARGET_TO_CURRENT)

APPROVAL_ACTIVITY = 'mail.mail_activity_data_todo'


class OdomateHrTransfer(models.Model):
    _name = 'odomate.hr.transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee Transfer'
    _order = 'effective_date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        copy=False,
        index=True,
        default='/',
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    effective_date = fields.Date(
        string='Effective Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    reason = fields.Text(string='Reason')

    new_department_id = fields.Many2one(
        'hr.department', string='To Department', ondelete='restrict', tracking=True)
    new_job_id = fields.Many2one(
        'hr.job', string='To Job Position', ondelete='restrict', tracking=True)
    new_work_location_id = fields.Many2one(
        'hr.work.location', string='To Work Location', ondelete='restrict', tracking=True)
    new_parent_id = fields.Many2one(
        'hr.employee', string='To Manager', ondelete='restrict', tracking=True)
    new_company_id = fields.Many2one(
        'res.company', string='To Company', ondelete='restrict', tracking=True)

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('to_approve', 'To Approve'),
            ('approved', 'Approved'),
            ('applied', 'Applied'),
            ('refused', 'Refused'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
        tracking=True,
    )
    applied_date = fields.Datetime(string='Applied On', readonly=True, copy=False)
    version_id = fields.Many2one(
        'hr.version', string='Created Version', readonly=True, copy=False, ondelete='set null')
    refuse_reason = fields.Text(string='Refusal Reason', readonly=True, copy=False)

    current_department_id = fields.Many2one(
        'hr.department', string='From Department', compute='_compute_current_values', store=True)
    current_job_id = fields.Many2one(
        'hr.job', string='From Job Position', compute='_compute_current_values', store=True)
    current_work_location_id = fields.Many2one(
        'hr.work.location', string='From Work Location', compute='_compute_current_values', store=True)
    current_parent_id = fields.Many2one(
        'hr.employee', string='From Manager', compute='_compute_current_values', store=True)
    current_company_id = fields.Many2one(
        'res.company', string='From Company', compute='_compute_current_values', store=True)

    apply_ready = fields.Boolean(
        string='Effective Date Reached', compute='_compute_apply_ready')

    @api.depends(
        'employee_id.department_id',
        'employee_id.job_id',
        'employee_id.work_location_id',
        'employee_id.parent_id',
        'employee_id.company_id',
    )
    def _compute_current_values(self):
        for transfer in self:
            if transfer.state == 'applied':
                # Frozen "from" snapshot taken by _apply_transfer(); a later
                # change to the employee must not overwrite it.
                continue
            employee = transfer.employee_id
            transfer.current_department_id = employee.department_id
            transfer.current_job_id = employee.job_id
            transfer.current_work_location_id = employee.work_location_id
            transfer.current_parent_id = employee.parent_id
            transfer.current_company_id = employee.company_id

    @api.depends('effective_date')
    def _compute_apply_ready(self):
        today = fields.Date.context_today(self)
        for transfer in self:
            transfer.apply_ready = bool(
                transfer.effective_date and transfer.effective_date <= today)

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains(
        'employee_id',
        'new_department_id',
        'new_job_id',
        'new_work_location_id',
        'new_parent_id',
        'new_company_id',
    )
    def _check_transfer_changes_something(self):
        for transfer in self:
            targets = [name for name in TARGET_TO_CURRENT if transfer[name]]
            if not targets:
                raise ValidationError(_(
                    "Transfer %s must change at least one of department, job "
                    "position, work location, manager or company.",
                    transfer.name,
                ))
            if transfer.state == 'applied':
                continue
            for target in targets:
                if transfer[target] == transfer[TARGET_TO_CURRENT[target]]:
                    raise ValidationError(_(
                        "%(label)s is already %(value)s for %(employee)s. "
                        "A transfer must record an actual change.",
                        label=transfer._fields[target].get_description(self.env)['string'],
                        value=transfer[target].display_name,
                        employee=transfer.employee_id.display_name,
                    ))

    @api.constrains('employee_id', 'effective_date')
    def _check_effective_date_after_last_version(self):
        for transfer in self:
            if transfer.state == 'applied' or not transfer.effective_date:
                continue
            last_version_date = transfer._get_last_version().date_version
            if last_version_date and transfer.effective_date <= last_version_date:
                raise ValidationError(_(
                    "The effective date of transfer %(name)s must be later than "
                    "%(date)s, the date of the most recent version of %(employee)s.",
                    name=transfer.name,
                    date=last_version_date,
                    employee=transfer.employee_id.display_name,
                ))

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'odomate.hr.transfer') or '/'
        return super().create(vals_list)

    def write(self, vals):
        if any(field_name in vals for field_name in LOCKED_AFTER_APPLY):
            applied = self.filtered(lambda transfer: transfer.state == 'applied')
            if applied:
                raise UserError(_(
                    "Transfer %s has already been applied and can no longer be "
                    "changed. Record a new transfer to reverse or correct this move.",
                    ', '.join(applied.mapped('name')),
                ))
        return super().write(vals)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_last_version(self):
        self.ensure_one()
        if not self.employee_id:
            return self.env['hr.version']
        return self.env['hr.version'].search(
            [('employee_id', '=', self.employee_id.id)],
            order='date_version desc, id desc',
            limit=1,
        )

    def _get_approver_users(self):
        self.ensure_one()
        group = self.env.ref('hr.group_hr_manager', raise_if_not_found=False)
        if not group:
            return self.env['res.users']
        companies = self.employee_id.company_id | self.new_company_id
        candidates = group.sudo().all_user_ids.filtered(
            lambda user: user.active and not user.share)
        return candidates.filtered(
            lambda user: all(company in user.company_ids for company in companies))

    def _schedule_approval_activities(self):
        self.ensure_one()
        approvers = self._get_approver_users()
        if not approvers:
            _logger.info(
                "No HR Manager with access to the companies of transfer %s: "
                "no approval activity scheduled.", self.name)
            return
        summary = _("Approve employee transfer %s", self.name)
        for approver in approvers:
            self.activity_schedule(
                APPROVAL_ACTIVITY,
                date_deadline=self.effective_date,
                summary=summary,
                user_id=approver.id,
            )

    def _close_approval_activities(self, feedback):
        for transfer in self:
            transfer.activity_feedback(
                [APPROVAL_ACTIVITY], feedback=feedback, only_automated=False)

    def _check_approval_rights(self):
        self.ensure_one()
        if self.env.su:
            return
        if not self.env.user.has_group('hr.group_hr_manager'):
            raise AccessError(_(
                "Only an HR Manager can approve employee transfer %s.", self.name))
        if self.new_company_id and self.new_company_id not in self.env.user.company_ids:
            raise AccessError(_(
                "You cannot approve transfer %(name)s: it moves the employee to "
                "%(company)s, which is not one of your allowed companies.",
                name=self.name,
                company=self.new_company_id.sudo().display_name,
            ))

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_send_for_approval(self):
        for transfer in self:
            if transfer.state != 'draft':
                raise UserError(_(
                    "Only a draft transfer can be sent for approval; %s is not draft.",
                    transfer.name,
                ))
        self.write({'state': 'to_approve'})
        for transfer in self:
            transfer._schedule_approval_activities()
        return True

    def action_approve(self):
        for transfer in self:
            if transfer.state != 'to_approve':
                raise UserError(_(
                    "Only a transfer waiting for approval can be approved; "
                    "%s is not waiting for approval.",
                    transfer.name,
                ))
            transfer._check_approval_rights()
        self.write({'state': 'approved'})
        self._close_approval_activities(_("Transfer approved."))
        return True

    def action_cancel(self):
        for transfer in self:
            if transfer.state not in ('draft', 'to_approve', 'approved'):
                raise UserError(_(
                    "Transfer %s can no longer be cancelled.", transfer.name))
        self.write({'state': 'cancelled'})
        self._close_approval_activities(_("Transfer cancelled."))
        return True

    def action_refuse(self):
        self.ensure_one()
        if self.state not in ('draft', 'to_approve'):
            raise UserError(_(
                "Transfer %s can no longer be refused.", self.name))
        # Return the XML-defined act_window so the dialog title comes from the
        # action's stored `name` (a model-term translation loaded from the .po),
        # which translates per user language — unlike a code (_()) string that a
        # long-running server may not hot-reload.
        action = self.env['ir.actions.act_window']._for_xml_id(
            'odomate_hr_transfer.action_odomate_hr_transfer_refuse')
        action['context'] = {'default_transfer_id': self.id}
        return action

    def _register_refusal(self, refuse_reason):
        self.ensure_one()
        if self.state not in ('draft', 'to_approve'):
            raise UserError(_(
                "Transfer %s can no longer be refused.", self.name))
        self.write({'refuse_reason': refuse_reason, 'state': 'refused'})
        self._close_approval_activities(
            _("Transfer refused: %s", refuse_reason))
        return True

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    def action_apply(self):
        today = fields.Date.context_today(self)
        for transfer in self:
            if transfer.state != 'approved':
                raise UserError(_(
                    "Transfer %s must be approved before it can be applied.",
                    transfer.name,
                ))
            if transfer.effective_date > today:
                raise UserError(_(
                    "Transfer %(name)s takes effect on %(date)s and cannot be "
                    "applied before that date.",
                    name=transfer.name,
                    date=transfer.effective_date,
                ))
            transfer._apply_transfer()
        return True

    def _prepare_version_vals(self, source_version):
        self.ensure_one()
        vals = source_version.sudo().copy_data()[0] if source_version else {}
        vals.pop('company_id', None)
        vals.update({
            'employee_id': self.employee_id.id,
            'date_version': self.effective_date,
        })
        for target, version_field in TARGET_TO_VERSION.items():
            if self[target]:
                vals[version_field] = self[target].id
        return vals

    def _apply_transfer(self):
        self.ensure_one()
        employee = self.employee_id
        # Snapshot the "from" side before anything is written: creating the
        # new hr.version (and, below, writing the employee) can immediately
        # change what employee_id.department_id/job_id/... resolve to.
        current_snapshot = {
            'current_department_id': employee.department_id.id,
            'current_job_id': employee.job_id.id,
            'current_work_location_id': employee.work_location_id.id,
            'current_parent_id': employee.parent_id.id,
            'current_company_id': employee.company_id.id,
        }
        version_vals = self._prepare_version_vals(
            employee.current_version_id or self._get_last_version())
        version = self.env['hr.version'].sudo().create(version_vals)

        employee_vals = {
            employee_field: self[target].id
            for target, employee_field in TARGET_TO_EMPLOYEE.items()
            if self[target]
        }
        if employee_vals:
            employee.sudo().write(employee_vals)

        self.write({
            'version_id': version.id,
            'applied_date': fields.Datetime.now(),
            'state': 'applied',
            **current_snapshot,
        })
        self.message_post(body=_(
            "Transfer applied: a new version dated %s was added to the "
            "employee's history.", self.effective_date))
        return version

    @api.model
    def _cron_apply_due_transfers(self):
        today = fields.Date.context_today(self)
        due_transfers = self.search([
            ('state', '=', 'approved'),
            ('effective_date', '<=', today),
        ])
        for transfer in due_transfers:
            try:
                with self.env.cr.savepoint():
                    transfer.action_apply()
            except (UserError, ValidationError, AccessError) as error:
                _logger.warning(
                    "Employee transfer %s could not be applied automatically: %s",
                    transfer.name, error)
        return True
