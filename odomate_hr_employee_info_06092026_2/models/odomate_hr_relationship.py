from odoo import fields, models


class OdomateHrRelationship(models.Model):
    _name = 'odomate.hr.relationship'
    _description = "Employee Dependant Relationship"
    _order = 'name'

    name = fields.Char(
        string="Relationship",
        required=True,
        help="Label shown when picking the link between an employee and a dependant, "
             "for example Spouse, Father or Guardian.",
    )
    active = fields.Boolean(
        default=True,
        help="Archived relationships stay on existing dependants but can no longer be selected.",
    )

    _name_uniq = models.Constraint(
        'UNIQUE(name)',
        "A relationship with this name already exists.",
    )
