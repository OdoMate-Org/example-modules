from odoo import fields, models


class AuditLogLine(models.Model):
    _name = "audit.log.line"
    _description = "Audit Log Field Change"
    _order = "log_id desc, id"

    log_id = fields.Many2one(
        comodel_name="audit.log",
        string="Event",
        required=True,
        readonly=True,
        index=True,
        ondelete="cascade",
    )
    field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Field",
        readonly=True,
        ondelete="set null",
    )
    field_description = fields.Char(string="Field Label", readonly=True)
    old_value = fields.Text(
        readonly=True,
        help="Left blank when the watch rule records light detail only.",
    )
    new_value = fields.Text(readonly=True)

    company_id = fields.Many2one(
        comodel_name="res.company",
        related="log_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    date = fields.Datetime(related="log_id.date", string="Event Date", readonly=True)
    user_id = fields.Many2one(related="log_id.user_id", string="User", readonly=True)
    record_name = fields.Char(related="log_id.record_name", string="Record", readonly=True)
    res_model = fields.Char(
        related="log_id.res_model", string="Technical Model", readonly=True
    )
    action = fields.Selection(related="log_id.action", string="Action", readonly=True)
