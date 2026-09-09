from odoo import _, api, fields, models, Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import format_date

CUSTODY_STATES = [
    ('draft', "Draft"),
    ('waiting_approval', "Waiting Approval"),
    ('approved', "Approved"),
    ('returned', "Returned"),
    ('refused', "Refused"),
]


class OdomateHrCustody(models.Model):
    _name = 'odomate.hr.custody'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Custody Request'
    _order = 'request_date desc, id desc'

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
        index=True,
        tracking=True,
        default=lambda self: self._default_employee_id(),
    )
    item_id = fields.Many2one(
        comodel_name='odomate.hr.custody.item',
        string="Item",
        required=True,
        index=True,
        tracking=True,
        ondelete='restrict',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    reason = fields.Char(string="Reason", required=True, tracking=True)
    request_date = fields.Date(
        string="Request Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    return_date = fields.Date(
        string="Return Date",
        required=True,
        tracking=True,
        help="Date on which the employee undertakes to return the item.",
    )
    actual_return_date = fields.Date(
        string="Actual Return Date",
        readonly=True,
        copy=False,
        tracking=True,
    )
    notes = fields.Text(string="Notes")
    state = fields.Selection(
        selection=CUSTODY_STATES,
        string="Status",
        default='draft',
        required=True,
        copy=False,
        tracking=True,
    )
    is_extension = fields.Boolean(
        string="Pending Extension",
        default=False,
        copy=False,
        help="Set while an extension of the return date is waiting for approval. "
             "A request in this situation can only be approved or refused.",
    )
    extend_new_return_date = fields.Date(
        string="Proposed Return Date",
        copy=False,
        help="Return date proposed by the employee. It replaces the return date "
             "only once the extension is approved.",
    )
    refusal_reason = fields.Text(string="Refusal Reason", copy=False)
    extension_refusal_reason = fields.Text(
        string="Extension Refusal Reason",
        copy=False,
    )
    is_overdue = fields.Boolean(
        string="Overdue",
        compute='_compute_is_overdue',
    )

    _check_return_after_request = models.Constraint(
        'CHECK(return_date >= request_date)',
        "The return date cannot be earlier than the request date.",
    )
    _unique_approved_item = models.UniqueIndex(
        "(item_id) WHERE state = 'approved'",
    )

    @api.model
    def _default_employee_id(self):
        return self.env['hr.employee'].sudo().search([
            ('user_id', '=', self.env.uid),
            ('company_id', 'in', self.env.companies.ids),
        ], limit=1).id or False

    @api.depends('state', 'return_date')
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for record in self:
            record.is_overdue = bool(
                record.state == 'approved'
                and record.return_date
                and record.return_date < today
            )

    @api.constrains('request_date', 'return_date')
    def _check_dates(self):
        for record in self:
            if record.return_date and record.request_date and record.return_date < record.request_date:
                raise ValidationError(_("The return date cannot be earlier than the request date."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _("New"):
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code(
                    'odomate.hr.custody'
                ) or _("New")
        return super().create(vals_list)

    def _check_custody_officer_rights(self):
        if self.env.su or self.env.user.has_group('hr.group_hr_user'):
            return
        raise AccessError(_(
            "Only members of the Employees / Officer group may approve, refuse "
            "or close a custody request."
        ))

    def _check_no_other_holder(self):
        self.ensure_one()
        conflict = self.sudo().search([
            ('item_id', '=', self.item_id.id),
            ('state', '=', 'approved'),
            ('id', '!=', self.id),
        ], limit=1)
        if conflict:
            raise UserError(_(
                "%(item)s is already in the custody of %(holder)s under request "
                "%(reference)s. Close that request before approving this one.",
                item=self.item_id.name,
                holder=conflict.employee_id.name or _("another employee"),
                reference=conflict.name,
            ))

    def action_send_for_approval(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Only a draft request can be sent for approval."))
            record.write({'state': 'waiting_approval', 'is_extension': False})
        return True

    def action_approve(self):
        self._check_custody_officer_rights()
        for record in self:
            if record.state != 'waiting_approval':
                raise UserError(_("Only a request waiting for approval can be approved."))
            record._check_no_other_holder()
            if record.is_extension:
                new_date = record.extend_new_return_date
                record.write({
                    'return_date': new_date or record.return_date,
                    'extend_new_return_date': False,
                    'is_extension': False,
                    'state': 'approved',
                })
                record.message_post(body=_(
                    "Extension approved. New return date: %(date)s.",
                    date=format_date(self.env, new_date) if new_date else '-',
                ))
            else:
                record.write({'state': 'approved'})
                record.message_post(body=_("Custody request approved."))
        return True

    def action_open_refuse_wizard(self):
        self.ensure_one()
        self._check_custody_officer_rights()
        if self.state != 'waiting_approval':
            raise UserError(_("Only a request waiting for approval can be refused."))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Refuse Extension") if self.is_extension else _("Refuse Custody Request"),
            'res_model': 'odomate.hr.custody.refuse',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id, 'active_model': self._name},
        }

    def action_open_extend_wizard(self):
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_("Only an item currently in custody can have its return date extended."))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Extend Return Date"),
            'res_model': 'odomate.hr.custody.extend',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id, 'active_model': self._name},
        }

    def action_returned(self):
        self._check_custody_officer_rights()
        for record in self:
            if record.state != 'approved':
                raise UserError(_("Only an item currently in custody can be marked as returned."))
            record.write({
                'state': 'returned',
                'actual_return_date': fields.Date.context_today(record),
            })
        return True

    def action_set_to_draft(self):
        for record in self:
            if record.is_extension:
                raise UserError(_(
                    "A request with a pending extension cannot be set back to draft. "
                    "Approve or refuse the extension instead."
                ))
            if record.state not in ('waiting_approval', 'refused'):
                raise UserError(_(
                    "Only a request that has never been approved can be set back to draft."
                ))
            values = {'state': 'draft'}
            if record.refusal_reason:
                record.message_post(body=_(
                    "Reset to draft. Previous refusal reason: %(reason)s",
                    reason=record.refusal_reason,
                ))
                values['refusal_reason'] = False
            record.write(values)
        return True

    def _get_reminder_partner(self):
        self.ensure_one()
        return self.employee_id.user_id.partner_id or self.employee_id.work_contact_id

    def _send_return_reminder(self):
        template = self.env.ref(
            'odomate_hr_custody.mail_template_custody_return_reminder',
            raise_if_not_found=False,
        )
        if not template:
            return self.browse()
        notified = self.browse()
        for record in self:
            partner = record.sudo()._get_reminder_partner()
            if not partner:
                continue
            template.sudo().send_mail(
                record.id,
                force_send=False,
                email_values={'recipient_ids': [Command.set(partner.ids)]},
            )
            notified |= record
        return notified

    def action_send_reminder(self):
        self._check_custody_officer_rights()
        for record in self:
            if record.state != 'approved':
                raise UserError(_(
                    "A reminder can only be sent for an item currently in custody."
                ))
        notified = self._send_return_reminder()
        if not notified:
            raise UserError(_(
                "No reminder could be sent: the employee has no linked user and no "
                "work contact to send the email to."
            ))
        return True

    @api.model
    def _get_requests_due_for_reminder(self):
        limit_date = fields.Date.add(fields.Date.context_today(self), days=1)
        return self.search([
            ('state', '=', 'approved'),
            ('return_date', '<=', limit_date),
        ])

    @api.model
    def _cron_send_return_reminders(self):
        requests = self._get_requests_due_for_reminder()
        if requests:
            requests._send_return_reminder()
        return True
