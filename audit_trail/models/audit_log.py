import json
import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .audit_rule import ACTION_SELECTION, DETAIL_LEVEL_SELECTION

_logger = logging.getLogger(__name__)

CLEANUP_CRON_XML_ID = "audit_trail.ir_cron_audit_log_cleanup"

DEFAULT_RETENTION_DAYS = 180
DEFAULT_BATCH_SIZE = 1000


class AuditLog(models.Model):
    _name = "audit.log"
    _description = "Audit Log Entry"
    _order = "date desc, id desc"

    rule_id = fields.Many2one(
        comodel_name="audit.rule",
        string="Watch Rule",
        readonly=True,
        index=True,
        ondelete="set null",
    )
    res_model = fields.Char(string="Technical Model", readonly=True, index=True)
    res_id = fields.Integer(string="Record ID", readonly=True, index=True)
    record_name = fields.Char(string="Record", readonly=True)
    action = fields.Selection(
        selection=ACTION_SELECTION,
        readonly=True,
        index=True,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        readonly=True,
        index=True,
        ondelete="set null",
    )
    date = fields.Datetime(readonly=True, index=True)
    detail_level = fields.Selection(
        selection=DETAIL_LEVEL_SELECTION,
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        readonly=True,
        index=True,
    )
    session_id = fields.Many2one(
        comodel_name="audit.session",
        string="Session",
        readonly=True,
        index=True,
        ondelete="set null",
    )
    page_action_id = fields.Many2one(
        comodel_name="audit.page.action",
        string="Screen",
        readonly=True,
        index=True,
        ondelete="set null",
    )
    deleted_snapshot = fields.Text(
        string="Deletion Snapshot",
        readonly=True,
        help="Field values captured at the moment the record was deleted. "
             "Excluded fields are scrubbed before storing.",
    )
    exported_res_ids = fields.Text(
        string="Exported Record IDs",
        readonly=True,
    )
    line_ids = fields.One2many(
        comodel_name="audit.log.line",
        inverse_name="log_id",
        string="Field Changes",
        readonly=True,
    )
    exported_count = fields.Integer(compute="_compute_exported_count")

    @api.depends("exported_res_ids")
    def _compute_exported_count(self):
        for log in self:
            log.exported_count = len(log._audit_exported_ids())

    @api.depends("record_name", "res_model", "action")
    def _compute_display_name(self):
        labels = dict(ACTION_SELECTION)
        for log in self:
            log.display_name = "%s: %s" % (
                labels.get(log.action, log.action or ""),
                log.record_name or log.res_model or "",
            )

    def _audit_exported_ids(self):
        self.ensure_one()
        if not self.exported_res_ids:
            return []
        try:
            parsed = json.loads(self.exported_res_ids)
        except (TypeError, ValueError):
            return []
        if not isinstance(parsed, list):
            return []
        return [entry for entry in parsed if isinstance(entry, int)]

    def action_view_exported_records(self):
        self.ensure_one()
        res_ids = self._audit_exported_ids()
        if not res_ids:
            raise UserError(_("This event does not carry any exported record."))
        if not self.res_model or self.res_model not in self.env:
            raise UserError(_(
                "The model %s is no longer installed on this database.",
                self.res_model or "",
            ))
        return {
            "type": "ir.actions.act_window",
            "name": _("Exported Records"),
            "res_model": self.res_model,
            "view_mode": "list,form",
            "domain": [("id", "in", res_ids)],
            "target": "current",
        }

    @api.model
    def _audit_cleanup_settings(self):
        params = self.env["ir.config_parameter"].sudo()
        enabled = params.get_param("audit_trail.cleanup_enabled", "False")
        try:
            retention_days = int(
                params.get_param("audit_trail.retention_days", DEFAULT_RETENTION_DAYS)
            )
        except (TypeError, ValueError):
            retention_days = DEFAULT_RETENTION_DAYS
        try:
            batch_size = int(
                params.get_param("audit_trail.batch_size", DEFAULT_BATCH_SIZE)
            )
        except (TypeError, ValueError):
            batch_size = DEFAULT_BATCH_SIZE
        return {
            "enabled": str(enabled).lower() in ("true", "1", "yes"),
            "retention_days": retention_days if retention_days > 0 else DEFAULT_RETENTION_DAYS,
            "batch_size": batch_size if batch_size > 0 else DEFAULT_BATCH_SIZE,
        }

    @api.model
    def _cron_cleanup_logs(self):
        """Delete expired events, sessions and screens one batch at a time.

        Disabled unless clean-up was explicitly turned on. Events are purged
        against the retention window first; empty sessions and screens (rows
        with no event left pointing at them) are then retired against the
        same window, so those two supporting tables cannot grow forever
        regardless of retention_days. When any batch fills up, the cron
        re-triggers itself so a large first run never holds a long
        transaction open.
        """
        settings = self._audit_cleanup_settings()
        if not settings["enabled"]:
            return False
        limit_date = fields.Datetime.now() - timedelta(days=settings["retention_days"])
        batch_size = settings["batch_size"]

        expired = self.sudo().search(
            [("date", "<", limit_date)], order="date asc, id asc", limit=batch_size
        )
        logs_removed = len(expired)
        if expired:
            expired.unlink()
            _logger.info("Audit trail clean-up removed %s events older than %s.",
                         logs_removed, limit_date)

        sessions_removed = self.env["audit.session"]._cron_cleanup_sessions(
            limit_date, batch_size
        )
        page_actions_removed = self.env["audit.page.action"]._cron_cleanup_page_actions(
            limit_date, batch_size
        )

        if (
            logs_removed >= batch_size
            or sessions_removed >= batch_size
            or page_actions_removed >= batch_size
        ):
            cron = self.env.ref(CLEANUP_CRON_XML_ID, raise_if_not_found=False)
            if cron:
                cron.sudo()._trigger()
        return bool(logs_removed or sessions_removed or page_actions_removed)
