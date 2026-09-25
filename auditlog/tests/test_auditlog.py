import json
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestAuditlogCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Rule = cls.env["auditlog.rule"]
        cls.Log = cls.env["auditlog.log"]
        cls.Category = cls.env["res.partner.category"]
        cls.category_model = cls.env["ir.model"]._get("res.partner.category")
        cls.sequence_model = cls.env["ir.model"]._get("ir.sequence")
        cls.main_company = cls.env.ref("base.main_company")
        cls.company2 = cls.env["res.company"].create({"name": "Audit Test Company B"})
        cls.group_user = cls.env.ref("auditlog.group_auditlog_user")
        cls.group_manager = cls.env.ref("auditlog.group_auditlog_manager")
        cls.other_user = cls.env["res.users"].create({
            "name": "Audit Integration Bot",
            "login": "audit_integration_bot",
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id, cls.env.ref("base.group_partner_manager").id])],
        })
        cls.auditor = cls.env["res.users"].create({
            "name": "Audit Reader Main Company",
            "login": "audit_reader_main",
            "company_id": cls.main_company.id,
            "company_ids": [(6, 0, [cls.main_company.id])],
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id, cls.group_user.id])],
        })

    def _make_rule(self, ir_model, confirm=True, **vals):
        values = {"name": f"Audit {ir_model.model}", "model_id": ir_model.id}
        values.update(vals)
        rule = self.Rule.create(values)
        self.addCleanup(rule._revert_methods)
        if confirm:
            rule.set_to_confirmed()
        return rule

    def _logs(self, ir_model, method, res_id=None):
        domain = [("model_id", "=", ir_model.id), ("method", "=", method)]
        if res_id is not None:
            domain.append(("res_id", "=", res_id))
        return self.Log.search(domain)


@tagged("post_install", "-at_install")
class TestAuditlogRuleLifecycle(TestAuditlogCommon):

    def test_unique_model_constraint(self):
        self._make_rule(self.category_model, confirm=False)
        with self.assertRaises(Exception), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.Rule.create({"name": "Duplicate", "model_id": self.category_model.id})
            self.Rule.flush_model()

    def test_auditlog_models_cannot_be_audited(self):
        log_model = self.env["ir.model"]._get("auditlog.log")
        with self.assertRaises(ValidationError):
            self.Rule.create({"name": "Recursive", "model_id": log_model.id})

    def test_model_names_denormalized(self):
        rule = self._make_rule(self.category_model, confirm=False)
        self.assertEqual(rule.model_model, "res.partner.category")
        self.assertEqual(rule.model_name, self.category_model.name)

    def test_confirm_is_idempotent(self):
        rule = self._make_rule(self.category_model)
        action = rule.action_id
        self.assertTrue(action)
        self.assertEqual(action.binding_model_id, self.category_model)
        rule.set_to_confirmed()
        self.assertEqual(rule.action_id, action)
        count = self.env["ir.actions.act_window"].search_count([
            ("res_model", "=", "auditlog.log"),
            ("binding_model_id", "=", self.category_model.id),
        ])
        self.assertEqual(count, 1)

    def test_draft_reverts_patches(self):
        rule = self._make_rule(self.category_model)
        self.assertTrue(getattr(type(self.Category), "auditlog_ruled_create", False))
        rule.set_to_draft()
        self.assertFalse(getattr(type(self.Category), "auditlog_ruled_create", False))
        self.assertFalse(rule.action_id.binding_model_id)
        category = self.Category.create({"name": "Not audited"})
        self.assertFalse(self._logs(self.category_model, "create", category.id))

    def test_flag_change_repatches(self):
        rule = self._make_rule(self.category_model)
        rule.write({"log_create": False})
        category = self.Category.create({"name": "No create log"})
        self.assertFalse(self._logs(self.category_model, "create", category.id))
        self.assertFalse(getattr(type(self.Category), "auditlog_ruled_create", False))
        rule.write({"log_create": True})
        category = self.Category.create({"name": "Create log again"})
        self.assertEqual(len(self._logs(self.category_model, "create", category.id)), 1)

    def test_unlink_rule_reverts_patches(self):
        rule = self._make_rule(self.category_model)
        rule.unlink()
        self.assertFalse(getattr(type(self.Category), "auditlog_ruled_write", False))


