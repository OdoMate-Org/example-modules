import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .common import LOG_TYPE_SELECTION


class AuditlogLog(models.Model):
    _name = "auditlog.log"
    _description = "Auditlog - Log"
    _order = "create_date desc, id desc"

    name = fields.Char(string="Resource Name")
    model_id = fields.Many2one(
        "ir.model", string="Model", index=True, ondelete="set null"
    )
    model_name = fields.Char(string="Model Name", readonly=True)
    model_model = fields.Char(string="Technical Model Name", readonly=True)
    res_id = fields.Integer(string="Resource ID", index=True)
    res_ids = fields.Text(
        string="Resource IDs",
        help="JSON list of the record ids covered by an export.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        help="Company of the audited record at log time, when its model has one.",
    )
    user_id = fields.Many2one("res.users", string="User", index=True)
    method = fields.Char()
    line_ids = fields.One2many("auditlog.log.line", "log_id", string="Fields updated")
    http_session_id = fields.Many2one(
        "auditlog.http.session", string="Session", index=True
    )
    http_request_id = fields.Many2one(
        "auditlog.http.request", string="HTTP Request", index=True
    )
    log_type = fields.Selection(LOG_TYPE_SELECTION, string="Type")
    exported_count = fields.Integer(
        string="Exported Records",
        compute="_compute_exported_count",
    )

    _model_res_idx = models.Index("(model_id, res_id)")

    def _get_res_id_list(self):
        self.ensure_one()
        if not self.res_ids:
            return []
        try:
            ids = json.loads(self.res_ids)
        except ValueError:
            return []
        if not isinstance(ids, list):
            return []
        return [i for i in ids if isinstance(i, int)]

    @api.depends("res_ids")
    def _compute_exported_count(self):
        for log in self:
            log.exported_count = len(log._get_res_id_list())

    def show_res_ids(self):
        self.ensure_one()
        if not self.model_id or not self.model_model:
            raise UserError(_("The audited model of this log no longer exists."))
        if self.model_model not in self.env:
            raise UserError(
                _("The model %(model)s is not installed anymore.", model=self.model_model)
            )
        return {
            "type": "ir.actions.act_window",
            "name": _("Exported Records"),
            "res_model": self.model_model,
            "view_mode": "list,form",
            "domain": [("id", "in", self._get_res_id_list())],
            "target": "current",
        }
