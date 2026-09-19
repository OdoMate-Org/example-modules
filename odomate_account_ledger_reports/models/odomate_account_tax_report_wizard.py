from odoo import fields, models


def _first_day_of_month(record):
    return fields.Date.context_today(record).replace(day=1)


class OdomateAccountTaxReportWizard(models.TransientModel):
    _name = 'odomate.account.tax.report.wizard'
    _inherit = ['odomate.account.report.filter']
    _description = "Tax Report Dialog"

    _odomate_report_xmlid = 'action_report_odomate_tax_report'

    date_from = fields.Date(
        string="Start Date",
        required=True,
        default=lambda self: _first_day_of_month(self),
    )
    date_to = fields.Date(
        string="End Date",
        required=True,
        default=fields.Date.context_today,
    )
