import hashlib
import json
import logging

from odoo import _, api, fields, models, modules
from odoo.exceptions import UserError, ValidationError

from .common import FIELDS_BLACKLIST, LOG_TYPE_SELECTION, LOGGABLE_METHODS

_logger = logging.getLogger(__name__)

PATCH_TRIGGER_FIELDS = frozenset({
    "model_id",
    "log_read",
    "log_write",
    "log_unlink",
    "log_create",
    "log_export_data",
    "log_type",
    "users_to_exclude_ids",
    "log_failure_policy",
    "state",
})


def _normalize_value(value):
    """Copy ``value`` into plain data: recordsets become id lists and
    containers are rebuilt, so the caller's structure is never shared."""
    if isinstance(value, models.BaseModel):
        return value.ids
    if isinstance(value, dict):
        return {key: _normalize_value(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_normalize_value(val) for val in value]
    if isinstance(value, tuple):
        return tuple(_normalize_value(val) for val in value)
    return value


def _is_empty(value):
    return value is None or value is False or value in ("", [], ())


def _extract_ids(value):
    """Best-effort id list from a read() value or x2many commands."""
    if not isinstance(value, (list, tuple)):
        return None
    ids = []
    for item in value:
        if isinstance(item, int) and not isinstance(item, bool):
            ids.append(item)
        elif isinstance(item, (list, tuple)) and item:
            command = item[0]
            if command == 6 and len(item) > 2 and isinstance(item[2], (list, tuple)):
                ids.extend(i for i in item[2] if isinstance(i, int))
            elif command in (1, 4) and len(item) > 1 and isinstance(item[1], int):
                ids.append(item[1])
            else:
                return None
        else:
            return None
    return ids


class AuditlogRule(models.Model):
    _name = "auditlog.rule"
    _description = "Auditlog - Rule"

    name = fields.Char(required=True)
    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        index=True,
        ondelete="set null",
        domain=[("transient", "=", False), ("model", "not like", "auditlog.")],
        help="Select model for which you want to generate log.",
    )
    model_name = fields.Char(readonly=True)
    model_model = fields.Char(string="Technical Model Name", readonly=True)
    log_read = fields.Boolean(
        string="Log Reads",
        help="Select this if you want to keep track of read/open on any record of the model of this rule",
    )
    log_write = fields.Boolean(
        string="Log Writes",
        default=True,
        help="Select this if you want to keep track of modification on any record of the model of this rule",
    )
    log_unlink = fields.Boolean(
        string="Log Deletes",
        default=True,
        help="Select this if you want to keep track of deletion on any record of the model of this rule",
    )
    log_create = fields.Boolean(
        string="Log Creates",
        default=True,
        help="Select this if you want to keep track of creation on any record of the model of this rule",
    )
    log_export_data = fields.Boolean(
        string="Log Exports",
        default=True,
        help="Select this if you want to keep track of exports on any record of the model of this rule",
    )
    log_type = fields.Selection(
        LOG_TYPE_SELECTION,
        string="Type",
        required=True,
        default="full",
        help="Full log: make a diff between the data before and after the operation (log more info like computed fields which were updated, but it is slower)\nFast log: only log the changes made through the create and write operations (less information, but it is faster)",
    )
    log_failure_policy = fields.Selection(
        [("block", "Block the operation"), ("skip", "Skip the log")],
        string="On Logging Failure",
        required=True,
        default="block",
        help="Block: an error while writing the audit log rolls back the audited operation.\nSkip: the audited operation completes, the error is written to the server log and no audit record is kept.",
    )
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed")],
        required=True,
        default="draft",
    )
    action_id = fields.Many2one(
        "ir.actions.act_window",
        string="Action",
        readonly=True,
        copy=False,
    )
    log_count = fields.Integer(
        string="Logs",
        compute="_compute_log_count",
    )
    capture_record = fields.Boolean(
        help="Select this if you want to keep track of Unlink Record",
    )
    users_to_exclude_ids = fields.Many2many(
        "res.users",
        "auditlog_rule_res_users_exclude_rel",
        "rule_id",
        "user_id",
        string="Users to Exclude",
        context={"active_test": False},
    )
    fields_to_exclude_ids = fields.Many2many(
        "ir.model.fields",
        "auditlog_rule_ir_model_fields_exclude_rel",
        "rule_id",
        "field_id",
        string="Fields to Exclude",
        domain="[('model_id', '=', model_id)]",
    )

    _model_uniq = models.Constraint(
        "unique(model_id)",
        "There is already a rule defined on this model.\nYou cannot define another: please edit the existing one.",
    )

    @api.constrains("model_id")
    def _check_model_auditable(self):
        for rule in self:
            if rule.model_id.model and rule.model_id.model.startswith("auditlog."):
                raise ValidationError(_("Audit trail models cannot be audited themselves."))

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def _set_model_names(self, vals):
        if vals.get("model_id"):
            ir_model = self.env["ir.model"].sudo().browse(vals["model_id"])
            vals["model_name"] = ir_model.name
            vals["model_model"] = ir_model.model

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._set_model_names(vals)
        rules = super().create(vals_list)
        if rules._patch_methods():
            rules._signal_registry_change()
        return rules

    def write(self, vals):
        self._set_model_names(vals)
        repatch = bool(PATCH_TRIGGER_FIELDS.intersection(vals))
        reverted = self._revert_patches() if repatch else False
        result = super().write(vals)
        patched = self._patch_methods() if repatch else False
        if reverted or patched:
            self._signal_registry_change()
        return result

    def unlink(self):
        if self._revert_patches():
            self._signal_registry_change()
        actions = self.action_id
        result = super().unlink()
        actions.sudo().unlink()
        return result

    @api.depends("model_id")
    def _compute_log_count(self):
        Log = self.env["auditlog.log"]
        counts = {}
        model_ids = self.model_id.ids
        if model_ids and Log.has_access("read"):
            counts = {
                model.id: count
                for model, count in Log._read_group(
                    [("model_id", "in", model_ids)], ["model_id"], ["__count"]
                )
            }
        for rule in self:
            rule.log_count = counts.get(rule.model_id.id, 0)

    def action_view_logs(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("auditlog.action_auditlog_log")
        action["domain"] = [("model_id", "=", self.model_id.id)]
        action["context"] = {}
        action["display_name"] = _("Logs of %(rule)s", rule=self.name)
        return action

    # ------------------------------------------------------------------
    # State flow
    # ------------------------------------------------------------------

    def set_to_confirmed(self):
        act_window = self.env["ir.actions.act_window"].sudo()
        for rule in self:
            if not rule.model_id:
                raise UserError(_("Select a model before confirming the rule %(rule)s.", rule=rule.name))
            binding = {
                "binding_model_id": rule.model_id.id,
                "binding_type": "action",
                "binding_view_types": "form",
            }
            action = rule.action_id.sudo().exists()
            if action:
                if action.binding_model_id != rule.model_id:
                    action.write(binding)
            else:
                rule.action_id = act_window.create(dict(
                    binding,
                    name=_("View logs"),
                    res_model="auditlog.log",
                    view_mode="list,form",
                    domain="[('model_id', '=', %s), ('res_id', '=', active_id)]" % rule.model_id.id,
                ))
        self.filtered(lambda r: r.state != "confirmed").write({"state": "confirmed"})
        if self._patch_methods():
            self._signal_registry_change()
        return True

    def set_to_draft(self):
        self.action_id.sudo().exists().write({"binding_model_id": False})
        self.write({"state": "draft"})
        return True

    # ------------------------------------------------------------------
    # Registry patching
    # ------------------------------------------------------------------

    def _auditlog_model_cache(self):
        registry = self.env.registry
        if not hasattr(registry, "_auditlog_model_cache"):
            registry._auditlog_model_cache = {}
        return registry._auditlog_model_cache

    def _auditlog_field_cache(self):
        registry = self.env.registry
        if not hasattr(registry, "_auditlog_field_cache"):
            registry._auditlog_field_cache = {}
        return registry._auditlog_field_cache

    def _register_hook(self):
        result = super()._register_hook()
        self._auditlog_model_cache()
        self._auditlog_field_cache()
        self.sudo().search([("state", "=", "confirmed")])._patch_methods()
        return result

    def _signal_registry_change(self):
        if modules.module.current_test:
            return
        self.env.registry.registry_invalidated = True

    @api.model
    def _patch_method(self, model_class, method_name, method):
        method.origin = getattr(model_class, method_name)
        method._auditlog_own = method_name in model_class.__dict__
        method._auditlog_patch = True
        setattr(model_class, method_name, method)
        setattr(model_class, f"auditlog_ruled_{method_name}", True)
        return True

    @api.model
    def _revert_method(self, model_class, method_name):
        marker = f"auditlog_ruled_{method_name}"
        if not model_class.__dict__.get(marker):
            return False
        current = model_class.__dict__.get(method_name)
        if current is not None and getattr(current, "_auditlog_patch", False):
            if current._auditlog_own:
                setattr(model_class, method_name, current.origin)
            else:
                delattr(model_class, method_name)
        delattr(model_class, marker)
        return True

    def _patch_methods(self):
        updated = False
        registry = self.env.registry
        model_cache = self._auditlog_model_cache()
        for rule in self:
            model_name = rule.model_id.model or rule.model_model
            if rule.state != "confirmed" or not model_name or model_name not in registry:
                continue
            model_cache[model_name] = rule.model_id.id
            model_class = registry[model_name]
            for method_name in LOGGABLE_METHODS:
                if rule[f"log_{method_name}"] and not model_class.__dict__.get(f"auditlog_ruled_{method_name}"):
                    maker = getattr(rule, f"_make_{method_name}")
                    updated |= rule._patch_method(model_class, method_name, maker())
        return updated

    def _revert_patches(self):
        """Revert every patch installed for the rules' models, based on the
        ``auditlog_ruled_<method>`` markers rather than the current flags."""
        updated = False
        registry = self.env.registry
        for rule in self.exists():
            model_name = rule.model_id.model or rule.model_model
            if not model_name or model_name not in registry:
                continue
            model_class = registry[model_name]
            for method_name in LOGGABLE_METHODS:
                updated |= rule._revert_method(model_class, method_name)
        return updated

    def _revert_methods(self):
        updated = self._revert_patches()
        if updated:
            self._signal_registry_change()
        return updated

    # ------------------------------------------------------------------
    # Live configuration
    # ------------------------------------------------------------------

    @api.model
    def _auditlog_live_rule(self, rule_id):
        return self.sudo().with_context(active_test=False, auditlog_disabled=True).search(
            [("id", "=", rule_id), ("state", "=", "confirmed")], limit=1
        )

    def _is_user_excluded(self, uid):
        return uid in self.users_to_exclude_ids.ids

    @api.model
    def _write_guard_key(self, records, vals):
        digest = hashlib.sha1(
            repr(sorted((key, repr(val)) for key, val in vals.items())).encode()
        ).hexdigest()
        return "%s:%s:%s" % (records._name, ",".join(map(str, sorted(records.ids))), digest)

    @api.model
    def _update_vals_list(self, vals_list):
        """Normalized snapshot of ``vals_list`` for the log path; the list the
        ORM receives is left untouched."""
        return [_normalize_value(dict(vals)) for vals in vals_list]

    def get_auditlog_fields(self, model):
        excluded = set(self.fields_to_exclude_ids.mapped("name"))
        return [
            name
            for name, field in model._fields.items()
            if ((not field.compute and not field.related) or field.store)
            and field.type != "binary"
            and name not in FIELDS_BLACKLIST
            and name not in excluded
        ]

    def _read_audit_values(self, records):
        if not records:
            return {}
        field_names = self.get_auditlog_fields(records)
        data = records.sudo().with_context(auditlog_disabled=True, active_test=False).read(
            field_names, load="_classic_read"
        )
        return {values["id"]: values for values in data}

    # ------------------------------------------------------------------
    # Patched method factories: closures capture the rule id only
    # ------------------------------------------------------------------

    def _make_create(self):
        rule_id = self.id

        @api.model_create_multi
        def create(self, vals_list, **kwargs):
            rule = self.env["auditlog.rule"]._auditlog_live_rule(rule_id)
            if not rule or rule._is_user_excluded(self.env.uid):
                return create.origin(self, vals_list, **kwargs)
            if rule.log_type == "fast":
                snapshot = rule._update_vals_list(vals_list)
                records = create.origin(self, vals_list, **kwargs)
                new_values = {
                    record.id: values
                    for record, values in zip(records, snapshot, strict=True)
                }
            else:
                records = create.origin(self, vals_list, **kwargs)
                new_values = rule._read_audit_values(records)
            rule._create_logs_for_rule(
                self.env.uid, self._name, records.ids, "create", None, new_values
            )
            return records

        return create

    def _make_write(self):
        rule_id = self.id

        def write(self, vals, **kwargs):
            rule = self.env["auditlog.rule"]._auditlog_live_rule(rule_id)
            if not rule or rule._is_user_excluded(self.env.uid):
                return write.origin(self, vals, **kwargs)
            guard_key = rule._write_guard_key(self, vals)
            guard = self.env.context.get("auditlog_write_guard") or ()
            if guard_key in guard:
                return write.origin(self, vals, **kwargs)
            guarded = self.with_context(auditlog_write_guard=(*guard, guard_key))
            if rule.log_type == "fast":
                snapshot = rule._update_vals_list([vals])[0]
                old_values = {res_id: dict.fromkeys(snapshot, False) for res_id in self.ids}
                result = write.origin(guarded, vals, **kwargs)
                new_values = {res_id: snapshot for res_id in self.ids}
            else:
                old_values = rule._read_audit_values(self)
                result = write.origin(guarded, vals, **kwargs)
                new_values = rule._read_audit_values(self)
            rule._create_logs_for_rule(
                self.env.uid, self._name, self.ids, "write", old_values, new_values
            )
            return result

        return write

    def _make_unlink(self):
        rule_id = self.id

        def unlink(self, **kwargs):
            rule = self.env["auditlog.rule"]._auditlog_live_rule(rule_id)
            if not rule or rule._is_user_excluded(self.env.uid):
                return unlink.origin(self, **kwargs)
            old_values = rule._read_audit_values(self) if rule.capture_record else None
            rule._create_logs_for_rule(
                self.env.uid, self._name, self.ids, "unlink", old_values, None
            )
            return unlink.origin(self, **kwargs)

        return unlink

    def _make_read(self):
        rule_id = self.id

        def read(self, fields=None, load="_classic_read", **kwargs):
            context = self.env.context
            if context.get("auditlog_disabled") or context.get("auditlog_disabled_read"):
                return read.origin(self, fields, load, **kwargs)
            rule = self.env["auditlog.rule"]._auditlog_live_rule(rule_id)
            if not rule or rule._is_user_excluded(self.env.uid):
                return read.origin(self, fields, load, **kwargs)
            result = read.origin(self, fields, load, **kwargs)
            read_values = {
                values["id"]: values
                for values in result
                if isinstance(values, dict) and values.get("id")
            }
            if read_values:
                rule._create_logs_for_rule(
                    self.env.uid, self._name, list(read_values), "read", read_values, None
                )
            return result

        return read

    def _make_export_data(self):
        rule_id = self.id

        def export_data(self, fields_to_export, **kwargs):
            rule = self.env["auditlog.rule"]._auditlog_live_rule(rule_id)
            if not rule or rule._is_user_excluded(self.env.uid):
                return export_data.origin(self, fields_to_export, **kwargs)
            result = export_data.origin(
                self.with_context(auditlog_disabled_read=True), fields_to_export, **kwargs
            )
            rule._create_logs_for_rule(
                self.env.uid, self._name, self.ids, "export_data", None, None
            )
            return result

        return export_data

    # ------------------------------------------------------------------
    # Log creation
    # ------------------------------------------------------------------

    @api.model
    def create_logs(self, uid, res_model, res_ids, method,
                    old_values=None, new_values=None, additional_log_values=None):
        """Create logs for ``res_ids`` of ``res_model``; the rule configuration
        is always read fresh from the database."""
        model_id = self._auditlog_model_cache().get(res_model)
        if not model_id:
            _logger.warning(
                "Auditlog: model %s is not in the audit cache, %s not logged", res_model, method
            )
            return False
        rule = self.sudo().with_context(active_test=False).search(
            [("model_id", "=", model_id), ("state", "=", "confirmed")], limit=1
        )
        if not rule:
            return False
        return rule._create_logs_for_rule(
            uid, res_model, res_ids, method, old_values, new_values, additional_log_values
        )

    def _create_logs_for_rule(self, uid, res_model, res_ids, method,
                              old_values=None, new_values=None, additional_log_values=None):
        self.ensure_one()
        model_id = self._auditlog_model_cache().get(res_model)
        if not model_id:
            _logger.warning(
                "Auditlog: model %s is not in the audit cache, %s not logged", res_model, method
            )
            return False
        if not res_ids:
            return False
        if getattr(self.env.cr, "readonly", False):
            with self.env.registry.cursor() as cr:
                return self.with_env(self.env(cr=cr))._create_logs_for_rule(
                    uid, res_model, res_ids, method, old_values, new_values, additional_log_values
                )
        rule = self.sudo().with_context(auditlog_disabled=True)
        args = (uid, res_model, model_id, list(res_ids), method,
                old_values or {}, new_values or {}, additional_log_values or {})
        if rule.log_failure_policy == "skip":
            try:
                with self.env.cr.savepoint():
                    rule._do_create_logs(*args)
            except Exception:
                _logger.error(
                    "Auditlog: failed to log %s on %s %s; operation kept (policy: skip)",
                    method, res_model, res_ids, exc_info=True,
                )
                return False
            return True
        rule._do_create_logs(*args)
        return True

    def _do_create_logs(self, uid, res_model, model_id, res_ids, method,
                        old_values, new_values, additional_log_values):
        Model = self.env[res_model].sudo().with_context(active_test=False, auditlog_disabled=True)
        ir_model = self.env["ir.model"].sudo().browse(model_id)
        base_vals = {
            "model_id": model_id,
            "model_name": ir_model.name,
            "model_model": res_model,
            "method": method,
            "user_id": uid,
            "log_type": self.log_type,
            "http_request_id": self.env["auditlog.http.request"].current_http_request(),
            "http_session_id": self.env["auditlog.http.session"].current_http_session(),
        }
        base_vals.update(additional_log_values)
        records = Model.browse(res_ids).exists()
        companies = self._get_record_companies(records)

        if method == "export_data":
            company_ids = set(companies.values())
            base_vals.update({
                "name": Model._description,
                "res_ids": json.dumps(res_ids),
                "company_id": company_ids.pop() if len(company_ids) == 1 else False,
            })
            self.env["auditlog.log"].create([base_vals])
            return

        names = {record.id: record.display_name for record in records}
        field_meta = self._get_field_meta(res_model)
        excluded = set(self.fields_to_exclude_ids.mapped("name")) | FIELDS_BLACKLIST
        all_vals = []
        for res_id in res_ids:
            old = old_values.get(res_id, {})
            new = new_values.get(res_id, {})
            if method == "create":
                field_names = [name for name, value in new.items() if not _is_empty(value)]
            elif method == "write":
                field_names = [name for name in new if name in old and old[name] != new[name]]
            elif method == "read" or (method == "unlink" and self.capture_record):
                field_names = list(old)
            else:
                field_names = []
            lines = [
                (0, 0, self._prepare_log_line_vals(res_model, field_meta[name], old.get(name), new.get(name)))
                for name in field_names
                if name not in excluded and name in field_meta
            ]
            all_vals.append(dict(
                base_vals,
                name=names.get(res_id, False),
                res_id=res_id,
                company_id=companies.get(res_id, False),
                line_ids=lines,
            ))
        self.env["auditlog.log"].create(all_vals)

    @api.model
    def _get_record_companies(self, records):
        field = records._fields.get("company_id")
        if not field or field.type != "many2one" or field.comodel_name != "res.company":
            return {}
        return {record.id: record.company_id.id for record in records}

    @api.model
    def _get_field_meta(self, res_model):
        cache = self._auditlog_field_cache()
        if res_model not in cache:
            fields_data = self.env["ir.model.fields"].sudo().with_context(auditlog_disabled=True).search_read(
                [("model", "=", res_model)],
                ["name", "field_description", "ttype", "relation"],
            )
            cache[res_model] = {field["name"]: field for field in fields_data}
        return cache[res_model]

    @api.model
    def _prepare_log_line_vals(self, res_model, meta, old_value, new_value):
        return {
            "field_id": meta["id"],
            "field_name": meta["name"],
            "field_description": meta["field_description"],
            "old_value": False if old_value is None else str(old_value),
            "new_value": False if new_value is None else str(new_value),
            "old_value_text": self._format_value(res_model, meta, old_value),
            "new_value_text": self._format_value(res_model, meta, new_value),
        }

    @api.model
    def _format_value(self, res_model, meta, value):
        if value is None:
            return False
        ttype = meta["ttype"]
        relation = meta.get("relation")
        if ttype == "many2one":
            if isinstance(value, (list, tuple)) and len(value) == 2 and isinstance(value[1], str):
                return value[1]
            ids = value if isinstance(value, list) else [value] if isinstance(value, int) and value else []
            if ids and relation and relation in self.env:
                related = self.env[relation].sudo().with_context(
                    active_test=False, auditlog_disabled=True
                ).browse(ids).exists()
                return ", ".join(related.mapped("display_name")) or str(value)
            return False if value is False else str(value)
        if ttype in ("one2many", "many2many"):
            ids = _extract_ids(value)
            if ids is None or not relation or relation not in self.env:
                return str(value)
            related = self.env[relation].sudo().with_context(
                active_test=False, auditlog_disabled=True
            ).browse(ids).exists()
            names = {record.id: record.display_name for record in related}
            return ", ".join(names.get(i, "%s (DELETED)" % i) for i in ids)
        if ttype == "selection" and value is not False:
            field = self.env[res_model]._fields.get(meta["name"])
            try:
                labels = dict(field._description_selection(self.env)) if field else {}
            except (AttributeError, TypeError, ValueError):
                labels = {}
            return labels.get(value, str(value))
        if value is False and ttype != "boolean":
            return False
        return str(value)
