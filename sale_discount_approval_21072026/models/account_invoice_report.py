from odoo import fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    discount = fields.Float(string="Discount %", readonly=True)

    def _select(self) -> SQL:
        return SQL("%s, line.discount AS discount", super()._select())