@tagged("post_install", "-at_install")
class TestAuditlogLogging(TestAuditlogCommon):

    def test_create_full_logs_lines(self):
        self._make_rule(self.category_model)
        category = self.Category.create({"name": "Premium"})
        log = self._logs(self.category_model, "create", category.id)
        self.assertEqual(len(log), 1)
        self.assertEqual(log.log_type, "full")
        self.assertEqual(log.name, "Premium")
        self.assertEqual(log.model_model, "res.partner.category")
        self.assertFalse(log.company_id)
        line = log.line_ids.filtered(lambda l: l.field_name == "name")
        self.assertEqual(line.new_value_text, "Premium")
        self.assertTrue(line.field_description)

    def test_batch_create_one_log_per_record(self):
        self._make_rule(self.category_model)
        categories = self.Category.create([{"name": "Batch A"}, {"name": "Batch B"}, {"name": "Batch C"}])
        logs = self.Log.search([("model_id", "=", self.category_model.id), ("res_id", "in", categories.ids)])
        self.assertEqual(len(logs), 3)
        self.assertEqual(set(logs.mapped("name")), {"Batch A", "Batch B", "Batch C"})

    def test_write_full_old_and_new(self):
        self._make_rule(self.category_model)
        category = self.Category.create({"name": "Before"})
        category.write({"name": "After"})
        log = self._logs(self.category_model, "write", category.id)
        self.assertEqual(len(log), 1)
        line = log.line_ids.filtered(lambda l: l.field_name == "name")
        self.assertEqual(line.old_value_text, "Before")
        self.assertEqual(line.new_value_text, "After")

    def test_write_x2many_logs_names(self):
        self._make_rule(self.category_model)
        child = self.Category.create({"name": "Child Tag"})
        parent = self.Category.create({"name": "Parent Tag"})
        parent.write({"child_ids": [(4, child.id)]})
        log = self._logs(self.category_model, "write", parent.id)
        line = log.line_ids.filtered(lambda l: l.field_name == "child_ids")
        self.assertTrue(line)
        self.assertIn("Child Tag", line.new_value_text)

    def test_excluded_field_produces_no_line(self):
        name_field = self.env["ir.model.fields"]._get("res.partner.category", "name")
        self._make_rule(self.category_model, fields_to_exclude_ids=[(6, 0, name_field.ids)])
        category = self.Category.create({"name": "Hidden", "color": 1})
        category.write({"name": "Still hidden"})
        log = self._logs(self.category_model, "write", category.id)
        self.assertFalse(log.line_ids.filtered(lambda l: l.field_name == "name"))

    def test_unlink_without_capture(self):
        self._make_rule(self.category_model, capture_record=False)
        category = self.Category.create({"name": "To delete"})
        res_id = category.id
        category.unlink()
        log = self._logs(self.category_model, "unlink", res_id)
        self.assertEqual(len(log), 1)
        self.assertFalse(log.line_ids)
        self.assertEqual(log.name, "To delete")

    def test_unlink_with_capture(self):
        self._make_rule(self.category_model, capture_record=True)
        category = self.Category.create({"name": "Captured"})
        res_id = category.id
        category.unlink()
        log = self._logs(self.category_model, "unlink", res_id)
        line = log.line_ids.filtered(lambda l: l.field_name == "name")
        self.assertEqual(line.old_value_text, "Captured")

    def test_capture_record_read_live(self):
        rule = self._make_rule(self.category_model, capture_record=False)
        rule.write({"capture_record": True})
        category = self.Category.create({"name": "Live config"})
        res_id = category.id
        category.unlink()
        log = self._logs(self.category_model, "unlink", res_id)
        self.assertTrue(log.line_ids.filtered(lambda l: l.field_name == "name"))

    def test_excluded_user_is_not_logged(self):
        self._make_rule(self.category_model, users_to_exclude_ids=[(6, 0, self.other_user.ids)])
        category = self.Category.with_user(self.other_user).sudo().create({"name": "Integration"})
        self.assertFalse(self._logs(self.category_model, "create", category.id))
        category.with_user(self.other_user).sudo().write({"name": "Integration 2"})
        self.assertFalse(self._logs(self.category_model, "write", category.id))
        self.Category.browse(category.id).write({"name": "By admin"})
        self.assertTrue(self._logs(self.category_model, "write", category.id))

    def test_exclusion_added_on_confirmed_rule(self):
        rule = self._make_rule(self.category_model)
        rule.write({"users_to_exclude_ids": [(4, self.other_user.id)]})
        category = self.Category.with_user(self.other_user).sudo().create({"name": "Late exclusion"})
        self.assertFalse(self._logs(self.category_model, "create", category.id))

    def test_fast_log(self):
        self._make_rule(self.category_model, log_type="fast")
        category = self.Category.create({"name": "Fast"})
        log = self._logs(self.category_model, "create", category.id)
        self.assertEqual(log.log_type, "fast")
        self.assertEqual(log.line_ids.filtered(lambda l: l.field_name == "name").new_value_text, "Fast")
        category.write({"name": "Faster"})
        log = self._logs(self.category_model, "write", category.id)
        self.assertEqual(log.line_ids.filtered(lambda l: l.field_name == "name").new_value_text, "Faster")

    def test_snapshot_does_not_mutate_vals(self):
        parent = self.Category.create({"name": "Parent"})
        vals_list = [{"name": "Kid", "parent_id": parent}]
        snapshot = self.Rule._update_vals_list(vals_list)
        self.assertEqual(snapshot[0]["parent_id"], parent.ids)
        self.assertIs(vals_list[0]["parent_id"], parent)

    def test_read_logging(self):
        self._make_rule(self.category_model, log_read=True)
        category = self.Category.create({"name": "Readable"})
        category.read(["name"])
        self.assertTrue(self._logs(self.category_model, "read", category.id))

    def test_export_logs_json_and_no_read_flood(self):
        self._make_rule(self.category_model, log_read=True, log_export_data=True)
        categories = self.Category.create([{"name": f"Export {i}"} for i in range(5)])
        reads_before = self.Log.search_count([("model_id", "=", self.category_model.id), ("method", "=", "read")])
        categories.export_data(["name"])
        log = self._logs(self.category_model, "export_data")
        self.assertEqual(len(log), 1)
        self.assertEqual(sorted(json.loads(log.res_ids)), sorted(categories.ids))
        self.assertEqual(log.exported_count, 5)
        reads_after = self.Log.search_count([("model_id", "=", self.category_model.id), ("method", "=", "read")])
        self.assertEqual(reads_before, reads_after)
        action = log.show_res_ids()
        self.assertEqual(action["res_model"], "res.partner.category")
        self.assertEqual(sorted(action["domain"][0][2]), sorted(categories.ids))

    def test_show_res_ids_without_model(self):
        log = self.Log.create({"name": "Orphan", "method": "export_data", "res_ids": json.dumps([1])})
        with self.assertRaises(UserError):
            log.show_res_ids()

    def test_failure_policy_block(self):
        self._make_rule(self.category_model, log_failure_policy="block")
        with patch.object(type(self.Log), "create", side_effect=RuntimeError("log store down")):
            with self.assertRaises(RuntimeError):
                self.Category.create({"name": "Blocked"})

    def test_failure_policy_skip(self):
        self._make_rule(self.category_model, log_failure_policy="skip")
        with patch.object(type(self.Log), "create", side_effect=RuntimeError("log store down")), \
                mute_logger("odoo.addons.auditlog.models.auditlog_rule"):
            category = self.Category.create({"name": "Skipped log"})
        self.assertTrue(category.exists())
        self.assertFalse(self._logs(self.category_model, "create", category.id))

    def test_missing_model_cache_is_graceful(self):
        self._make_rule(self.category_model)
        cache = self.env.registry._auditlog_model_cache
        saved = cache.pop("res.partner.category")
        self.addCleanup(cache.__setitem__, "res.partner.category", saved)
        with mute_logger("odoo.addons.auditlog.models.auditlog_rule"):
            category = self.Category.create({"name": "No cache"})
        self.assertTrue(category.exists())
        self.assertFalse(self._logs(self.category_model, "create", category.id))


