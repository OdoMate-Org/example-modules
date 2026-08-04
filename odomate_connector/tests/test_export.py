import base64
import json

from odoo.addons.odomate_connector import collector, snapshot_lib
from odoo.tests.common import TransactionCase, tagged

GENERATED_AT = "2026-01-01T00:00:00+00:00"


@tagged("post_install", "-at_install")
class TestContextExport(TransactionCase):
    def _snapshot(self):
        raw = collector.collect(self.env)
        return snapshot_lib.build_snapshot(
            raw, connector_version=snapshot_lib.CONNECTOR_VERSION, generated_at=GENERATED_AT
        )

    def _payload(self):
        payload, _ = snapshot_lib.serialize(self._snapshot())
        return payload

    def test_snapshot_has_all_sections(self):
        snap = self._snapshot()
        for key in (
            "schema_version",
            "connector_version",
            "generated_at",
            "instance",
            "modules",
            "models",
            "views",
            "settings",
            "config_params",
            "groups",
            "automations",
            "record_counts",
        ):
            self.assertIn(key, snap)
        self.assertEqual(snap["schema_version"], 1)
        names = {m["name"] for m in snap["modules"]}
        self.assertIn("base", names)
        self.assertIn("odomate_connector", names)
        self.assertIn("res.partner", {m["model"] for m in snap["models"]})

    def test_seeded_secret_param_never_exported(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "odomate_probe.api_secret", "SENTINEL_SECRET_93117"
        )
        self.assertNotIn("SENTINEL_SECRET_93117", self._payload())

    def test_business_records_never_exported(self):
        self.env["res.partner"].create(
            {"name": "Xyzzy Confidential GmbH", "email": "ceo@xyzzy-confidential.example"}
        )
        payload = self._payload()
        self.assertNotIn("Xyzzy Confidential", payload)
        self.assertNotIn("xyzzy-confidential.example", payload)

    def test_db_uuid_only_hashed(self):
        real_uuid = self.env["ir.config_parameter"].sudo().get_param("database.uuid")
        snap = self._snapshot()
        self.assertTrue(snap["instance"]["db_uuid_hash"].startswith("sha256:"))
        self.assertNotIn(real_uuid, self._payload())

    def test_custom_field_captured(self):
        self.env["ir.model.fields"].create(
            {
                "name": "x_odomate_probe_field",
                "model_id": self.env["ir.model"]._get_id("res.partner"),
                "ttype": "char",
                "field_description": "Probe",
            }
        )
        snap = self._snapshot()
        partner = next(m for m in snap["models"] if m["model"] == "res.partner")
        probe = next(f for f in partner["fields"] if f["name"] == "x_odomate_probe_field")
        self.assertTrue(probe["custom"])

    def test_settings_values_match_their_declared_type(self):
        """No None, and no int masquerading as a boolean.

        `is_installed_<module>` fields are declared boolean but resolve to the
        module's integer id — which differs between any two databases and would
        report a permanent false mismatch against a replica of the same
        environment. Observed on a real 95-module install.
        """
        settings = self.env["res.config.settings"]
        exported = self._snapshot()["settings"]
        self.assertTrue(exported, "expected some settings to be exported")
        for name, value in exported.items():
            self.assertIsNotNone(value, f"{name} exported as None")
            expected = bool if settings._fields[name].type == "boolean" else str
            self.assertTrue(
                value is False or isinstance(value, expected),
                f"{name}={value!r} ({type(value).__name__}) violates its declared type",
            )

    def test_installed_module_indicators_are_not_exported_as_ids(self):
        exported = self._snapshot()["settings"]
        offenders = {
            k: v for k, v in exported.items() if k.startswith("is_installed_") and v is not False
        }
        for name, value in offenders.items():
            self.assertIsInstance(value, bool, f"{name}={value!r} leaked a module id")

    def test_unanalyzed_tables_report_unknown_not_zero(self):
        """PostgreSQL 14+ uses reltuples = -1 for "never analyzed".

        Clamping that to 0 asserts a table holding real data is empty, which is
        worse than saying nothing: a consumer concludes the customer does no
        manufacturing, raises no purchase requests, and so on.
        """
        counts = self._snapshot()["record_counts"]
        self.assertTrue(counts, "expected some record counts")
        for model, value in counts.items():
            self.assertTrue(
                value is None or (isinstance(value, int) and value >= 0),
                f"{model}={value!r} is neither a count nor an explicit unknown",
            )
        # A freshly built DB has plenty of never-analyzed tables; if every single
        # one reported a number, the -1 sentinel would be being swallowed again.
        self.assertIn(None, counts.values(), "no table reported unknown — is -1 being clamped?")

    def test_company_related_settings_are_captured(self):
        """`default_get` does not resolve settings related through company_id.

        Those carry real policy (approval thresholds, lock behaviour), so the
        collector reads an instantiated record instead. This asserts the class is
        represented rather than naming one field, since which company-related
        settings exist depends on the installed modules.
        """
        settings = self.env["res.config.settings"]
        exported = self._snapshot()["settings"]
        company_related = {
            name
            for name, f in settings._fields.items()
            if f.type in ("boolean", "selection")
            and str(getattr(f, "related", "") or "").startswith("company_id")
        }
        if not company_related:
            self.skipTest("no company-related settings in this install")
        self.assertTrue(
            company_related & set(exported),
            f"none of {len(company_related)} company-related settings were exported",
        )

    def test_automation_conditions_referencing_records_are_masked(self):
        """The negative case, end to end against a real database.

        The unit tests cover the masking rules; this proves the whole path —
        a consultant writes a condition naming a customer, and the exported
        file does not contain that customer.
        """
        if "base.automation" not in self.env:
            self.skipTest("base_automation not installed")
        partner = self.env["res.partner"].create(
            {"name": "Wellness Holdings GmbH", "ref": "CUST-00042"}
        )
        model = self.env["ir.model"]._get("res.partner")
        action = self.env["ir.actions.server"].create(
            {"name": "probe", "model_id": model.id, "state": "code", "code": "pass"}
        )
        conditions = {
            "by_name": "[('name', '=', 'Wellness Holdings GmbH')]",
            "by_ref": "[('ref', 'ilike', 'CUST-00042')]",
            "by_id": "[('parent_id', '=', %d)]" % partner.id,
        }
        for label, domain in conditions.items():
            self.env["base.automation"].create(
                {
                    "name": "probe %s" % label,
                    "model_id": model.id,
                    "trigger": "on_write",
                    "filter_domain": domain,
                    "action_server_ids": [(6, 0, [action.id])],
                }
            )
        payload = self._payload()
        self.assertNotIn("Wellness Holdings GmbH", payload)
        self.assertNotIn("CUST-00042", payload)
        # A many2one comparison is a record reference, so the id must not survive.
        self.assertNotIn("'parent_id', '=', %d" % partner.id, payload)
        # The condition's shape is still there — that is the point of masking
        # rather than dropping.
        exported = {a["name"]: a["filter_domain"] for a in self._snapshot()["automations"]}
        self.assertIn("name", exported["probe by_name"])
        self.assertIn(snapshot_lib.REDACTED_VALUE, exported["probe by_name"])

    def test_transient_models_are_exported_and_flagged(self):
        models = {m["model"]: m for m in self._snapshot()["models"]}
        self.assertIn("res.config.settings", models)
        self.assertTrue(models["res.config.settings"]["transient"])
        self.assertFalse(models["res.partner"]["transient"])

    def test_record_counts_skip_transient_models(self):
        """Wizards persist nothing, so a row count for one is meaningless."""
        snap = self._snapshot()
        transient = {m["model"] for m in snap["models"] if m["transient"]}
        self.assertFalse(transient & set(snap["record_counts"]))

    def test_models_carry_owning_module(self):
        models = {m["model"]: m for m in self._snapshot()["models"]}
        self.assertEqual(models["res.partner"]["module"], "base")
        self.assertEqual(models["res.partner"]["xmlid"], "base.model_res_partner")

    def test_stored_computed_fields_are_distinguishable(self):
        """A stored-computed field cannot be written to, and an automation
        triggered on it never fires — both silent failures without these flags."""
        models = {m["model"]: m for m in self._snapshot()["models"]}
        fields = {f["name"]: f for f in models["res.partner"]["fields"]}
        for name, f in fields.items():
            self.assertIsInstance(f["store"], bool, name)
            self.assertIsInstance(f["computed"], bool, name)
        computed = [f for f in fields.values() if f["computed"]]
        self.assertTrue(computed, "expected res.partner to have computed fields")

    def test_db_created_view_captured(self):
        """A view created in the DB (no module xmlid) is a customization."""
        self.env["ir.ui.view"].create(
            {
                "name": "odomate probe view",
                "model": "res.partner",
                "type": "form",
                "inherit_id": self.env.ref("base.view_partner_form").id,
                "arch": (
                    '<xpath expr="//field[@name=\'name\']" position="after">'
                    '<field name="ref"/></xpath>'
                ),
            }
        )
        views = self._snapshot()["views"]
        match = [
            v
            for v in views
            if v["model"] == "res.partner" and v["inherit_id_xmlid"] == "base.view_partner_form"
        ]
        self.assertTrue(match, f"db-created view not captured; got {len(views)} views")
        self.assertTrue(match[0]["custom"])
        self.assertIn("xpath", match[0]["arch"])

    def test_module_view_edited_by_user_captured(self):
        """A module-shipped view whose arch the user edited is a customization.

        This is the arch_updated branch — the view keeps its module xmlid, so
        only the edited flag distinguishes it from stock.
        """
        view = self.env.ref("base.view_partner_form")
        # Any write touching arch flips arch_updated (ir_ui_view.write) — this
        # is what saving in the view editor does. Re-writing the SAME arch keeps
        # the XML valid while still marking the view as user-modified.
        view.write({"arch": view.arch})
        self.assertTrue(view.arch_updated, "writing arch should mark the view as updated")
        captured = {
            (v["model"], v["type"])
            for v in self._snapshot()["views"]
            if v["inherit_id_xmlid"] is None
        }
        self.assertIn(("res.partner", "form"), captured)

    def test_stock_views_not_reported_as_customized(self):
        """A pristine module view must NOT be reported — else every DB looks customized."""
        for v in self._snapshot()["views"]:
            self.assertNotEqual(
                (v["model"], v["inherit_id_xmlid"]),
                ("res.currency", None),
                "stock currency view reported as customized",
            )

    def test_wizard_generates_valid_download(self):
        wiz = self.env["odomate.context.export"].create({})
        wiz.action_generate()
        self.assertEqual(wiz.state, "done")
        self.assertEqual(wiz.filename, "odomate_context.json")
        data = json.loads(base64.b64decode(wiz.snapshot_file))
        self.assertEqual(data["schema_version"], 1)
        self.assertIn("truncated", data)
