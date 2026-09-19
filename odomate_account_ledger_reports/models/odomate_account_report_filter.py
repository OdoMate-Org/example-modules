from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

MODULE = 'odomate_account_ledger_reports'

REPORT_GROUPS = (
    'account.group_account_manager',
    'account.group_account_user',
    'account.group_account_readonly',
)

EXCLUDED_DISPLAY_TYPES = ['line_section', 'line_subsection', 'line_note']

STATE_BY_TARGET_MOVE = {
    'posted': ['posted'],
    'all': ['draft', 'posted'],
}

RECEIVABLE = 'asset_receivable'
PAYABLE = 'liability_payable'

ACCOUNT_TYPES_BY_RESULT_SELECTION = {
    'customer': [RECEIVABLE],
    'supplier': [PAYABLE],
    'customer_supplier': [RECEIVABLE, PAYABLE],
}

RESULT_SELECTION = [
    ('customer', "Receivable Accounts"),
    ('supplier', "Payable Accounts"),
    ('customer_supplier', "Receivable and Payable Accounts"),
]


class OdomateAccountReportFilter(models.TransientModel):
    _name = 'odomate.account.report.filter'
    _description = "Accounting Report Filter"

    _odomate_report_xmlid = None

    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        domain="[('id', 'in', allowed_company_ids)]",
    )
    date_from = fields.Date(string="Start Date")
    date_to = fields.Date(string="End Date")
    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string="Journals",
        domain="[('company_id', '=', company_id)]",
        help="Leave empty to cover every journal of the selected company.",
    )
    target_move = fields.Selection(
        selection=[('posted', "Posted Entries Only"), ('all', "All Entries")],
        string="Entries",
        required=True,
        default='posted',
    )

    # ------------------------------------------------------------------
    # Stable contract - journals and state
    # ------------------------------------------------------------------

    def _odomate_journals(self):
        self.ensure_one()
        if self.journal_ids:
            return self.journal_ids
        return self.env['account.journal'].search(
            [('company_id', '=', self.company_id.id)], order='sequence, type, code'
        )

    def _odomate_state_domain(self):
        self.ensure_one()
        return self._odomate_state_domain_for(self.target_move)

    @api.model
    def _odomate_state_domain_for(self, target_move):
        states = STATE_BY_TARGET_MOVE.get(target_move) or STATE_BY_TARGET_MOVE['posted']
        return [('parent_state', 'in', list(states))]

    # ------------------------------------------------------------------
    # Stable contract - journal item domain
    # ------------------------------------------------------------------

    def _odomate_line_domain(self, date_field='date', date_from=None, date_to=None):
        self.ensure_one()
        return self._odomate_base_domain(
            self.company_id,
            journals=self._odomate_journals(),
            target_move=self.target_move,
            date_from=self.date_from if date_from is None else date_from,
            date_to=self.date_to if date_to is None else date_to,
            date_field=date_field,
        )

    @api.model
    def _odomate_base_domain(self, company, journals=None, target_move='posted',
                             date_from=None, date_to=None, date_field='date'):
        domain = [
            ('company_id', '=', company.id),
            ('display_type', 'not in', EXCLUDED_DISPLAY_TYPES),
        ]
        domain += self._odomate_state_domain_for(target_move)
        if journals is not None:
            domain.append(('journal_id', 'in', journals.ids))
        if date_from:
            domain.append((date_field, '>=', date_from))
        if date_to:
            domain.append((date_field, '<=', date_to))
        return domain

    @api.model
    def _odomate_options_line_domain(self, options, date_field='date',
                                     date_from=None, date_to=None):
        return self._odomate_base_domain(
            options['company'],
            journals=options['journals'],
            target_move=options['target_move'],
            date_from=options['date_from'] if date_from is None else date_from,
            date_to=options['date_to'] if date_to is None else date_to,
            date_field=date_field,
        )

    # ------------------------------------------------------------------
    # Stable contract - opening balance domain
    # ------------------------------------------------------------------

    @api.model
    def _odomate_initial_balance_domain(self, company, date_from, journals=None,
                                        target_move='posted'):
        fiscalyear_from = company.compute_fiscalyear_dates(date_from)['date_from']
        domain = [
            ('company_id', '=', company.id),
            ('display_type', 'not in', EXCLUDED_DISPLAY_TYPES),
            ('date', '<', date_from),
            '|',
            ('account_id.include_initial_balance', '=', True),
            ('date', '>=', fiscalyear_from),
        ]
        domain += self._odomate_state_domain_for(target_move)
        if journals is not None:
            domain.append(('journal_id', 'in', journals.ids))
        return domain

    # ------------------------------------------------------------------
    # Stable contract - validation
    # ------------------------------------------------------------------

    def _odomate_check_filter(self):
        self.ensure_one()
        if self.company_id.id not in self.env.companies.ids:
            raise UserError(_(
                "You cannot print a report for a company you are not allowed to work in."
            ))
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise UserError(_("The start date cannot be after the end date."))
        foreign = self.journal_ids.filtered(lambda j: j.company_id != self.company_id)
        if foreign:
            raise UserError(_(
                "Every journal must belong to %(company)s.",
                company=self.company_id.display_name,
            ))

    @api.model
    def _odomate_check_report_access(self):
        if not any(self.env.user.has_group(group) for group in REPORT_GROUPS):
            raise AccessError(_("Only accounting users can print accounting reports."))

    # ------------------------------------------------------------------
    # Stable contract - data crossing the browser
    # ------------------------------------------------------------------

    def _odomate_report_data(self):
        self.ensure_one()
        return {
            'company_id': self.company_id.id,
            'date_from': self.date_from.isoformat() if self.date_from else False,
            'date_to': self.date_to.isoformat() if self.date_to else False,
            'journal_ids': self._odomate_journals().ids,
            'explicit_journals': bool(self.journal_ids),
            'target_move': self.target_move,
            'wizard_model': self._name,
        }

    @api.model
    def _odomate_options_from_data(self, data):
        data = dict(data or {})
        company = self.env['res.company'].browse(
            data.get('company_id') or self.env.company.id
        )
        return {
            'data': data,
            'company': company,
            'currency': company.currency_id,
            'date_from': fields.Date.to_date(data.get('date_from')) or False,
            'date_to': fields.Date.to_date(data.get('date_to')) or False,
            'journals': self.env['account.journal'].browse(data.get('journal_ids') or []),
            'explicit_journals': bool(data.get('explicit_journals')),
            'target_move': data.get('target_move') or 'posted',
            'wizard_model': data.get('wizard_model') or self._name,
        }

    # ------------------------------------------------------------------
    # Stable contract - printing
    # ------------------------------------------------------------------

    def _odomate_print(self, report_xmlid=None):
        self.ensure_one()
        self._odomate_check_filter()
        xmlid = report_xmlid or self._odomate_report_xmlid
        if not xmlid:
            raise UserError(_("No printable report is configured for this dialog."))
        if '.' not in xmlid:
            xmlid = '%s.%s' % (MODULE, xmlid)
        return self.env.ref(xmlid).report_action(self, data=self._odomate_report_data())

    def action_odomate_print(self):
        self.ensure_one()
        return self._odomate_print()

    # ------------------------------------------------------------------
    # Shared presentation helpers
    # ------------------------------------------------------------------

    @api.model
    def _odomate_header_values(self, options):
        return {
            'company': options['company'],
            'date_from': options['date_from'],
            'date_to': options['date_to'],
            'journals': options['journals'] if options['explicit_journals'] else False,
            'target_move_label': self._odomate_target_move_label(options['target_move']),
        }

    @api.model
    def _odomate_target_move_label(self, target_move):
        labels = dict(self._fields['target_move']._description_selection(self.env))
        return labels.get(target_move) or labels.get('posted')

    @api.model
    def _odomate_account_label(self, account):
        return ' '.join(part for part in (account.code, account.name) if part)

    @api.model
    def _odomate_analytic_labels(self, lines):
        ids = set()
        for line in lines:
            for key in (line.analytic_distribution or {}):
                for part in str(key).split(','):
                    if part.strip().isdigit():
                        ids.add(int(part.strip()))
        names = {}
        if ids:
            accounts = self.env['account.analytic.account'].browse(sorted(ids)).exists()
            names = {account.id: account.display_name for account in accounts}
        labels = {}
        for line in lines:
            parts = []
            for key, percentage in (line.analytic_distribution or {}).items():
                named = [
                    names[int(p.strip())]
                    for p in str(key).split(',')
                    if p.strip().isdigit() and int(p.strip()) in names
                ]
                if named:
                    parts.append('%s (%s%%)' % (' + '.join(named), percentage))
            labels[line.id] = ', '.join(parts)
        return labels
