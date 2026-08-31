from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..models.audit_log import CLEANUP_CRON_XML_ID


class AuditConfig(models.TransientModel):
    _name = "audit.config"
    _description = "Audit Trail Clean-up Settings"

    cleanup_enabled = fields.Boolean(
        string="Enable Automatic Clean-up",
        default=False,
        help="While this is off, no event is ever deleted automatically.",
    )
    retention_days = fields.Integer(
        string="Keep Events For (days)",
        default=180,
    )
    batch_size = fields.Integer(
        string="Batch Size",
        default=1000,
        help="Number of events, sessions or screens deleted per run. The job "
             "re-triggers itself until nothing expired is left, so a large "
             "first clean-up never holds one long transaction open.",
    )

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        settings = self.env["audit.log"]._audit_cleanup_settings()
        if "cleanup_enabled" in fields_list:
            result["cleanup_enabled"] = settings["enabled"]
        if "retention_days" in fields_list:
            result["retention_days"] = settings["retention_days"]
        if "batch_size" in fields_list:
            result["batch_size"] = settings["batch_size"]
        return result

    @api.constrains("retention_days", "batch_size")
    def _check_positive_values(self):
        for config in self:
            if config.retention_days <= 0:
                raise ValidationError(_("The retention period must be at least one day."))
            if config.batch_size <= 0:
                raise ValidationError(_("The batch size must be at least one event."))

    def _sync_cleanup_cron(self):
        cron = self.env.ref(CLEANUP_CRON_XML_ID, raise_if_not_found=False)
        if cron:
            cron.sudo().active = self.cleanup_enabled

    def action_save(self):
        self.ensure_one()
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("audit_trail.cleanup_enabled", str(self.cleanup_enabled))
        params.set_param("audit_trail.retention_days", str(self.retention_days))
        params.set_param("audit_trail.batch_size", str(self.batch_size))
        self._sync_cleanup_cron()
        return {"type": "ir.actions.act_window_close"}

    def action_run_cleanup_now(self):
        self.ensure_one()
        self.action_save()
        self.env["audit.log"]._cron_cleanup_logs()
        return {"type": "ir.actions.act_window_close"}
