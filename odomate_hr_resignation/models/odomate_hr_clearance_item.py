from odoo import fields, models


class OdomateHrClearanceItem(models.Model):
    _name = 'odomate.hr.clearance.item'
    _description = 'Exit Clearance Item'
    _order = 'sequence, name, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    responsible_user_id = fields.Many2one(
        comodel_name='res.users',
        string="Default Responsible",
        domain=[('share', '=', False)],
        help="User who is asked to clear this item. When empty, the HR user who "
             "approves the resignation is used instead.",
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        default=lambda self: self.env.company,
        help="Leave empty to make this clearance item available to every company.",
    )
    active = fields.Boolean(default=True)

    _name_company_uniq = models.UniqueIndex(
        "(name, company_id) WHERE company_id IS NOT NULL",
        "A clearance item with this name already exists for this company.",
    )
    _name_global_uniq = models.UniqueIndex(
        "(name) WHERE company_id IS NULL",
        "A global clearance item with this name already exists.",
    )
