import logging
from datetime import timedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class AuditlogAutovacuum(models.TransientModel):
    _name = "auditlog.autovacuum"
    _description = "Auditlog - Delete old logs"

    days = fields.Integer(
        string="Keep Last (Days)",
        required=True,
        default=180,
        help="Logs, HTTP requests and user sessions older than this number of days are deleted.",
    )
    chunk_size = fields.Integer(
        string="Chunk Size",
        help="Maximum number of records deleted per model in this run. Leave empty to delete all matching records.",
    )

    def action_run(self):
        self.ensure_one()
        self.autovacuum(self.days, chunk_size=self.chunk_size or None)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": _("Audit data older than %(days)s days has been deleted.", days=self.days),
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    @api.model
    def autovacuum(self, days, chunk_size=None):
        """Delete audit data older than ``days`` days, oldest first.

        :param days: retention period; values <= 0 mean "everything up to now"
        :param chunk_size: max records removed per model and per run
        """
        days = max(int(days or 0), 0)
        deadline = fields.Datetime.now() - timedelta(days=days)
        for data_model in (
            "auditlog.log",
            "auditlog.http.request",
            "auditlog.http.session",
        ):
            records = self.env[data_model].sudo().search(
                [("create_date", "<=", deadline)],
                limit=chunk_size,
                order="create_date asc, id asc",
            )
            count = len(records)
            records.unlink()
            _logger.info("AUTOVACUUM - %s '%s' records deleted", count, data_model)
        return True
