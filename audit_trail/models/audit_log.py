import json

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.fields import Domain

CLEANUP_BATCH_SIZE = 1000

AUDIT_ACTIONS = [
    ('create', 'Create'),
    ('write', 'Change'),
    ('unlink', 'Delete'),
    ('export', 'Export'),
    ('read', 'List Open'),
]


class AuditLog(models.Model):
    _name = 'audit.log'
    _description = 'Audit Recorded Event'
    _order = 'date desc, id desc'

    rule_id = fields.Many2one('audit.rule', string='Watch Rule', required=True, index=True, ondelete='cascade')
    res_model = fields.Char(string='Kind of Record', index=True, readonly=True)
    res_id = fields.Integer(string='Record ID', index=True, readonly=True)
    record_name = fields.Char(string='Record', readonly=True)
    action = fields.Selection(AUDIT_ACTIONS, string='Action', required=True, index=True, readonly=True)
    user_id = fields.Many2one('res.users', string='User', index=True, ondelete='set null', readonly=True)
    date = fields.Datetime(string='Date', required=True, index=True, default=fields.Datetime.now, readonly=True)
    detail_level = fields.Char(string='Detail Level', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, readonly=True)
    deleted_data = fields.Text(string='Deleted Record Contents', readonly=True)
    exported_res_ids = fields.Text(string='Exported Record IDs', readonly=True)
    exported_count = fields.Integer(string='Records Included', compute='_compute_exported_count')
    session_id = fields.Many2one('audit.session', string='Working Session', index=True, ondelete='set null')
    source_action = fields.Char(string='Source Screen', readonly=True)
    line_ids = fields.One2many('audit.log.line', 'log_id', string='Field Changes', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        rules = self.env['audit.rule'].sudo().browse(
            {vals['rule_id'] for vals in vals_list if vals.get('rule_id')})
        rule_by_id = {rule.id: rule for rule in rules}
        for vals in vals_list:
            rule = rule_by_id.get(vals.get('rule_id'))
            if not rule:
                continue
            vals.setdefault('res_model', rule.model_name)
            vals.setdefault('company_id', rule.company_id.id)
            vals.setdefault('detail_level', rule.detail_level)
        return super().create(vals_list)

    @api.model
    def _action_labels(self):
        return dict(self.fields_get(['action'], attributes=['selection'])['action']['selection'])

    @api.depends('record_name', 'res_model', 'action')
    def _compute_display_name(self):
        labels = self._action_labels()
        for log in self:
            log.display_name = f"{log.record_name or log.res_model or ''} - {labels.get(log.action, '')}"

    @api.depends('exported_res_ids')
    def _compute_exported_count(self):
        for log in self:
            log.exported_count = len(log._get_exported_ids())

    def _get_exported_ids(self):
        self.ensure_one()
        try:
            ids = json.loads(self.exported_res_ids or '[]')
        except ValueError:
            return []
        return sorted(int(i) for i in ids if isinstance(i, int))

    def action_view_exported_records(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Exported Records"),
            'res_model': self.res_model,
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('id', 'in', self._get_exported_ids())],
            'context': {'active_test': False},
        }

    def action_open_record(self):
        self.ensure_one()
        record = self.env[self.res_model].browse(self.res_id).exists() if self.res_model in self.env else None
        if not record:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': _("This record no longer exists; its recorded history is kept here."),
                },
            }
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.res_model,
            'res_id': self.res_id,
            'view_mode': 'form',
            'views': [(False, 'form')],
        }

    @api.model
    def _cleanup_domain(self):
        companies = self.env['res.company'].sudo().with_context(active_test=False).search(
            [('audit_cleanup_enabled', '=', True)])
        if not companies:
            return None
        now = fields.Datetime.now()
        return Domain.OR([
            Domain('company_id', '=', company.id)
            & Domain('date', '<', now - relativedelta(months=max(company.audit_cleanup_age_months, 1)))
            for company in companies
        ])

    @api.model
    def _cron_cleanup_logs(self, batch_size=CLEANUP_BATCH_SIZE):
        """Delete one bounded batch of expired history; the scheduler re-runs until caught up."""
        domain = self._cleanup_domain()
        if domain is None:
            return
        Log = self.sudo()
        logs = Log.search(domain, order='date, id', limit=batch_size)
        done = len(logs)
        logs.unlink()
        remaining = Log.search_count(domain) if done == batch_size else 0
        if self.env.context.get('cron_id'):
            self.env['ir.cron']._commit_progress(done, remaining=remaining)
