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
            "auto_install",
        }
        for m in mods:
            self.assertEqual(set(m), expected_keys)

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

    def test_transient_models_excluded_and_fields_sorted(self):
        models = _build(_raw())["models"]
        self.assertEqual([m["model"] for m in models], ["sale.order"])
        self.assertEqual([f["name"] for f in models[0]["fields"]], ["name", "x_priority_score"])
        self.assertNotIn("transient", models[0])

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

    def test_passthrough_sections(self):
        raw = _raw()
        snap = _build(raw)
        self.assertEqual(snap["automations"], raw["automations"])
        self.assertEqual(snap["record_counts"], {"sale.order": 12840, "res.partner": 3211})

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

    def test_oversized_archs_dropped_first(self):
        raw = _raw()
        raw["views"][0]["arch"] = "<data>" + "x" * (6 * 1024 * 1024) + "</data>"
        payload, truncated = snapshot_lib.serialize(_build(raw))
        self.assertEqual(truncated, ["view_archs"])
        data = json.loads(payload)
        self.assertIsNone(data["views"][0]["arch"])
        self.assertEqual(data["views"][0]["inherit_id_xmlid"], "sale.view_order_form")
        self.assertLessEqual(len(payload.encode()), snapshot_lib.MAX_SNAPSHOT_BYTES)

    def test_standard_fields_dropped_second(self):
        raw = _raw()
        big_fields = [
            {
                "name": "field_%07d" % i,
                "ttype": "char",
                "selection": None,
                "relation": "some.very.long.relation.model.name",
                "required": False,
                "custom": False,
            }
            for i in range(60000)
        ]
        raw["models"].append(
            {"model": "res.partner", "custom": False, "transient": False, "fields": big_fields}
        )
        payload, truncated = snapshot_lib.serialize(_build(raw))
        self.assertEqual(truncated, ["view_archs", "standard_model_fields"])
        by_model = {m["model"]: m for m in json.loads(payload)["models"]}
        self.assertEqual(by_model["res.partner"]["fields"], [])
        self.assertEqual(len(by_model["sale.order"]["fields"]), 2)
        self.assertLessEqual(len(payload.encode()), snapshot_lib.MAX_SNAPSHOT_BYTES)

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