@tagged("post_install", "-at_install")
class TestAuditlogMultiCompany(TestAuditlogCommon):

    def test_company_denormalized_from_record(self):
        self._make_rule(self.sequence_model)
        sequence = self.env["ir.sequence"].create({
            "name": "Audit seq B",
            "company_id": self.company2.id,
        })
        log = self._logs(self.sequence_model, "create", sequence.id)
        self.assertEqual(log.company_id, self.company2)
        self.assertTrue(log.line_ids)
        self.assertEqual(set(log.line_ids.mapped("company_id").ids), {self.company2.id})

    def test_company_record_rules(self):
        log_a = self.Log.create({"name": "Main", "method": "write", "company_id": self.main_company.id,
                                 "line_ids": [(0, 0, {"field_name": "name", "old_value_text": "x"})]})
        log_b = self.Log.create({"name": "Other", "method": "write", "company_id": self.company2.id,
                                 "line_ids": [(0, 0, {"field_name": "name", "old_value_text": "y"})]})
        log_none = self.Log.create({"name": "Global", "method": "write"})
        visible = self.Log.with_user(self.auditor).search([("id", "in", (log_a | log_b | log_none).ids)])
        self.assertEqual(visible, log_a | log_none)
        lines = self.env["auditlog.log.line"].with_user(self.auditor).search(
            [("log_id", "in", (log_a | log_b).ids)])
        self.assertEqual(lines, log_a.line_ids)

    def test_log_line_view_is_read_only(self):
        View = self.env["auditlog.log.line.view"]
        with self.assertRaises(UserError):
            View.create({"field_name": "name"})
        log = self.Log.create({"name": "V", "method": "write", "company_id": self.company2.id,
                               "line_ids": [(0, 0, {"field_name": "name", "new_value_text": "v"})]})
        self.env.flush_all()
        row = View.search([("log_id", "=", log.id)])
        self.assertEqual(len(row), 1)
        self.assertEqual(row.company_id, self.company2)
        with self.assertRaises(UserError):
            row.write({"new_value_text": "tampered"})
        with self.assertRaises(UserError):
            row.unlink()

    def test_autovacuum(self):
        log = self.Log.create({"name": "Old", "method": "write"})
        self.env.flush_all()
        self.env["auditlog.autovacuum"].autovacuum(0)
        self.assertFalse(log.exists())


