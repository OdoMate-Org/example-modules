"""Pure-logic tests for snapshot_lib — no database, no Odoo environment.

snapshot_lib decides *what leaves the customer's database*, so it is written as
plain functions over plain dicts and can be tested without a registry or cursor.

These subclass ``BaseCase`` rather than ``unittest.TestCase`` deliberately:
Odoo's tag selector skips any test class with no ``test_tags`` attribute, and
it does so with a debug-level log and a passing run. Plain ``unittest.TestCase``
classes are therefore collected by nobody and silently never execute.
``BaseCase.__init_subclass__`` assigns ``{'standard', 'at_install'}``, while
``registry``/``cr``/``env`` stay ``None`` — so these still need no database.
"""

import ast
import json
from pathlib import Path

from odoo.addons.odomate_connector import snapshot_lib
from odoo.tests.common import BaseCase

FIXTURES = Path(__file__).resolve().parent / "fixtures"
GENERATED_AT = "2026-01-01T00:00:00+00:00"


def _raw():
    return json.loads((FIXTURES / "raw_small.json").read_text())


def _build(raw):
    return snapshot_lib.build_snapshot(
        raw, connector_version="1.0.0", generated_at=GENERATED_AT
    )


class TestSecretPattern(BaseCase):
    def test_matches_the_spec_patterns(self):
        for word in ("key", "secret", "token", "password", "api", "dkim", "private"):
            self.assertTrue(snapshot_lib.SECRET_RE.search("some.%s.thing" % word), word)
            self.assertTrue(
                snapshot_lib.SECRET_RE.search("SOME.%s.THING" % word.upper()), word
            )

    def test_does_not_match_benign_names(self):
        for benign in (
            "group_discount_per_so_line",
            "auth_signup_uninvited",
            "mail.catchall.alias",
        ):
            self.assertIsNone(snapshot_lib.SECRET_RE.search(benign), benign)


class TestRedactParams(BaseCase):
    ALLOW = frozenset({"auth_signup.invitation_scope", "base_setup.default_user_rights"})

    def test_allowlist_first(self):
        params = {
            "auth_signup.invitation_scope": "b2b",
            "database.secret": "s3cr3t",
            "some.random.param": "x",
        }
        self.assertEqual(
            snapshot_lib.redact_params(params, self.ALLOW),
            {"auth_signup.invitation_scope": "b2b"},
        )

    def test_secret_key_dropped_even_if_allowlisted(self):
        allow = frozenset({"mail.dkim.selector"})
        self.assertEqual(snapshot_lib.redact_params({"mail.dkim.selector": "v1"}, allow), {})

    def test_secret_value_dropped_even_if_allowlisted(self):
        allow = frozenset({"harmless.flag"})
        self.assertEqual(
            snapshot_lib.redact_params({"harmless.flag": "my_api_token=abc"}, allow), {}
        )

    def test_none_values_survive(self):
        allow = frozenset({"harmless.flag"})
        self.assertEqual(
            snapshot_lib.redact_params({"harmless.flag": None}, allow),
            {"harmless.flag": None},
        )


