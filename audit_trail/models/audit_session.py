import logging
from datetime import timedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

DEFAULT_INACTIVITY_MINUTES = 30


class AuditSession(models.Model):
    _name = "audit.session"
    _description = "Audit Working Session"
    _order = "start_datetime desc, id desc"

    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        readonly=True,
        index=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        readonly=True,
        index=True,
    )
    start_datetime = fields.Datetime(readonly=True, index=True)
    last_activity_datetime = fields.Datetime(readonly=True, index=True)
    log_ids = fields.One2many(
        comodel_name="audit.log",
        inverse_name="session_id",
        string="Events",
        readonly=True,
    )
    page_action_ids = fields.One2many(
        comodel_name="audit.page.action",
        inverse_name="session_id",
        string="Screens Visited",
        readonly=True,
    )
    log_count = fields.Integer(compute="_compute_log_count")

    @api.depends("log_ids")
    def _compute_log_count(self):
        grouped = self.env["audit.log"].sudo()._read_group(
            [("session_id", "in", self.ids)],
            groupby=["session_id"],
            aggregates=["__count"],
        )
        counts = {session.id: count for session, count in grouped}
        for session in self:
            session.log_count = counts.get(session.id, 0)

    @api.depends("user_id", "start_datetime")
    def _compute_display_name(self):
        for session in self:
            if session.start_datetime:
                start = fields.Datetime.context_timestamp(
                    session, session.start_datetime
                ).strftime("%Y-%m-%d %H:%M")
            else:
                start = _("unknown start")
            session.display_name = "%s / %s" % (
                session.user_id.display_name or _("Unknown user"),
                start,
            )

    @api.model
    def _audit_inactivity_minutes(self):
        raw = self.env["ir.config_parameter"].sudo().get_param(
            "audit_trail.inactivity_minutes", DEFAULT_INACTIVITY_MINUTES
        )
        try:
            minutes = int(raw)
        except (TypeError, ValueError):
            minutes = DEFAULT_INACTIVITY_MINUTES
        return minutes if minutes > 0 else DEFAULT_INACTIVITY_MINUTES

    @api.model
    def _audit_current_session(self, company_id):
        """Reuse the acting user's open session, or open a new one.

        A gap longer than the inactivity timeout starts a new session rather
        than extending the previous one.
        """
        now = fields.Datetime.now()
        threshold = now - timedelta(minutes=self._audit_inactivity_minutes())
        sessions = self.sudo()
        session = sessions.search(
            [
                ("user_id", "=", self.env.uid),
                ("company_id", "=", company_id),
                ("last_activity_datetime", ">=", threshold),
            ],
            order="last_activity_datetime desc",
            limit=1,
        )
        if session:
            session.last_activity_datetime = now
            return session
        return sessions.create({
            "user_id": self.env.uid,
            "company_id": company_id,
            "start_datetime": now,
            "last_activity_datetime": now,
        })

    def action_view_logs(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "audit_trail.action_audit_log"
        )
        action["domain"] = [("session_id", "=", self.id)]
        action["context"] = {"search_default_group_by_page_action": 1}
        return action

    @api.model
    def _cron_cleanup_sessions(self, limit_date, batch_size):
        """Delete stale sessions that no longer carry any event.

        A session with events left is never removed, even past
        ``limit_date`` — its own events keep it alive until they expire on
        their own pass. Deleting a session cascades (DB ondelete) to any
        audit.page.action rows still pointing at it.

        Emptiness is decided with an aggregate read over audit.log rather
        than a ``('log_ids', '=', False)`` one2many-negation leaf: the
        latter does not reliably reflect logs unlinked earlier in this same
        clean-up transaction, so genuinely empty, expired sessions were
        being skipped.
        """
        candidates = self.sudo().search(
            [("last_activity_datetime", "<", limit_date)],
            order="last_activity_datetime asc, id asc",
            limit=batch_size,
        )
        if not candidates:
            return 0
        grouped = self.env["audit.log"].sudo()._read_group(
            [("session_id", "in", candidates.ids)],
            groupby=["session_id"],
            aggregates=["__count"],
        )
        with_logs = {session.id for session, count in grouped if count}
        expired = candidates.filtered(lambda s: s.id not in with_logs)
        removed = len(expired)
        if expired:
            expired.unlink()
            _logger.info(
                "Audit trail clean-up removed %s empty sessions older than %s.",
                removed, limit_date,
            )
        return removed
