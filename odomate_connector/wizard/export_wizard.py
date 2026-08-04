import base64
from datetime import datetime, timezone

from odoo import fields, models
from odoo.exceptions import AccessError

from .. import collector, snapshot_lib


class ContextExportWizard(models.TransientModel):
    _name = "odomate.context.export"
    _description = "Export OdoMate Context"

    state = fields.Selection([("draft", "Draft"), ("done", "Done")], default="draft", required=True)
    snapshot_file = fields.Binary(string="Snapshot", readonly=True, attachment=False)
    filename = fields.Char(readonly=True)
    summary = fields.Text(readonly=True)

    def action_generate(self):
        self.ensure_one()
        if not self.env.user.has_group("base.group_system"):
            raise AccessError("Only Settings administrators may export the OdoMate context.")
        raw = collector.collect(self.env)
        snapshot = snapshot_lib.build_snapshot(
            raw,
            connector_version=snapshot_lib.CONNECTOR_VERSION,
            generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        payload, truncated = snapshot_lib.serialize(snapshot)
        self.write(
            {
                "state": "done",
                "snapshot_file": base64.b64encode(payload.encode()),
                "filename": "odomate_context.json",
                "summary": self._summary_text(snapshot, truncated),
            }
        )
        return {
            "type": "ir.actions.act_window",
            # Without an explicit name the re-opened dialog is titled "Odoo".
            "name": "Export OdoMate Context",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    @staticmethod
    def _summary_text(snapshot, truncated):
        inst = snapshot["instance"]
        n_fields = sum(len(m["fields"]) for m in snapshot["models"])
        lines = [
            f"Odoo {inst['odoo_version']} ({inst['edition']})",
            f"{len(snapshot['modules'])} installed modules",
            f"{len(snapshot['models'])} models, {n_fields} fields",
            f"{len(snapshot['views'])} customized views",
            f"{len(snapshot['settings'])} settings, {len(snapshot['groups'])} security groups",
        ]
        if truncated:
            lines.append(f"Truncated to fit the 5 MB cap: {', '.join(truncated)}")
        lines.append("No business records, credentials or user data are included.")
        return "\n".join(lines)
