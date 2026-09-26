from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

RULE_MAP_VERSION_KEY = 'audit_trail_rule_map_version'

LOCKED_WHILE_ACTIVE = {
    'model_id',
    'company_id',
    'detail_level',
    'track_create',
    'track_write',
    'track_unlink',
    'track_export',
    'track_read',
    'keep_deleted_copy',
    'excluded_user_ids',
    'excluded_field_ids',
}


class AuditRule(models.Model):
    _name = 'audit.rule'
    _description = 'Audit Watch Rule'
    _order = 'name, id'

    name = fields.Char(required=True)
    model_id = fields.Many2one(
        'ir.model', string='Kind of Record', required=True, index=True, ondelete='cascade',
        domain=[('transient', '=', False), ('model', 'not like', 'audit.')],
        help="The kind of record being watched, for example Contact or Bank Account.")
    model_name = fields.Char(related='model_id.model', store=True, string='Model Name')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, index=True,
        default=lambda self: self.env.company,
        help="Only changes made while working in this company are recorded.")
    state = fields.Selection(
        [('draft', 'Draft'), ('active', 'Active')],
        string='Status', default='draft', required=True, readonly=True, copy=False)
    detail_level = fields.Selection(
        [('full', 'Full'), ('light', 'Light')],
        string='Detail Level', default='full', required=True,
        help="Full re-reads the record before and after every change to keep old and new values. "
             "Light stores only the new value and skips the extra read.")
    track_create = fields.Boolean(string='Record Creation', default=True)
    track_write = fields.Boolean(string='Record Changes', default=True)
    track_unlink = fields.Boolean(string='Record Deletion', default=True)
    track_export = fields.Boolean(string='Record Exports', default=True)
    track_read = fields.Boolean(
        string='Record List Opens', default=False,
        help="Counts only lists showing more than one record. A single record opened on its own is never recorded.")
    keep_deleted_copy = fields.Boolean(
        string='Keep a Copy on Deletion', default=True,
        help="Stores the full record contents alongside the deletion event.")
    excluded_user_ids = fields.Many2many(
        'res.users', 'audit_rule_excluded_user_rel', 'rule_id', 'user_id',
        string='People to Exclude',
        help="Actions performed by these people are never recorded.")
    excluded_field_ids = fields.Many2many(
        'ir.model.fields', 'audit_rule_excluded_field_rel', 'rule_id', 'field_id',
        string='Fields to Exclude',
        domain="[('model_id', '=', model_id)]",
        help="Changes to these fields are never recorded.")
    log_count = fields.Integer(string='Recorded Events', compute='_compute_log_count')

    _model_company_uniq = models.Constraint(
        'UNIQUE(model_id, company_id)',
        "A watch rule already exists for this kind of record in this company. Edit the existing rule instead.",
    )

    @api.depends('model_id', 'company_id')
    def _compute_log_count(self):
        counts = dict(self.env['audit.log']._read_group(
            [('rule_id', 'in', self.ids)], ['rule_id'], ['__count']))
        for rule in self:
            rule.log_count = counts.get(rule, 0)

    def _check_no_duplicate(self, model_id, company_id, exclude_ids=()):
        if not model_id or not company_id:
            return
        existing = self.sudo().search([
            ('model_id', '=', model_id),
            ('company_id', '=', company_id),
            ('id', 'not in', list(exclude_ids)),
        ], limit=1)
        if existing:
            raise ValidationError(_(
                "A watch rule for %(model)s already exists in %(company)s: \"%(rule)s\". "
                "Edit that rule instead of creating a second one.",
                model=existing.model_id.name,
                company=existing.company_id.name,
                rule=existing.name,
            ))

    @api.model_create_multi
    def create(self, vals_list):
        seen = set()
        for vals in vals_list:
            company_id = vals.get('company_id') or self.env.company.id
            key = (vals.get('model_id'), company_id)
            if key in seen:
                raise ValidationError(_("Only one watch rule per kind of record and company is allowed."))
            seen.add(key)
            self._check_no_duplicate(*key)
        rules = super().create(vals_list)
        self._invalidate_rule_map()
        return rules

    def write(self, vals):
        locked = LOCKED_WHILE_ACTIVE.intersection(vals)
        if locked and vals.get('state') != 'draft' and any(rule.state == 'active' for rule in self):
            raise UserError(_(
                "This watch rule is active, so its watch settings are locked. "
                "Set it back to Draft before changing them."))
        if 'model_id' in vals or 'company_id' in vals:
            for rule in self:
                self._check_no_duplicate(
                    vals.get('model_id', rule.model_id.id),
                    vals.get('company_id', rule.company_id.id),
                    rule.ids,
                )
        res = super().write(vals)
        self._invalidate_rule_map()
        return res

    def unlink(self):
        res = super().unlink()
        self._invalidate_rule_map()
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_active(self):
        if any(rule.state == 'active' for rule in self):
            raise UserError(_("Set the watch rule back to Draft before deleting it."))

    def action_confirm(self):
        self.filtered(lambda r: r.state == 'draft').write({'state': 'active'})
        return True

    def action_set_draft(self):
        self.filtered(lambda r: r.state == 'active').write({'state': 'draft'})
        return True

    def action_view_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Recorded Events"),
            'res_model': 'audit.log',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('rule_id', '=', self.id)],
        }

    @api.model
    def _invalidate_rule_map(self):
        self.env.cr.cache.pop(RULE_MAP_VERSION_KEY, None)
        self.env.transaction.invalidate_ormcache()

    @api.model
    def _get_rule_map_token(self):
        """Version stamp of the rule table, read once per cursor.

        Every create/write/unlink of a rule changes it, so a worker whose
        in-memory cache was built before a rule was confirmed (in another
        worker or a concurrent request) can never keep serving that stale map.
        """
        cache = self.env.cr.cache
        token = cache.get(RULE_MAP_VERSION_KEY)
        if token is None:
            [(count, last_write, max_id)] = self.sudo().with_context(active_test=False)._read_group(
                [], [], ['__count', 'write_date:max', 'id:max'])
            token = cache[RULE_MAP_VERSION_KEY] = (count, str(last_write), max_id)
        return token

    @api.model
    def _get_active_rule_map(self):
        """Active rules keyed by (model name, company id)."""
        return self._get_active_rule_map_cached(self._get_rule_map_token())

    @api.model
    @api.ormcache('token')
    def _get_active_rule_map_cached(self, token):
        """Active rules for one version ``token`` of the rule table."""
        result = {}
        rules = self.sudo().with_context(active_test=False).search([('state', '=', 'active')])
        for rule in rules:
            result[(rule.model_name, rule.company_id.id)] = {
                'id': rule.id,
                'detail_level': rule.detail_level,
                'create': rule.track_create,
                'write': rule.track_write,
                'unlink': rule.track_unlink,
                'export': rule.track_export,
                'read': rule.track_read,
                'keep_deleted_copy': rule.keep_deleted_copy,
                'excluded_user_ids': frozenset(rule.excluded_user_ids.ids),
                'excluded_fields': frozenset(rule.excluded_field_ids.mapped('name')),
            }
        return result