class TestMaskDomain(BaseCase):
    """An automation condition may reference a record by name.

    The wizard and the Apps Store page both promise no names and no business
    records, so a condition's *shape* is exported while values that could be
    data are not.
    """

    FIELDS = {
        "state": {"ttype": "selection", "selection": [["draft", "Draft"], ["done", "Done"]]},
        "name": {"ttype": "char", "selection": None},
        "sequence": {"ttype": "integer", "selection": None},
        "active": {"ttype": "boolean", "selection": None},
    }

    def test_selection_value_is_schema_and_survives(self):
        self.assertEqual(
            snapshot_lib.mask_domain("[('state', '=', 'done')]", self.FIELDS),
            repr([("state", "=", "done")]),
        )

    def test_customer_name_is_redacted(self):
        masked = snapshot_lib.mask_domain(
            "[('partner_id.name', '=', 'Acme GmbH')]", self.FIELDS
        )
        self.assertNotIn("Acme GmbH", masked)
        self.assertIn("partner_id.name", masked)
        self.assertIn(snapshot_lib.REDACTED_VALUE, masked)

    def test_free_text_on_own_model_is_redacted(self):
        masked = snapshot_lib.mask_domain("[('name', 'ilike', 'Wellness Ltd')]", self.FIELDS)
        self.assertNotIn("Wellness Ltd", masked)

    def test_value_outside_the_declared_selection_is_redacted(self):
        """A selection field compared to something not in its schema is data."""
        masked = snapshot_lib.mask_domain("[('state', '=', 'Acme')]", self.FIELDS)
        self.assertNotIn("Acme", masked)

    def test_numeric_and_boolean_survive(self):
        self.assertIn("5", snapshot_lib.mask_domain("[('sequence', '>', 5)]", self.FIELDS))
        self.assertIn("True", snapshot_lib.mask_domain("[('active', '=', True)]", self.FIELDS))

    def test_structural_tokens_survive(self):
        masked = snapshot_lib.mask_domain(
            "['|', ('state', '=', 'done'), ('name', '=', 'Acme')]", self.FIELDS
        )
        self.assertIn("'|'", masked)
        self.assertNotIn("Acme", masked)

    def test_unparseable_domain_fails_closed(self):
        self.assertIsNone(snapshot_lib.mask_domain("[('state', '=', foo)]", self.FIELDS))
        self.assertIsNone(snapshot_lib.mask_domain("not a domain at all", self.FIELDS))

    def test_unknown_field_is_redacted(self):
        masked = snapshot_lib.mask_domain("[('x_secret', '=', 'Acme')]", self.FIELDS)
        self.assertNotIn("Acme", masked)


class TestConfigParamAllowlist(BaseCase):
    def test_no_entry_is_killed_by_the_redactor(self):
        """An allowlisted key matching SECRET_RE can never survive redaction.

        Such an entry reads as "we export this" while the redactor always drops
        it — a trap for whoever maintains the allowlist next.
        """
        dead = {
            k for k in snapshot_lib.CONFIG_PARAM_ALLOWLIST if snapshot_lib.SECRET_RE.search(k)
        }
        self.assertEqual(dead, set())


class TestRedactSettings(BaseCase):
    def test_secret_named_settings_dropped(self):
        settings = {
            "group_discount_per_so_line": True,
            "unsplash_access_key_set": True,
            "auth_signup_uninvited": "b2b",
        }
        self.assertEqual(
            snapshot_lib.redact_settings(settings),
            {"group_discount_per_so_line": True, "auth_signup_uninvited": "b2b"},
        )


class TestHashDbUuid(BaseCase):
    def test_sha256_prefixed_and_stable(self):
        h = snapshot_lib.hash_db_uuid("11111111-2222-3333-4444-555555555555")
        self.assertEqual(h, snapshot_lib.hash_db_uuid("11111111-2222-3333-4444-555555555555"))
        self.assertTrue(h.startswith("sha256:"))
        self.assertEqual(len(h), len("sha256:") + 64)
        self.assertNotIn("11111111-2222", h)


class TestClassifyModuleSource(BaseCase):
    CASES = [
        ("Odoo S.A.", "https://www.odoo.com", "LGPL-3", "core"),
        ("Odoo S.A.", "https://www.odoo.com", "OEEL-1", "enterprise"),
        ("Odoo S.A.", "https://www.odoo.com", "OPL-1", "enterprise"),
        (
            "Camptocamp, Odoo Community Association (OCA)",
            "https://github.com/OCA/queue",
            "AGPL-3",
            "oca",
        ),
        ("ACME Consulting", "https://acme.example", "LGPL-3", "thirdparty"),
        ("", "", "LGPL-3", "custom"),
        (None, None, None, "custom"),
    ]

    def test_sources(self):
        for author, website, license_, expected in self.CASES:
            with self.subTest(author=author, license=license_):
                self.assertEqual(
                    snapshot_lib.classify_module_source(author, website, license_), expected
                )

    def test_filesystem_location_outranks_the_manifest(self):
        """l10n_ua ships inside core Odoo but declares a third-party author.

        Trusting the manifest sent a replica builder hunting for a module that
        was already in the distribution.
        """
        self.assertEqual(
            snapshot_lib.classify_module_source(
                "ERP Ukraine (https://erp.co.ua)", "https://erp.co.ua", "LGPL-3", location="core"
            ),
            "core",
        )

    def test_imported_modules_are_unobtainable(self):
        """base_import_module uploads live only in that database."""
        self.assertEqual(
            snapshot_lib.classify_module_source(
                "ACME", "https://acme.example", "LGPL-3", location=None, imported=True
            ),
            "custom",
        )

    def test_external_module_without_any_identity_is_custom(self):
        self.assertEqual(
            snapshot_lib.classify_module_source("", "", "LGPL-3", location="external"), "custom"
        )

    def test_oca_still_wins_over_plain_external(self):
        self.assertEqual(
            snapshot_lib.classify_module_source(
                "ACSONE SA/NV, Odoo Community Association (OCA)",
                "https://github.com/OCA/server-ux",
                "AGPL-3",
                location="external",
            ),
            "oca",
        )

    def test_enterprise_licence_outranks_location(self):
        self.assertEqual(
            snapshot_lib.classify_module_source(
                "Odoo S.A.", "https://www.odoo.com", "OEEL-1", location="core"
            ),
            "enterprise",
        )


