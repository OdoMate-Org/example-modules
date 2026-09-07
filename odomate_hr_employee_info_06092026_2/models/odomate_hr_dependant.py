from odoo import api, fields, models


class OdomateHrDependant(models.Model):
    _name = 'odomate.hr.dependant'
    _description = "Employee Dependant"
    _order = 'employee_id, name'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Employee",
        required=True,
        ondelete='cascade',
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        related='employee_id.company_id',
        store=True,
        index=True,
    )
    name = fields.Char(
        string="Name",
        required=True,
    )
    relationship_id = fields.Many2one(
        comodel_name='odomate.hr.relationship',
        string="Relationship",
        required=True,
        ondelete='restrict',
    )
    phone = fields.Char(string="Phone")
    birthdate = fields.Date(string="Date of Birth")
    is_emergency_contact = fields.Boolean(
        string="Emergency Contact",
        default=False,
        help="Only one dependant per employee can be the emergency contact. Ticking this box "
             "unticks the others and copies the name and phone onto the employee record.",
    )

    _emergency_contact_uniq = models.UniqueIndex(
        "(employee_id) WHERE is_emergency_contact IS TRUE"
    )

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [dict(vals) for vals in vals_list]
        winner_index_by_employee = {}
        for index, vals in enumerate(vals_list):
            if vals.get('is_emergency_contact') and vals.get('employee_id'):
                winner_index_by_employee[vals['employee_id']] = index
        for index, vals in enumerate(vals_list):
            if vals.get('is_emergency_contact') and winner_index_by_employee.get(vals.get('employee_id')) != index:
                vals['is_emergency_contact'] = False
        self._odomate_release_emergency_slot(list(winner_index_by_employee))
        dependants = super().create(vals_list)
        dependants._odomate_apply_emergency_contact()
        return dependants

    def write(self, vals):
        if vals.get('is_emergency_contact') and len(self) > 1:
            for dependant in self:
                dependant.write(vals)
            return True
        if vals.get('is_emergency_contact'):
            employee_ids = [vals['employee_id']] if vals.get('employee_id') else self.employee_id.ids
            self._odomate_release_emergency_slot(employee_ids, keep_ids=self.ids)
        res = super().write(vals)
        if {'is_emergency_contact', 'name', 'phone', 'employee_id'} & set(vals):
            self._odomate_apply_emergency_contact()
        return res

    def _odomate_release_emergency_slot(self, employee_ids, keep_ids=()):
        """Unflag every other emergency contact of the given employees, and flush.

        Called before the row is inserted or updated so the partial unique index
        on ``(employee_id) WHERE is_emergency_contact`` never sees two live rows.
        """
        employee_ids = [employee_id for employee_id in set(employee_ids) if employee_id]
        if not employee_ids:
            return
        domain = [
            ('employee_id', 'in', employee_ids),
            ('is_emergency_contact', '=', True),
        ]
        if keep_ids:
            domain.append(('id', 'not in', list(keep_ids)))
        conflicting = self.sudo().search(domain)
        if conflicting:
            conflicting.write({'is_emergency_contact': False})
            conflicting.flush_recordset(['is_emergency_contact'])

    def _odomate_apply_emergency_contact(self):
        """Copy the flagged dependant onto ``hr.employee.emergency_contact``/``emergency_phone``."""
        for dependant in self.filtered('is_emergency_contact'):
            employee = dependant.employee_id
            if not employee:
                continue
            employee.sudo().write({
                'emergency_contact': dependant.name,
                'emergency_phone': dependant.phone or False,
            })
