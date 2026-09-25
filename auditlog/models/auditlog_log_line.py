from odoo import fields, models


class AuditlogLogLine(models.Model):
    _name = "auditlog.log.line"
    _description = "Auditlog - Log details (fields updated)"
    _order = "id desc"
    _rec_name = "field_description"

    field_id = fields.Many2one(
        "ir.model.fields", string="Field", ondelete="set null", index=True
    )
    log_id = fields.Many2one(
        "auditlog.log", string="Log", ondelete="cascade", index=True
    )
    old_value = fields.Text()
    new_value = fields.Text()
    old_value_text = fields.Text(string="Old value Text")
    new_value_text = fields.Text(string="New value Text")
    field_name = fields.Char(string="Technical name", readonly=True)
    field_description = fields.Char(string="Description", readonly=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="log_id.company_id",
        store=True,
        index=True,
    )