class TestBuildSnapshot(BaseCase):
    def test_meta_fields(self):
        snap = _build(_raw())
        self.assertEqual(snap["schema_version"], 1)
        self.assertEqual(snap["connector_version"], "1.0.0")
        self.assertEqual(snap["generated_at"], GENERATED_AT)

    def test_instance_edition_and_uuid_hash(self):
        inst = _build(_raw())["instance"]
        self.assertEqual(inst["edition"], "community")
        self.assertTrue(inst["db_uuid_hash"].startswith("sha256:"))
        self.assertNotIn("db_uuid", inst)
        self.assertEqual(inst["languages"], ["en_US", "uk_UA"])

    def test_enterprise_edition_detected(self):
        raw = _raw()
        raw["modules"][0]["license"] = "OEEL-1"
        self.assertEqual(_build(raw)["instance"]["edition"], "enterprise")

    def test_modules_classified_and_sorted(self):
        mods = _build(_raw())["modules"]
        self.assertEqual(
            [m["name"] for m in mods], ["base", "queue_job", "sale", "x_custom_margin"]
        )
        self.assertEqual(
            {m["name"]: m["source"] for m in mods},
            {"base": "core", "queue_job": "oca", "sale": "core", "x_custom_margin": "custom"},
        )
        expected_keys = {
            "name",
            "installed_version",
            "published_version",
            "source",
            "author",
            "website",
            "url",
            "license",
            "addons_root",
            "auto_install",
        }
        for m in mods:
            self.assertEqual(set(m), expected_keys)

    def test_addons_root_separates_a_sites_own_code_from_a_vendors(self):
        """`source` calls both 'external'; only the addons directory tells them
        apart, and only when the deployment keeps them in separate paths."""
        mods = {m["name"]: m for m in _build(_raw())["modules"]}
        self.assertEqual(mods["queue_job"]["addons_root"], "oca-addons")
        self.assertEqual(mods["x_custom_margin"]["addons_root"], "client-addons")
        self.assertEqual(mods["base"]["addons_root"], "addons")
        # Grouping is the point: two roots here, so the two are distinguishable.
        external = {
            m["addons_root"] for m in mods.values() if m["addons_root"] != "addons"
        }
        self.assertEqual(external, {"oca-addons", "client-addons"})

    def test_module_source_location_survives(self):
        """OCA puts the repository in `website` — without it a replica cannot
        fetch the module back, which is the whole point of keeping the field."""
        mods = {m["name"]: m for m in _build(_raw())["modules"]}
        self.assertEqual(mods["queue_job"]["website"], "https://github.com/OCA/queue")
        self.assertEqual(mods["queue_job"]["source"], "oca")
        self.assertEqual(mods["queue_job"]["license"], "LGPL-3")

    def test_store_provenance_is_carried(self):
        """published_version is the only signal a module came from the Apps
        Store rather than a repository."""
        mods = {m["name"]: m for m in _build(_raw())["modules"]}
        self.assertEqual(mods["sale"]["published_version"], "19.0.1.2")
        self.assertEqual(mods["base"]["published_version"], "")

    def test_transient_models_included_but_flagged(self):
        """Wizards are a public API surface — often the only supported way to
        perform an OCA operation — so they are exported, flagged rather than
        dropped."""
        models = {m["model"]: m for m in _build(_raw())["models"]}
        self.assertIn("sale.advance.payment.inv", models)
        self.assertTrue(models["sale.advance.payment.inv"]["transient"])
        self.assertFalse(models["sale.order"]["transient"])

    def test_fields_sorted(self):
        models = {m["model"]: m for m in _build(_raw())["models"]}
        self.assertEqual(
            [f["name"] for f in models["sale.order"]["fields"]], ["name", "x_priority_score"]
        )

    def test_models_carry_their_owning_module(self):
        """`ref=` to another module's model xmlid is otherwise a guess, and
        `depends` cannot be derived from the models a module touches."""
        models = {m["model"]: m for m in _build(_raw())["models"]}
        self.assertEqual(models["sale.order"]["module"], "sale")
        self.assertEqual(models["sale.order"]["xmlid"], "sale.model_sale_order")

    def test_views_marked_custom(self):
        views = _build(_raw())["views"]
        self.assertTrue(views[0]["custom"])
        self.assertEqual(views[0]["inherit_id_xmlid"], "sale.view_order_form")

    def test_settings_and_params_redacted(self):
        snap = _build(_raw())
        self.assertNotIn("unsplash_access_key_set", snap["settings"])
        self.assertEqual(snap["config_params"], {"auth_signup.invitation_scope": "b2b"})
        self.assertNotIn("SHOULD_NEVER_APPEAR", json.dumps(snap))

    def test_groups_custom_flag_and_order(self):
        groups = _build(_raw())["groups"]
        self.assertEqual(groups[0]["xmlid"], "sales_team.group_sale_manager")
        self.assertFalse(groups[0]["custom"])
        self.assertEqual(
            groups[-1],
            {"xmlid": None, "name": "Custom Approvers", "custom": True, "users_count": 2},
        )

    def test_record_counts_pass_through(self):
        self.assertEqual(
            _build(_raw())["record_counts"], {"sale.order": 12840, "res.partner": 3211}
        )

    def test_automation_identity_passes_through_but_condition_is_masked(self):
        raw = _raw()
        snap = _build(raw)
        before, after = raw["automations"][0], snap["automations"][0]
        for key in ("name", "model", "trigger", "active"):
            self.assertEqual(after[key], before[key])
        self.assertNotEqual(after["filter_domain"], before["filter_domain"])
        self.assertNotIn("Wellness Ltd", json.dumps(snap))

    def test_input_not_mutated(self):
        raw = _raw()
        before = json.dumps(raw, sort_keys=True)
        _build(raw)
        self.assertEqual(json.dumps(raw, sort_keys=True), before)


