from odoo import _, fields, models
from odoo.exceptions import UserError


class OdomateAccountDayBookWizard(models.TransientModel):
    _name = 'odomate.account.day.book.wizard'
    _inherit = ['odomate.account.report.filter']
    _description = "Day Book"

    _odomate_report_xmlid = 'odomate_account_daily_reports.action_report_odomate_day_book'

    date_from = fields.Date(required=True, default=fields.Date.context_today)
    date_to = fields.Date(required=True, default=fields.Date.context_today)

    def _odomate_check_filter(self):
        super()._odomate_check_filter()
        if not self.date_from or not self.date_to:
            raise UserError(_("Set both a start and an end date for the day book."))
