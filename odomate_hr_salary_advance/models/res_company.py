from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    advance_max_percent = fields.Float(
        string="Max Advance (% of Monthly Salary)",
        default=50.0,
        help="Share of the employee's monthly salary that may be advanced. "
             "50 means half a month's wage.",
    )
    advance_max_amount = fields.Monetary(
        string="Max Advance Amount",
        currency_field="currency_id",
        default=0.0,
        help="Absolute ceiling applied on top of the percentage. "
             "Leave at 0 for no hard ceiling.",
    )
    advance_allow_multiple = fields.Boolean(
        string="Allow Multiple Open Advances",
        default=False,
        help="Allow an employee to hold more than one advance that has not "
             "been fully recovered yet.",
    )
    advance_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Salary Advance Journal",
        domain="[('type', 'in', ['bank', 'cash']), ('company_id', '=', id)]",
        help="Bank or cash journal used to disburse salary advances. "
             "Required before any advance can be paid.",
    )

    _advance_max_percent_range = models.Constraint(
        "CHECK(advance_max_percent >= 0 AND advance_max_percent <= 100)",
        "The maximum advance percentage must be between 0 and 100.",
    )
    _advance_max_amount_positive = models.Constraint(
        "CHECK(advance_max_amount >= 0)",
        "The maximum advance amount cannot be negative.",
    )
