import json
import logging
from urllib.parse import urlparse

from odoo import _, api, fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)

SKIP_CONTEXT_KEY = 'audit_trail_skip'
SKIP_FIELDS = {'id', 'create_uid', 'create_date', 'write_uid', 'write_date', 'display_name'}
SKIP_FIELD_TYPES = {'binary', 'one2many', 'properties', 'properties_definition', 'json', 'image'}


class Base(models.AbstractModel):
    _inherit = 'base'

    # ------------------------------------------------------------------
    # Rule lookup
    # ------------------------------------------------------------------
    def _audit_is_skipped(self):
        for model_name, ids in self.env.context.get(SKIP_CONTEXT_KEY, ()):
            if model_name == self._name and (ids is None or set(self.ids) <= set(ids)):
                return True
        return False

    def _audit_rule(self, action):
        """Return the cached active rule settings for this model/company/action, or None."""
        if (
            self._transient
            or self._abstract
            or self._name.startswith('audit.')
            or not self.pool.ready
            or self.env.context.get('install_mode')
            or 'audit.rule' not in self.env
        ):
            return None
        rule = self.env['audit.rule']._get_active_rule_map().get((self._name, self.env.company.id))
        if not rule or not rule.get(action) or self.env.uid in rule['excluded_user_ids']:
            return None
        if self._audit_is_skipped():
            return None
        return rule

    def _audit_guard(self, ids=None):
        skip = tuple(self.env.context.get(SKIP_CONTEXT_KEY, ()))
        entry = (self._name, tuple(ids) if ids is not None else None)
        return self.with_context(**{SKIP_CONTEXT_KEY: skip + (entry,)})

    # ------------------------------------------------------------------
    # Value capture
    # ------------------------------------------------------------------
    def _audit_field_names(self, rule, restrict_to=None):
        names = []
        for name, field in self._fields.items():
            if restrict_to is not None and name not in restrict_to:
                continue
            if (
                not field.store
                or name in SKIP_FIELDS
                or field.type in SKIP_FIELD_TYPES
                or name in rule['excluded_fields']
            ):
                continue
            names.append(name)
        return names

    def _audit_format_value(self, record, fname, selection_labels):
        field = self._fields[fname]
        value = record[fname]
        if field.type == 'many2one':
            return value.display_name or '' if value else ''
        if field.type == 'many2many':
            return ', '.join(value.mapped('display_name'))
        if field.type == 'boolean':
            return str(bool(value))
        if value is False or value is None:
            return ''
        if field.type == 'selection':
            return selection_labels.get(fname, {}).get(value, str(value))
        if field.type == 'datetime':
            return fields.Datetime.to_string(value)
        if field.type == 'date':
            return fields.Date.to_string(value)
        return str(value)

    def _audit_snapshot(self, fnames):
        """Formatted values of ``fnames`` for every record, keyed by record id."""
        if not fnames:
            return {rec.id: {} for rec in self}
        selection_names = [f for f in fnames if self._fields[f].type == 'selection']
        selection_labels = {}
        if selection_names:
            for fname, info in self.sudo().fields_get(selection_names, attributes=['selection']).items():
                selection_labels[fname] = dict(info.get('selection') or [])
        result = {}
        for record in self.sudo().with_context(active_test=False):
            result[record.id] = {
                fname: self._audit_format_value(record, fname, selection_labels) for fname in fnames
            }
        return result

    def _audit_source_action(self):
        """Best-effort name of the screen the request came from, read from the browser URL."""
        if not request:
            return False
        try:
            referrer = request.httprequest.referrer or ''
        except RuntimeError:
            return False
        parts = [p for p in urlparse(referrer).path.split('/') if p]
        if len(parts) < 2 or parts[0] not in ('odoo', 'web'):
            return False
        segments = [p for p in parts[1:] if not p.isdigit() and p != 'new']
        if not segments:
            return False
        key = segments[-1]
        Actions = self.env['ir.actions.actions'].sudo()
        action = Actions
        if key.startswith('action-'):
            ref = key[len('action-'):]
            if ref.isdigit():
                action = Actions.browse(int(ref)).exists()
            else:
                action = self.env.ref(ref, raise_if_not_found=False) or Actions
        elif 'path' in Actions._fields:
            action = Actions.search([('path', '=', key)], limit=1)
        return getattr(action, 'name', False) or False

    # ------------------------------------------------------------------
    # Log writing (never aborts the host operation)
    # ------------------------------------------------------------------
    def _audit_prepare_log_vals(self, rule, entries):
        session = self.env['audit.session']._get_current_session()
        source = self._audit_source_action()
        fnames = {line[0] for entry in entries for line in entry.get('lines', ())}
        field_recs = {}
        if fnames:
            field_recs = {
                f.name: f for f in self.env['ir.model.fields'].sudo().search(
                    [('model', '=', self._name), ('name', 'in', list(fnames))])
            }
        now = fields.Datetime.now()
        vals_list = []
        for entry in entries:
            line_cmds = []
            for fname, old, new in entry.get('lines', ()):
                field_rec = field_recs.get(fname)
                line_cmds.append((0, 0, {
                    'field_id': field_rec.id if field_rec else False,
                    'field_description': field_rec.field_description if field_rec else self._fields[fname].string,
                    'old_value': old or False,
                    'new_value': new or False,
                }))
            vals_list.append({
                'rule_id': rule['id'],
                'res_model': self._name,
                'res_id': entry.get('res_id') or False,
                'record_name': entry.get('record_name') or False,
                'action': entry['action'],
                'user_id': self.env.uid,
                'date': now,
                'detail_level': rule['detail_level'],
                'company_id': self.env.company.id,
                'deleted_data': entry.get('deleted_data') or False,
                'exported_res_ids': entry.get('exported_res_ids') or False,
                'session_id': session.id or False,
                'source_action': source,
                'line_ids': line_cmds,
            })
        return vals_list

    def _audit_write_logs(self, rule, entries):
        entries = [e for e in entries if e]
        if not entries:
            return
        if getattr(self.env.cr, 'readonly', False):
            try:
                with self.env.registry.cursor() as cr:
                    model = self.with_env(self.env(cr=cr))
                    model.env['audit.log'].sudo().create(model._audit_prepare_log_vals(rule, entries))
            except Exception:
                _logger.exception("Audit Trail could not record %s events on %s", entries[0]['action'], self._name)
            return
        # Flush the host operation first so that its own errors surface normally.
        self.env.flush_all()
        try:
            with self.env.cr.savepoint():
                self.env['audit.log'].sudo().create(self._audit_prepare_log_vals(rule, entries))
        except Exception:
            _logger.exception("Audit Trail could not record %s events on %s", entries[0]['action'], self._name)

    # ------------------------------------------------------------------
    # ORM hooks
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        rule = self._audit_rule('create')
        if not rule:
            return super().create(vals_list)
        records = super(Base, self._audit_guard()).create(vals_list).with_env(self.env)
        try:
            full = rule['detail_level'] == 'full'
            all_names = self._audit_field_names(rule) if full else None
            entries = []
            for record, vals in zip(records, vals_list):
                names = all_names if full else self._audit_field_names(rule, set(vals))
                values = record._audit_snapshot(names)[record.id]
                entries.append({
                    'action': 'create',
                    'res_id': record.id,
                    'record_name': record.sudo().display_name,
                    'lines': [(f, False, values[f]) for f in names
                              if values[f] and (not full or values[f] != 'False')],
                })
        except Exception:
            _logger.exception("Audit Trail could not capture created values on %s", self._name)
            return records
        records._audit_write_logs(rule, entries)
        return records

    def write(self, vals):
        rule = self._audit_rule('write') if self else None
        if not rule:
            return super().write(vals)
        full = rule['detail_level'] == 'full'
        before = {}
        try:
            names = self._audit_field_names(rule, None if full else set(vals))
            if full:
                before = self._audit_snapshot(names)
        except Exception:
            _logger.exception("Audit Trail could not capture previous values on %s", self._name)
            return super().write(vals)
        res = super(Base, self._audit_guard(self.ids)).write(vals)
        try:
            after = self._audit_snapshot(names)
            entries = []
            for record in self:
                new_values = after.get(record.id, {})
                if full:
                    old_values = before.get(record.id, {})
                    lines = [(f, old_values.get(f), new_values[f]) for f in names
                             if old_values.get(f) != new_values[f]]
                else:
                    lines = [(f, False, new_values[f]) for f in names]
                if lines:
                    entries.append({
                        'action': 'write',
                        'res_id': record.id,
                        'record_name': record.sudo().display_name,
                        'lines': lines,
                    })
        except Exception:
            _logger.exception("Audit Trail could not capture new values on %s", self._name)
            return res
        self._audit_write_logs(rule, entries)
        return res

    def unlink(self):
        rule = self._audit_rule('unlink') if self else None
        if not rule:
            return super().unlink()
        entries = []
        try:
            snapshot = self._audit_snapshot(self._audit_field_names(rule)) if rule['keep_deleted_copy'] else {}
            for record in self.sudo():
                entry = {
                    'action': 'unlink',
                    'res_id': record.id,
                    'record_name': record.display_name,
                }
                if record.id in snapshot:
                    entry['deleted_data'] = json.dumps(
                        snapshot[record.id], ensure_ascii=False, indent=2, sort_keys=True)
                entries.append(entry)
        except Exception:
            _logger.exception("Audit Trail could not capture deleted records on %s", self._name)
            entries = []
        model = self.browse()
        res = super(Base, self._audit_guard(self.ids)).unlink()
        model._audit_write_logs(rule, entries)
        return res

    def export_data(self, fields_to_export):
        res = super().export_data(fields_to_export)
        rule = self._audit_rule('export') if self else None
        if rule:
            self.browse()._audit_write_logs(rule, [{
                'action': 'export',
                'record_name': _("%(count)s records exported", count=len(self)),
                'exported_res_ids': json.dumps(self.ids),
            }])
        return res

    @api.model
    @api.readonly
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        result = super().web_search_read(
            domain, specification, offset=offset, limit=limit, order=order, count_limit=count_limit)
        rule = self._audit_rule('read')
        if rule:
            ids = [rec['id'] for rec in result.get('records', ()) if isinstance(rec.get('id'), int)]
            if len(ids) > 1:
                self._audit_write_logs(rule, [{
                    'action': 'read',
                    'record_name': _("%(count)s records listed", count=len(ids)),
                    'exported_res_ids': json.dumps(ids),
                }])
        return result

    # ------------------------------------------------------------------
    # "View Logs" button on watched records
    # ------------------------------------------------------------------
    def action_audit_view_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Audit Logs"),
            'res_model': 'audit.log',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {'create': False},
        }
