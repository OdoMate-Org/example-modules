from odoo import api, fields, models
from odoo.http import request


class AuditlogHttpRequest(models.Model):
    _name = "auditlog.http.request"
    _description = "Auditlog - HTTP request log"
    _order = "create_date DESC"

    display_name = fields.Char(
        string="Name",
        compute="_compute_display_name",
        store=True,
    )
    name = fields.Char(string="Path")
    root_url = fields.Char(string="Root URL")
    user_id = fields.Many2one("res.users", string="User", index=True)
    company_id = fields.Many2one("res.company", string="Company", index=True)
    http_session_id = fields.Many2one(
        "auditlog.http.session", string="Session", index=True
    )
    log_ids = fields.One2many("auditlog.log", "http_request_id", string="Logs")

    @api.depends("create_date", "name")
    def _compute_display_name(self):
        for http_request in self:
            create_date = http_request.create_date or fields.Datetime.now()
            http_request.display_name = "{} ({})".format(
                http_request.name or "?",
                fields.Datetime.to_string(create_date),
            )

    @api.model
    def current_http_request(self):
        """Return the id of the audit record for the current HTTP request,
        creating it on first use; False outside a request."""
        if not request:
            return False
        try:
            httprequest = request.httprequest
            env = request.env
        except (AttributeError, RuntimeError):
            return False
        if not httprequest:
            return False
        cached_id = getattr(httprequest, "auditlog_http_request_id", False)
        if cached_id and self.sudo().browse(cached_id).exists():
            return cached_id
        new_request = self.sudo().create({
            "name": httprequest.path,
            "root_url": httprequest.url_root,
            "user_id": env.uid,
            "company_id": env.user.company_id.id,
            "http_session_id": self.env["auditlog.http.session"].current_http_session(),
        })
        httprequest.auditlog_http_request_id = new_request.id
        return new_request.id
