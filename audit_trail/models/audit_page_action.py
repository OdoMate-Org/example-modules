import logging

from odoo import _, api, fields, models, tools

_logger = logging.getLogger(__name__)


class AuditPageAction(models.Model):
    _name = "audit.page.action"
    _description = "Audit Screen / Action"
    _order = "id desc"

    name = fields.Char(string="Screen", readonly=True)
    res_model = fields.Char(string="Technical Model", readonly=True, index=True)
    session_id = fields.Many2one(
        comodel_name="audit.session",
        string="Session",
        readonly=True,
        index=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="session_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    last_activity_datetime = fields.Datetime(
        string="Last Activity",
        readonly=True,
        index=True,
        help="Logical timestamp of the most recent event recorded on this "
             "screen. Retention clean-up ages a screen by this value, not by "
             "create_date, so seeded or imported rows expire together with "
             "the events they belong to.",
    )
    log_ids = fields.One2many(
        comodel_name="audit.log",
        inverse_name="page_action_id",
        string="Events",
        readonly=True,
    )

    @api.depends("name", "res_model")
    def _compute_display_name(self):
        for page_action in self:
            page_action.display_name = (
                page_action.name
                or page_action.res_model
                or _("Screen #%s", page_action.id)
            )

    @api.model
    @tools.ormcache("res_model", "self.env.lang")
    def _audit_screen_label(self, res_model):
        window_action = self.env["ir.actions.act_window"].sudo().search(
            [("res_model", "=", res_model)], order="id", limit=1
        )
        if window_action:
            return window_action.name
        model = self.env["ir.model"].sudo()._get(res_model)
        return model.name or res_model

    @api.model
    def _audit_current_page_action(self, session, res_model):
        if not session:
            return self.browse()
        now = fields.Datetime.now()
        page_actions = self.sudo()
        existing = page_actions.search(
            [("session_id", "=", session.id), ("res_model", "=", res_model)],
            limit=1,
        )
        if existing:
            existing.last_activity_datetime = now
            return existing
        return page_actions.create({
            "session_id": session.id,
            "res_model": res_model,
            "name": self._audit_screen_label(res_model),
            "last_activity_datetime": now,
        })

    @api.model
    def _cron_cleanup_page_actions(self, limit_date, batch_size):
        """Delete stale screens that no longer carry any event.

        Catches the case session clean-up alone would miss: a screen whose
        events have all expired while its session is still active because of
        other, newer screens.

        Age is taken from ``last_activity_datetime`` (a logical timestamp
        stamped from the events themselves), never from ``create_date`` —
        seeded, imported or migrated rows carry an install-time create_date
        that would otherwise shield them from retention forever. Rows with
        no logical timestamp yet (pre-existing rows created before this
        field existed) are treated as eligible and gated purely on
        emptiness. Emptiness is decided with an aggregate read over
        audit.log so logs unlinked earlier in this same clean-up
        transaction are reflected reliably.
        """
        candidates = self.sudo().search(
            [
                "|",
                ("last_activity_datetime", "=", False),
                ("last_activity_datetime", "<", limit_date),
            ],
            order="id asc",
            limit=batch_size,
        )
        if not candidates:
            return 0
        grouped = self.env["audit.log"].sudo()._read_group(
            [("page_action_id", "in", candidates.ids)],
            groupby=["page_action_id"],
            aggregates=["__count"],
        )
        with_logs = {page_action.id for page_action, count in grouped if count}
        expired = candidates.filtered(lambda pa: pa.id not in with_logs)
        removed = len(expired)
        if expired:
            expired.unlink()
            _logger.info(
                "Audit trail clean-up removed %s empty screens older than %s.",
                removed, limit_date,
            )
        return removed