@tagged("post_install", "-at_install")
class TestAuditlogCrudAndDemo(TestAuditlogCommon):

    def test_demo_data_loaded(self):
        demo_rule = self.env.ref("auditlog.demo_rule_res_partner", raise_if_not_found=False)
        if not demo_rule:
            self.skipTest("demo data not loaded")
        self.assertEqual(demo_rule.state, "confirmed")
        self.assertTrue(demo_rule.action_id)
        self.assertGreaterEqual(self.Log.search_count([("model_model", "=", "res.partner")]), 20)
        export_log = self.env.ref("auditlog.demo_log_export_main_contacts")
        self.assertEqual(export_log.exported_count, 5)

    def test_demo_viewer_company_isolation(self):
        viewer = self.env.ref("auditlog.demo_user_auditlog_viewer", raise_if_not_found=False)
        company_b = self.env.ref("auditlog.demo_company_b", raise_if_not_found=False)
        if not viewer or not company_b:
            self.skipTest("demo data not loaded")
        self.assertTrue(self.Log.search_count([("company_id", "=", company_b.id)]))
        self.assertFalse(self.Log.with_user(viewer).search_count([("company_id", "=", company_b.id)]))
        self.assertTrue(self.Log.with_user(viewer).search_count([]))

    def test_rule_crud_and_name_search(self):
        rule = self.Rule.create({"name": "CRUD rule", "model_id": self.category_model.id})
        self.assertTrue(rule.exists())
        self.assertEqual(rule.state, "draft")
        self.assertEqual(rule.log_failure_policy, "block")
        rule.write({"name": "CRUD rule renamed"})
        self.assertEqual(rule.name, "CRUD rule renamed")
        self.assertIsInstance(self.Rule.name_search("CRUD", limit=5), list)
        rule.unlink()
        self.assertFalse(rule.exists())

    def test_log_crud_and_name_search(self):
        log = self.Log.create({"name": "Manual log", "method": "write",
                               "line_ids": [(0, 0, {"field_name": "name", "field_description": "Name"})]})
        line = log.line_ids
        self.assertEqual(line.display_name, "Name")
        log.write({"method": "create"})
        self.assertEqual(log.method, "create")
        self.assertIsInstance(self.Log.name_search("", limit=5), list)
        log.unlink()
        self.assertFalse(line.exists())

    def test_http_models_crud(self):
        session = self.env["auditlog.http.session"].create({"name": "fingerprint", "user_id": self.env.uid})
        http_request = self.env["auditlog.http.request"].create({
            "name": "/odoo/contacts", "root_url": "http://localhost/", "http_session_id": session.id,
        })
        self.assertIn("/odoo/contacts", http_request.display_name)
        self.assertIsInstance(self.env["auditlog.http.request"].name_search("", limit=5), list)
        self.assertFalse(self.env["auditlog.http.session"].current_http_session())
        self.assertFalse(self.env["auditlog.http.request"].current_http_request())
        http_request.unlink()
        session.unlink()
        self.assertFalse(session.exists())