class TestSerialize(BaseCase):
    def test_small_snapshot_untruncated(self):
        payload, truncated = snapshot_lib.serialize(_build(_raw()))
        self.assertEqual(truncated, [])
        data = json.loads(payload)
        self.assertEqual(data["truncated"], [])
        self.assertEqual(data["schema_version"], 1)

    @staticmethod
    def _bulk_fields(n, prefix="f"):
        # A long relation inflates bytes per field, so the cap is reached with
        # far fewer dicts and the test stays fast.
        padding = "some.very.long.relation.model.name" * 15
        return [
            {
                "name": "%s_%07d" % (prefix, i),
                "ttype": "char",
                "selection": None,
                "relation": padding,
                "required": False,
                "readonly": False,
                "store": True,
                "computed": False,
                "related": None,
                "custom": False,
            }
            for i in range(n)
        ]

    def _oversized_raw(self):
        """Over the cap, and still over it after the core stage.

        Sized so both field stages must run while the unobtainable module and
        the view arch stay comfortably affordable — that is the ordering the
        strategy is meant to guarantee.
        """
        raw = _raw()
        for model, module, count in (
            ("res.partner", "base", 12000),
            ("queue.job", "queue_job", 40000),
            ("acme.secret", "acme_bespoke", 500),
        ):
            raw["models"].append(
                {
                    "model": model,
                    "custom": False,
                    "transient": False,
                    "module": module,
                    "xmlid": "%s.model_%s" % (module, model.replace(".", "_")),
                    "fields": self._bulk_fields(count, model.split(".")[0]),
                }
            )
        raw["modules"].append(
            {
                "name": "acme_bespoke",
                "installed_version": "19.0.1.0.0",
                "published_version": "",
                "author": "ACME",
                "website": "https://acme.example",
                "url": "",
                "license": "LGPL-3",
                "auto_install": False,
                "location": "external",
            }
        )
        return raw

    def test_degrades_in_re_derivability_order(self):
        """Core fields first, then OCA fields — and the genuinely lossy view
        arch survives both, because it exists nowhere else."""
        payload, truncated = snapshot_lib.serialize(_build(self._oversized_raw()))
        self.assertEqual(truncated, ["core_model_fields", "fetchable_model_fields"])
        data = json.loads(payload)
        by_model = {m["model"]: m for m in data["models"]}
        self.assertEqual(by_model["res.partner"]["fields"], [], "core fields should go first")
        self.assertEqual(by_model["queue.job"]["fields"], [], "OCA fields should go second")
        self.assertIsNotNone(data["views"][0]["arch"], "view arch dropped before cheaper content")
        self.assertLessEqual(len(payload.encode()), snapshot_lib.MAX_SNAPSHOT_BYTES)

    def test_unobtainable_module_fields_are_never_dropped(self):
        """A module we cannot fetch has no other source of truth for its schema."""
        payload, _ = snapshot_lib.serialize(_build(self._oversized_raw()))
        by_model = {m["model"]: m for m in json.loads(payload)["models"]}
        self.assertTrue(by_model["acme.secret"]["fields"], "bespoke module schema was discarded")

    def test_customized_fields_survive_every_stage(self):
        payload, _ = snapshot_lib.serialize(_build(self._oversized_raw()))
        by_model = {m["model"]: m for m in json.loads(payload)["models"]}
        names = [f["name"] for f in by_model["sale.order"]["fields"]]
        self.assertIn("x_priority_score", names)

    def test_deterministic(self):
        a, _ = snapshot_lib.serialize(_build(_raw()))
        b, _ = snapshot_lib.serialize(_build(_raw()))
        self.assertEqual(a, b)


