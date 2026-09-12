from odoo import _, api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    resignation_ids = fields.One2many(
        comodel_name='odomate.hr.resignation',
        inverse_name='employee_id',
        string="Resignations",
        groups='hr.group_hr_user',
    )
    active_resignation_id = fields.Many2one(
        comodel_name='odomate.hr.resignation',
        string="Ongoing Resignation",
        compute='_compute_active_resignation_id',
        groups='hr.group_hr_user',
    )
    resignation_count = fields.Integer(
        string="Resignation Count",
        compute='_compute_active_resignation_id',
        groups='hr.group_hr_user',
    )
    @api.depends('resignation_ids', 'resignation_ids.state')
    def _compute_active_resignation_id(self):
        for employee in self:
            ongoing = employee.resignation_ids.filtered(
                lambda resignation: resignation.state not in ('refused', 'withdrawn', 'released')
            )
            employee.active_resignation_id = ongoing[:1]
            employee.resignation_count = len(employee.resignation_ids)

    def action_open_outstanding_property(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Outstanding Company Property"),
            'res_model': 'odomate.hr.custody',
            'view_mode': 'list,form',
            'domain': [
                ('employee_id', '=', self.id),
                ('state', '=', 'approved'),
            ],
            'context': {'create': False},
        }

    def action_open_resignations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Resignations"),
            'res_model': 'odomate.hr.resignation',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
