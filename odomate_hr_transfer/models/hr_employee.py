from odoo import _, api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    odomate_transfer_ids = fields.One2many(
        'odomate.hr.transfer', 'employee_id', string='Transfers')
    odomate_transfer_count = fields.Integer(
        string='Transfer Count', compute='_compute_odomate_transfer_count')

    @api.depends('odomate_transfer_ids')
    def _compute_odomate_transfer_count(self):
        for employee in self:
            employee.odomate_transfer_count = len(employee.odomate_transfer_ids)

    def action_open_odomate_transfers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Transfers'),
            'res_model': 'odomate.hr.transfer',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
