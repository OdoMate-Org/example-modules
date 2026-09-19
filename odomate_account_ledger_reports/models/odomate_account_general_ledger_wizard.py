from odoo import _, api, fields, models
from odoo.exceptions import UserError

ANALYTIC_GROUP = 'analytic.group_analytic_accounting'


class OdomateAccountGeneralLedgerWizard(models.TransientModel):
    _name = 'odomate.account.general.ledger.wizard'
    _inherit = ['odomate.account.report.filter']
    _description = "General Ledger Report Dialog"

    _odomate_report_xmlid = 'action_report_odomate_general_ledger'

    account_ids = fields.Many2many(
        comodel_name='account.account',
        relation='odomate_gl_wizard_account_rel',
        column1='wizard_id',
        column2='account_id',
        string="Accounts",
        domain="[('company_ids', 'in', [company_id])]",
        help="Leave empty to cover every account of the selected company.",
    )
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='odomate_gl_wizard_partner_rel',
        column1='wizard_id',
        column2='partner_id',
        string="Partners",
    )
    analytic_account_ids = fields.Many2many(
        comodel_name='account.analytic.account',
        relation='odomate_gl_wizard_analytic_rel',
        column1='wizard_id',
        column2='analytic_account_id',
        string="Analytic Accounts",
        groups=ANALYTIC_GROUP,
    )
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
    initial_balance = fields.Boolean(
        string="Include Opening Balance",
        help="Print an opening balance line for every account, computed from the entries booked before the start date.",
    )
    sortby = fields.Selection(
        selection=[
            ('sort_date', "Date"),
            ('sort_journal_partner', "Journal and Partner"),
        ],
        string="Sort By",
        required=True,
        default='sort_date',
    )

    def _odomate_check_filter(self):
        super()._odomate_check_filter()
        if self.initial_balance and not self.date_from:
            raise UserError(_("Set a start date to print an opening balance."))

    def _odomate_report_data(self):
        data = super()._odomate_report_data()
        analytic_ids = []
        if self.env.user.has_group(ANALYTIC_GROUP):
            analytic_ids = self.analytic_account_ids.ids
        data.update({
            'account_ids': self.account_ids.ids,
            'partner_ids': self.partner_ids.ids,
            'analytic_account_ids': analytic_ids,
            'display_account': self.display_account,
            'initial_balance': bool(self.initial_balance),
            'sortby': self.sortby,
        })
        return data

    @api.model
    def _odomate_options_from_data(self, data):
        options = super()._odomate_options_from_data(data)
        options.update({
            'accounts': self.env['account.account'].browse(data.get('account_ids') or []),
            'partners': self.env['res.partner'].browse(data.get('partner_ids') or []),
            'analytic_accounts': self.env['account.analytic.account'].browse(
                data.get('analytic_account_ids') or []
            ),
            'display_account': data.get('display_account') or 'movement',
            'initial_balance': bool(data.get('initial_balance')),
            'sortby': data.get('sortby') or 'sort_date',
        })
        return options
