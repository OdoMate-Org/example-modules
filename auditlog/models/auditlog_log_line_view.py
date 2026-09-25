from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools import SQL

from .common import LOG_TYPE_SELECTION


class AuditlogLogLineView(models.Model):
    _name = "auditlog.log.line.view"
    _inherit = "auditlog.log.line"
    _description = "Auditlog - Log details (view)"
    _auto = False

    company_id = fields.Many2one("res.company", related=False, readonly=True)
    name = fields.Char(string="Resource Name", readonly=True)
    model_id = fields.Many2one("ir.model", string="Model", readonly=True)
    model_name = fields.Char(string="Model Name", readonly=True)
    model_model = fields.Char(string="Technical Model Name", readonly=True)
    res_id = fields.Integer(string="Resource ID", readonly=True)
    user_id = fields.Many2one("res.users", string="User", readonly=True)
    method = fields.Char(readonly=True)
    http_session_id = fields.Many2one(
        "auditlog.http.session", string="Session", readonly=True
    )
    http_request_id = fields.Many2one(
        "auditlog.http.request", string="HTTP Request", readonly=True
    )
    log_type = fields.Selection(LOG_TYPE_SELECTION, string="Type", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(SQL(
            """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    alogl.id,
                    alogl.create_date,
                    alogl.create_uid,
                    alogl.write_date,
                    alogl.write_uid,
                    alogl.field_id,
                    alogl.log_id,
                    alogl.old_value,
                    alogl.new_value,
                    alogl.old_value_text,
                    alogl.new_value_text,
                    alogl.field_name,
                    alogl.field_description,
                    alog.company_id,
                    alog.name,
                    alog.model_id,
                    alog.model_name,
                    alog.model_model,
                    alog.res_id,
                    alog.user_id,
                    alog.method,
                    alog.http_session_id,
                    alog.http_request_id,
                    alog.log_type
                FROM auditlog_log_line alogl
                JOIN auditlog_log alog ON alog.id = alogl.log_id
            )
            """,
            SQL.identifier(self._table),
        ))

    @api.model_create_multi
    def create(self, vals_list):
        raise UserError(_("Audit log details are read-only."))

    def write(self, vals):
        raise UserError(_("Audit log details are read-only."))

    def unlink(self):
        raise UserError(_("Audit log details are read-only."))
