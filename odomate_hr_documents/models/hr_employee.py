from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    document_ids = fields.One2many(
        'odomate.hr.document',
        'employee_id',
        string="Documents",
        groups='hr.group_hr_user',
    )
    document_count = fields.Integer(
        string="Document Count",
        compute='_compute_document_count',
        groups='hr.group_hr_user',
    )

    @api.depends('document_ids')
    def _compute_document_count(self):
        for employee in self:
            employee.document_count = len(employee.document_ids)

    def action_view_employee_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._("Employee Documents"),
            'res_model': 'odomate.hr.document',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
