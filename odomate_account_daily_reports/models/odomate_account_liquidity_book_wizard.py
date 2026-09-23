from odoo import _, api, fields, models
from odoo.exceptions import UserError

MULTI_CURRENCY_GROUP = 'base.group_multi_currency'


class OdomateAccountLiquidityBookWizard(models.TransientModel):
    _name = 'odomate.account.liquidity.book.wizard'
    _inherit = ['odomate.account.report.filter']
    _description = "Liquidity Book"

    _odomate_journal_types = ()
    _odomate_account_types = ()

    display_account = fields.Selection(
        selection=[
            ('all', "All Accounts"),
            ('movement', "With Movements"),
            ('not_zero', "With Balance Not Equal To Zero"),
        ],
        string="Display Accounts",
        required=True,
        default='movement',
    )
    sortby = fields.Selection(
        selection=[
            ('sort_date', "Date"),
            ('sort_journal_partner', "Journal and Partner"),
        ],
        string="Sort by",
        required=True,
        default='sort_date',
    )
    initial_balance = fields.Boolean(
        string="Include Opening Balance",
        help="Print an opening balance line for every account, computed from the entries booked before the start date.",
    )
    amount_currency = fields.Boolean(
        string="With Currency",
        groups=MULTI_CURRENCY_GROUP,
        help="Print the amount in the item's own currency next to the company-currency figures.",
    )

    def _odomate_journal_kinds_label(self):
        return ''

    def _odomate_journals(self):
        journals = super()._odomate_journals()
        types = list(self._odomate_journal_types)
        if types:
            journals = journals.filtered(lambda journal: journal.type in types)
        return journals

    def _odomate_check_filter(self):
        super()._odomate_check_filter()
        types = list(self._odomate_journal_types)
        if types:
            other_kind = self.journal_ids.filtered(
                lambda journal: journal.type not in types
            )
            if other_kind:
                raise UserError(_(
                    "This book only covers %(kinds)s journals.",
                    kinds=self._odomate_journal_kinds_label(),
                ))
        if self.initial_balance and not self.date_from:
            raise UserError(_("Set a start date to print an opening balance."))

    def _odomate_report_data(self):
        data = super()._odomate_report_data()
        show_currency = self.env.user.has_group(MULTI_CURRENCY_GROUP)
        data.update({
            'display_account': self.display_account,
            'sortby': self.sortby,
            'initial_balance': bool(self.initial_balance),
            'amount_currency': bool(self.amount_currency) if show_currency else False,
            'account_types': list(self._odomate_account_types),
        })
        return data

    @api.model
    def _odomate_options_from_data(self, data):
        options = super()._odomate_options_from_data(data)
        options.update({
            'display_account': data.get('display_account') or 'movement',
            'sortby': data.get('sortby') or 'sort_date',
            'initial_balance': bool(data.get('initial_balance')),
            'amount_currency': bool(data.get('amount_currency')),
            'account_types': list(data.get('account_types') or []),
        })
        return options


class OdomateAccountCashBookWizard(models.TransientModel):
    _name = 'odomate.account.cash.book.wizard'
    _inherit = ['odomate.account.liquidity.book.wizard']
    _description = "Cash Book"

    _odomate_report_xmlid = 'odomate_account_daily_reports.action_report_odomate_cash_book'
    _odomate_journal_types = ('cash',)
    _odomate_account_types = ('asset_cash',)

    def _odomate_journal_kinds_label(self):
        return _("cash")


class OdomateAccountBankBookWizard(models.TransientModel):
    _name = 'odomate.account.bank.book.wizard'
    _inherit = ['odomate.account.liquidity.book.wizard']
    _description = "Bank Book"

    _odomate_report_xmlid = 'odomate_account_daily_reports.action_report_odomate_bank_book'
    _odomate_journal_types = ('bank', 'credit')
    _odomate_account_types = ('asset_cash', 'liability_credit_card')

    def _odomate_journal_kinds_label(self):
        return _("bank and credit card")