class TestGoldenSnapshot(BaseCase):
    def test_matches_blessed_output(self):
        """Full-output comparison — catches ANY unintended shape or content drift."""
        golden = json.loads((FIXTURES / "golden_small.json").read_text())
        self.assertEqual(_build(_raw()), golden)


class TestSchemaContract(BaseCase):
    """The published schema is the contract consumers build against.

    Validated structurally with stdlib only — the module ships no third-party
    dependencies, so there is no jsonschema here.
    """

    def setUp(self):
        schema_path = (
            Path(__file__).resolve().parents[1] / "schema" / "odomate_context.schema.json"
        )
        self.schema = json.loads(schema_path.read_text())

    def test_every_required_top_level_key_is_produced(self):
        payload, _ = snapshot_lib.serialize(_build(_raw()))
        produced = set(json.loads(payload))
        missing = set(self.schema["required"]) - produced
        self.assertEqual(missing, set())

    def test_schema_declares_the_current_version(self):
        self.assertEqual(self.schema["properties"]["schema_version"]["const"], 1)
        self.assertEqual(snapshot_lib.SCHEMA_VERSION, 1)


class TestManifest(BaseCase):
    def setUp(self):
        manifest_path = Path(__file__).resolve().parents[1] / "__manifest__.py"
        self.manifest = ast.literal_eval(manifest_path.read_text())

    def test_version_carries_the_connector_version(self):
        """'19.0.1.0.0' must end in CONNECTOR_VERSION — the snapshot reports it."""
        self.assertEqual(
            self.manifest["version"].split(".", 2)[2], snapshot_lib.CONNECTOR_VERSION
        )

    def test_version_starts_with_the_odoo_series(self):
        """The Apps Store rejects versions that do not start with the series."""
        self.assertTrue(self.manifest["version"].startswith("19.0."), self.manifest["version"])

    def test_license_is_lgpl3(self):
        self.assertEqual(self.manifest["license"], "LGPL-3")

    def test_declared_data_files_exist(self):
        module_dir = Path(__file__).resolve().parents[1]
        for rel in self.manifest["data"]:
            self.assertTrue((module_dir / rel).is_file(), rel)
