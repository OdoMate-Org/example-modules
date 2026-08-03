from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    so_double_validation = fields.Selection(
        selection=[
            ('one_step', "Confirm directly"),
            ('two_step', "Get approval for large discounts"),
        ],
        string="Discount Approval",
        default='one_step',
    )
    so_double_validation_limit = fields.Float(
        string="Discount Approval Limit",
        help="Average line discount (in percent) above which a sale order "
             "requires a Sales Manager approval before it can be confirmed.",
        default=0.0,
    )
