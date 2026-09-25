import hashlib

from odoo import api, fields, models
from odoo.http import request


class AuditlogHttpSession(models.Model):
    _name = "auditlog.http.session"
    _description = "Auditlog - HTTP User session log"
    _order = "create_date DESC"

    display_name = fields.Char(
        string="Name",
        compute="_compute_display_name",
        store=True,
    )
    name = fields.Char(
        string="Session ID",
        index=True,
        help="SHA-256 fingerprint of the HTTP session identifier.",
    )
    user_id = fields.Many2one("res.users", string="User", index=True)
    company_id = fields.Many2one("res.company", string="Company", index=True)
    http_request_ids = fields.One2many(
        "auditlog.http.request",
        "http_session_id",
        string="HTTP Requests",
    )

    @api.depends("create_date", "user_id")
    def _compute_display_name(self):
        for session in self:
            create_date = session.create_date or fields.Datetime.now()
            session.display_name = "{} ({})".format(
                session.user_id.name or "?",
                fields.Datetime.to_string(create_date),
            )

    @api.model
    def _fingerprint(self, sid):
        return hashlib.sha256(sid.encode()).hexdigest()

    @api.model
    def current_http_session(self):
        """Return the id of the audit session matching the current HTTP
        session, creating it on first use; False outside a request."""
        if not request:
            return False
        try:
            http_session = request.session
            env = request.env
        except (AttributeError, RuntimeError):
            return False
        sid = getattr(http_session, "sid", None)
        if not sid:
            return False
        fingerprint = self._fingerprint(sid)
        existing = self.sudo().search(
            [("name", "=", fingerprint), ("user_id", "=", env.uid)], limit=1
        )
        if existing:
            return existing.id
        return self.sudo().create({
            "name": fingerprint,
            "user_id": env.uid,
            "company_id": env.user.company_id.id,
        }).id
