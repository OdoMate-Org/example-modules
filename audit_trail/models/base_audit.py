import json
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

AUDIT_OWN_MODELS = frozenset({
    "audit.rule",
    "audit.log",
    "audit.log.line",
    "audit.session",
    "audit.page.action",
    "audit.config",
})

MAGIC_FIELD_NAMES = frozenset({
    "id",
    "display_name",
    "create_uid",
    "create_date",
    "write_uid",
    "write_date",
    "__last_update",
})

UNTRACKABLE_FIELD_TYPES = frozenset({"one2many", "binary"})

MAX_VALUE_LENGTH = 2000


class Base(models.AbstractModel):
    _inherit = "base"

    def _audit_is_watched(self):
        if self._name in AUDIT_OWN_MODELS or self._transient or self._abstract:
            return False
        if self.env.context.get("audit_trail_skip"):
            return False
        try:
            if not self.env.registry.ready:
                return False
            watched = self.env["audit.rule"]._audit_watched_model_names()
        except Exception:
            return False
        return self._name in watched

    def _audit_config_for_company(self, company_id):
        return self.env["audit.rule"]._audit_rule_config(self._name, company_id)

    def _audit_group_by_company(self):
        field = self._fields.get("company_id")
        fallback = self.env.company.id
        if not field or field.type != "many2one" or field.comodel_name != "res.company":
            return {fallback: self}
        groups = {}
        for record in self:
            try:
                company_id = record.company_id.id or fallback
            except Exception:
                company_id = fallback
            groups[company_id] = groups.get(company_id, self.browse()) | record
        return groups

    def _audit_field_names(self, excluded_fields):
        names = []
        for name, field in self._fields.items():
            if name in MAGIC_FIELD_NAMES or name in excluded_fields:
                continue
            if field.type in UNTRACKABLE_FIELD_TYPES or not field.store:
                continue
            names.append(name)
        return names

    def _audit_changed_field_names(self, vals, excluded_fields):
        return [
            name for name in vals
            if name in self._fields
            and name not in MAGIC_FIELD_NAMES
            and name not in excluded_fields
            and self._fields[name].type not in UNTRACKABLE_FIELD_TYPES
        ]

    def _audit_read_values(self, field_names):
        if not field_names or not self:
            return {}
        try:
            rows = self.sudo().read(list(field_names))
        except Exception:
            _logger.exception(
                "Audit trail could not read values of %s while recording an event.",
                self._name,
            )
            return {}
        return {row["id"]: row for row in rows}

    def _audit_display_names(self):
        if not self:
            return {}
        try:
            rows = self.sudo().read(["display_name"])
        except Exception:
            return {}
        return {row["id"]: row.get("display_name") or "" for row in rows}

    def _audit_truncate(self, value):
        text = str(value)
        if len(text) > MAX_VALUE_LENGTH:
            return text[:MAX_VALUE_LENGTH] + "..."
        return text

    def _audit_format_value(self, field_name, value):
        field = self._fields.get(field_name)
        if value is None:
            return ""
        if value is False:
            return "False" if field is not None and field.type == "boolean" else ""
        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], int):
            return self._audit_truncate(value[1])
        if isinstance(value, (list, tuple)):
            if field is not None and field.comodel_name and field.comodel_name in self.env:
                comodel = self.env[field.comodel_name].sudo()
                linked = comodel.browse([v for v in value if isinstance(v, int)]).exists()
                return self._audit_truncate(", ".join(linked.mapped("display_name")))
            return self._audit_truncate(", ".join(str(item) for item in value))
        if field is not None and field.type == "selection":
            labels = dict(field._description_selection(self.env))
            return self._audit_truncate(labels.get(value, value))
        return self._audit_truncate(value)

    def _audit_field_records(self, field_names):
        if not field_names:
            return {}
        try:
            records = self.env["ir.model.fields"].sudo().search([
                ("model", "=", self._name),
                ("name", "in", list(field_names)),
            ])
        except Exception:
            return {}
        return {record.name: record for record in records}

    def _audit_line_command(self, field_name, field_records, old_value, new_value):
        field_record = field_records.get(field_name)
        description = field_record.field_description if field_record else None
        if not description:
            field = self._fields.get(field_name)
            description = field.string if field is not None else field_name
        return fields.Command.create({
            "field_id": field_record.id if field_record else False,
            "field_description": description,
            "old_value": old_value,
            "new_value": new_value,
        })

    def _audit_context(self, company_id):
        session = self.env["audit.session"]._audit_current_session(company_id)
        page_action = self.env["audit.page.action"]._audit_current_page_action(
            session, self._name
        )
        return session, page_action

    def _audit_base_log_vals(self, config, action, company_id, session, page_action):
        return {
            "rule_id": config["rule_id"],
            "res_model": self._name,
            "action": action,
            "user_id": self.env.uid,
            "date": fields.Datetime.now(),
            "detail_level": config["detail_level"],
            "company_id": company_id,
            "session_id": session.id if session else False,
            "page_action_id": page_action.id if page_action else False,
        }

    def _audit_applicable_config(self, company_id, action):
        config = self._audit_config_for_company(company_id)
        if not config or action not in config["actions"]:
            return None
        if self.env.uid in config["excluded_user_ids"]:
            return None
        return config

    def _audit_store(self, log_vals_list):
        if log_vals_list:
            self.env["audit.log"].sudo().create(log_vals_list)

    def _audit_track_create(self, vals_list):
        vals_by_id = {}
        for record, vals in zip(self, vals_list):
            vals_by_id[record.id] = vals or {}
        for company_id, records in self._audit_group_by_company().items():
            config = records._audit_applicable_config(company_id, "create")
            if not config:
                continue
            excluded = config["excluded_fields"]
            if config["detail_level"] == "full":
                read_names = records._audit_field_names(excluded)
                per_record_names = {
                    record.id: read_names for record in records
                }
            else:
                per_record_names = {
                    record.id: records._audit_changed_field_names(
                        vals_by_id.get(record.id, {}), excluded
                    )
                    for record in records
                }
                read_names = sorted({
                    name for names in per_record_names.values() for name in names
                })
            values_by_id = records._audit_read_values(read_names)
            names = records._audit_display_names()
            field_records = records._audit_field_records(read_names)
            session, page_action = records._audit_context(company_id)
            log_vals_list = []
            for record in records:
                row = values_by_id.get(record.id, {})
                commands = []
                for name in per_record_names.get(record.id, []):
                    value = row.get(name)
                    if value in (False, None, [], ""):
                        continue
                    commands.append(records._audit_line_command(
                        name,
                        field_records,
                        "",
                        records._audit_format_value(name, value),
                    ))
                log_vals = records._audit_base_log_vals(
                    config, "create", company_id, session, page_action
                )
                log_vals.update({
                    "res_id": record.id,
                    "record_name": names.get(record.id, ""),
                    "line_ids": commands,
                })
                log_vals_list.append(log_vals)
            records._audit_store(log_vals_list)

    def _audit_prepare_write(self, vals):
        plan = {}
        for company_id, records in self._audit_group_by_company().items():
            config = records._audit_applicable_config(company_id, "write")
            if not config:
                continue
            changed = records._audit_changed_field_names(vals, config["excluded_fields"])
            if not changed:
                continue
            old_values = {}
            if config["detail_level"] == "full":
                old_values = records._audit_read_values(changed)
            plan[company_id] = {
                "config": config,
                "record_ids": records.ids,
                "changed": changed,
                "old_values": old_values,
            }
        return plan

    def _audit_track_write(self, plan):
        for company_id, entry in plan.items():
            config = entry["config"]
            changed = entry["changed"]
            records = self.browse(entry["record_ids"]).exists()
            if not records:
                continue
            new_values = records._audit_read_values(changed)
            names = records._audit_display_names()
            field_records = records._audit_field_records(changed)
            session, page_action = records._audit_context(company_id)
            full_detail = config["detail_level"] == "full"
            log_vals_list = []
            for record in records:
                new_row = new_values.get(record.id, {})
                old_row = entry["old_values"].get(record.id, {}) if full_detail else {}
                commands = []
                for name in changed:
                    new_value = records._audit_format_value(name, new_row.get(name))
                    old_value = (
                        records._audit_format_value(name, old_row.get(name))
                        if full_detail else ""
                    )
                    if full_detail and old_value == new_value:
                        continue
                    commands.append(records._audit_line_command(
                        name, field_records, old_value, new_value
                    ))
                if not commands:
                    continue
                log_vals = records._audit_base_log_vals(
                    config, "write", company_id, session, page_action
                )
                log_vals.update({
                    "res_id": record.id,
                    "record_name": names.get(record.id, ""),
                    "line_ids": commands,
                })
                log_vals_list.append(log_vals)
            records._audit_store(log_vals_list)

    def _audit_prepare_unlink(self):
        plan = {}
        for company_id, records in self._audit_group_by_company().items():
            config = records._audit_applicable_config(company_id, "unlink")
            if not config:
                continue
            names = records._audit_display_names()
            snapshots = {}
            if config["keep_deleted_snapshot"]:
                snapshot_names = records._audit_field_names(config["excluded_fields"])
                rows = records._audit_read_values(snapshot_names)
                for record in records:
                    row = rows.get(record.id, {})
                    snapshot = {}
                    for name in snapshot_names:
                        value = row.get(name)
                        if value in (False, None, [], ""):
                            continue
                        snapshot[name] = records._audit_format_value(name, value)
                    snapshots[record.id] = snapshot
            plan[company_id] = {
                "config": config,
                "record_ids": records.ids,
                "names": names,
                "snapshots": snapshots,
            }
        return plan

    def _audit_track_unlink(self, plan):
        for company_id, entry in plan.items():
            config = entry["config"]
            session, page_action = self._audit_context(company_id)
            log_vals_list = []
            for record_id in entry["record_ids"]:
                log_vals = self._audit_base_log_vals(
                    config, "unlink", company_id, session, page_action
                )
                snapshot = entry["snapshots"].get(record_id)
                log_vals.update({
                    "res_id": record_id,
                    "record_name": entry["names"].get(record_id, ""),
                    "deleted_snapshot": (
                        json.dumps(snapshot, indent=2, sort_keys=True, default=str)
                        if snapshot else False
                    ),
                })
                log_vals_list.append(log_vals)
            self._audit_store(log_vals_list)

    def _audit_track_export(self):
        for company_id, records in self._audit_group_by_company().items():
            config = records._audit_applicable_config(company_id, "export")
            if not config:
                continue
            session, page_action = records._audit_context(company_id)
            log_vals = records._audit_base_log_vals(
                config, "export", company_id, session, page_action
            )
            if len(records) == 1:
                names = records._audit_display_names()
                record_name = names.get(records.id, "")
                res_id = records.id
            else:
                record_name = _("%s records", len(records))
                res_id = 0
            log_vals.update({
                "res_id": res_id,
                "record_name": record_name,
                "exported_res_ids": json.dumps(records.ids),
            })
            records._audit_store([log_vals])

    def _audit_track_read(self):
        if getattr(self.env.cr, "readonly", False):
            return
        for company_id, records in self._audit_group_by_company().items():
            config = records._audit_applicable_config(company_id, "read")
            if not config:
                continue
            names = records._audit_display_names()
            session, page_action = records._audit_context(company_id)
            log_vals_list = []
            for record in records:
                log_vals = records._audit_base_log_vals(
                    config, "read", company_id, session, page_action
                )
                log_vals.update({
                    "res_id": record.id,
                    "record_name": names.get(record.id, ""),
                })
                log_vals_list.append(log_vals)
            records._audit_store(log_vals_list)

    def action_view_audit_logs(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "audit_trail.action_audit_log"
        )
        action["domain"] = [("res_model", "=", self._name), ("res_id", "=", self.id)]
        action["context"] = {"search_default_group_by_action": 1}
        action["display_name"] = _("Audit trail of %s", self.display_name)
        return action

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if records._audit_is_watched():
            try:
                records._audit_track_create(vals_list)
            except Exception:
                _logger.exception(
                    "Audit trail could not record the creation of %s records.",
                    records._name,
                )
        return records

    def write(self, vals):
        plan = None
        if vals and self._audit_is_watched():
            try:
                plan = self._audit_prepare_write(vals)
            except Exception:
                _logger.exception(
                    "Audit trail could not capture the previous values of %s.",
                    self._name,
                )
                plan = None
        result = super().write(vals)
        if plan:
            try:
                self._audit_track_write(plan)
            except Exception:
                _logger.exception(
                    "Audit trail could not record an update on %s.", self._name
                )
        return result

    def unlink(self):
        plan = None
        if self._audit_is_watched():
            try:
                plan = self._audit_prepare_unlink()
            except Exception:
                _logger.exception(
                    "Audit trail could not capture the deletion snapshot of %s.",
                    self._name,
                )
                plan = None
        result = super().unlink()
        if plan:
            try:
                self._audit_track_unlink(plan)
            except Exception:
                _logger.exception(
                    "Audit trail could not record a deletion on %s.", self._name
                )
        return result

    def export_data(self, *args, **kwargs):
        result = super().export_data(*args, **kwargs)
        if self._audit_is_watched():
            try:
                self._audit_track_export()
            except Exception:
                _logger.exception(
                    "Audit trail could not record an export of %s.", self._name
                )
        return result

    def web_read(self, *args, **kwargs):
        result = super().web_read(*args, **kwargs)
        if not self.env.context.get("audit_trail_skip_read") and self._audit_is_watched():
            try:
                self._audit_track_read()
            except Exception:
                _logger.exception(
                    "Audit trail could not record a view of %s.", self._name
                )
        return result

    def web_save(self, *args, **kwargs):
        return super(Base, self.with_context(audit_trail_skip_read=True)).web_save(
            *args, **kwargs
        )

    @api.model
    def web_name_search(self, *args, **kwargs):
        return super(Base, self.with_context(audit_trail_skip=True)).web_name_search(
            *args, **kwargs
        )
