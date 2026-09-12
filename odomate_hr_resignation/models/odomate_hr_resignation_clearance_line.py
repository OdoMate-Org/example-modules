from odoo import _, api, fields, models
from odoo.exceptions import UserError

CLEARANCE_LINE_STATES = [
    ('pending', "Pending"),
    ('cleared', "Cleared"),
    ('blocked', "Blocked"),
]

IMMUTABLE_AFTER_RELEASE = (
    'resignation_id',
    'clearance_item_id',
    'responsible_user_id',
    'state',
    'remark',
    'cleared_date',
)


class OdomateHrResignationClearanceLine(models.Model):
    _name = 'odomate.hr.resignation.clearance.line'
    _description = 'Resignation Clearance Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'resignation_id, sequence, id'

    resignation_id = fields.Many2one(
        comodel_name='odomate.hr.resignation',
        string="Resignation",
        required=True,
        ondelete='cascade',
        index=True,
    )
    clearance_item_id = fields.Many2one(
        comodel_name='odomate.hr.clearance.item',
        string="Clearance Item",
        required=True,
        ondelete='restrict',
    )
    sequence = fields.Integer(default=10)
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Employee",
        related='resignation_id.employee_id',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        related='resignation_id.company_id',
        store=True,
        readonly=True,
    )
    responsible_user_id = fields.Many2one(
        comodel_name='res.users',
        string="Responsible",
        required=True,
        index=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=CLEARANCE_LINE_STATES,
        string="Status",
        default='pending',
        required=True,
        tracking=True,
    )
    remark = fields.Text(string="Remark")
    cleared_date = fields.Date(string="Cleared On", readonly=True)

    @api.depends('clearance_item_id', 'employee_id')
    def _compute_display_name(self):
        for line in self:
            item = line.clearance_item_id.name or _("Clearance")
            employee = line.employee_id.name
            line.display_name = f"{item} - {employee}" if employee else item

    def _may_edit(self):
        self.ensure_one()
        return (
            self.env.su
            or self.env.user.has_group('hr.group_hr_user')
            or self.responsible_user_id == self.env.user
        )

    def _check_editable(self):
        for line in self:
            if not line._may_edit():
                raise UserError(_(
                    "Only %(responsible)s or an HR officer can update this "
                    "clearance line.",
                    responsible=line.responsible_user_id.display_name,
                ))
        return True

    def write(self, vals):
        frozen = [name for name in IMMUTABLE_AFTER_RELEASE if name in vals]
        if frozen and any(
            line.sudo().resignation_id.state == 'released' for line in self
        ):
            raise UserError(_(
                "The exit clearance of a released resignation can no longer be "
                "changed."
            ))
        if not self.env.su and {'state', 'remark', 'cleared_date'} & set(vals):
            self._check_editable()
        return super().write(vals)

    def action_set_cleared(self):
        self._check_editable()
        self.write({
            'state': 'cleared',
            'cleared_date': fields.Date.context_today(self),
        })
        self.activity_unlink(['mail.mail_activity_data_todo'])
        return True

    def action_set_blocked(self):
        self._check_editable()
        for line in self:
            if not (line.remark or '').strip():
                raise UserError(_(
                    "Add a remark explaining what blocks %(item)s before marking "
                    "it as blocked.",
                    item=line.clearance_item_id.display_name,
                ))
        self.write({'state': 'blocked', 'cleared_date': False})
        return True

    def action_reset_pending(self):
        self._check_editable()
        self.write({'state': 'pending', 'cleared_date': False})
        return True
