from odoo import _, api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    custody_count = fields.Integer(
        string="Custody Records",
        compute='_compute_custody_count',
    )
    custody_current_count = fields.Integer(
        string="Items Currently Held",
        compute='_compute_custody_count',
    )

    @api.depends_context('company')
    def _compute_custody_count(self):
        self.custody_count = 0
        self.custody_current_count = 0
        if not self.ids:
            return
        Custody = self.env['odomate.hr.custody']
        if not Custody.has_access('read'):
            return
        grouped = Custody._read_group(
            [('employee_id', 'in', self.ids)],
            groupby=['employee_id', 'state'],
            aggregates=['__count'],
        )
        totals = dict.fromkeys(self.ids, 0)
        current = dict.fromkeys(self.ids, 0)
        for employee, state, count in grouped:
            totals[employee.id] = totals.get(employee.id, 0) + count
            if state == 'approved':
                current[employee.id] = current.get(employee.id, 0) + count
        for employee in self:
            employee.custody_count = totals.get(employee.id, 0)
            employee.custody_current_count = current.get(employee.id, 0)

    def action_open_custody_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Custody Requests"),
            'res_model': 'odomate.hr.custody',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    def action_open_current_custody(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Items Currently Held"),
            'res_model': 'odomate.hr.custody',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id), ('state', '=', 'approved')],
            'context': {'default_employee_id': self.id},
        }
