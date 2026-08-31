import json
from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger

MODULE = "audit_trail"


@tagged("post_install", "-at_install")
class AuditTrailCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner_model = cls.env["ir.model"]._get("res.partner")
        cls.Partner = cls.env["res.partner"]
        cls.Log = cls.env["audit.log"]

    @classmethod
    def _field(cls, model_name, field_name):
        return cls.env["ir.model.fields"].search(
            [("model", "=", model_name), ("name", "=", field_name)], limit=1
        )

    def _make_rule(self, activate=True, **overrides):
        values = {
            "name": "Contacts audit",
            "model_id": self.partner_model.id,
            "company_id": self.company.id,
            "detail_level": "full",
            "track_create": True,
            "track_write": True,
            "track_unlink": True,
            "track_export": True,
            "track_read": False,
            "keep_deleted_snapshot": False,
        }
        values.update(overrides)
        # Demo data ships an active rule on res.partner plus a recorded history;
        # drop both so each test starts from a known, empty trail.
        model_name = self.env["ir.model"].browse(values["model_id"]).model
        self.env["audit.rule"].sudo().search([
            ("model_id", "=", values["model_id"]),
            ("company_id", "=", values["company_id"]),
        ]).unlink()
        self.env["audit.log"].sudo().search(
            [("res_model", "=", model_name)]
        ).unlink()
        rule = self.env["audit.rule"].create(values)
        if activate:
            rule.action_confirm()
        return rule

    def _logs(self, action=None, res_id=None):
        domain = [("res_model", "=", "res.partner")]
        if action:
            domain.append(("action", "=", action))
        if res_id is not None:
            domain.append(("res_id", "=", res_id))
        return self.Log.search(domain)


@tagged("post_install", "-at_install")
class TestAuditRule(AuditTrailCommon):

    def test_state_flow_stamps_confirmation(self):
        rule = self._make_rule(activate=False)
        self.assertEqual(rule.state, "draft")
        self.assertFalse(rule.date_confirmed)

        rule.action_confirm()
        self.assertEqual(rule.state, "active")
        self.assertTrue(rule.date_confirmed)

        rule.action_draft()
        self.assertEqual(rule.state, "draft")
        self.assertTrue(
            rule.date_confirmed,
            "Setting a rule back to draft must not erase the confirmation stamp",
        )

    def test_duplicate_rule_is_blocked(self):
        first = self._make_rule(activate=False)
        with self.assertRaises(ValidationError):
            self.env["audit.rule"].create({
                "name": "Second rule",
                "model_id": self.partner_model.id,
                "company_id": self.company.id,
            })
        self.assertTrue(first.exists())

    def test_duplicate_rule_blocked_at_database_level(self):
        """The Python check must be backed by a real unique constraint.

        @api.constrains alone races under concurrency, so the uniqueness has to
        exist as a database constraint too.
        """
        constraint = self.env["ir.model.constraint"].search([
            ("name", "like", "%unique_model_company%"),
        ], limit=1)
        self.assertTrue(
            constraint,
            "audit.rule must ship a UNIQUE(model_id, company_id) database constraint",
        )
        self.assertEqual(constraint.type, "u")

    def test_excluded_fields_must_belong_to_watched_model(self):
        rule = self._make_rule(activate=False)
        with self.assertRaises(ValidationError):
            rule.excluded_field_ids = [
                fields.Command.link(self._field("res.users", "login").id)
            ]

    def test_nothing_recorded_while_draft(self):
        self._make_rule(activate=False)
        partner = self.Partner.create({"name": "Draft rule contact"})
        self.assertFalse(self._logs(res_id=partner.id))


@tagged("post_install", "-at_install")
class TestAuditRecording(AuditTrailCommon):

    def test_create_records_starting_values(self):
        self._make_rule()
        partner = self.Partner.create({"name": "Ada Lovelace", "email": "ada@example.com"})

        logs = self._logs(action="create", res_id=partner.id)
        self.assertEqual(len(logs), 1)
        log = logs
        self.assertEqual(log.record_name, "Ada Lovelace")
        self.assertEqual(log.user_id, self.env.user)
        self.assertEqual(log.detail_level, "full")
        self.assertTrue(log.line_ids)

        email_line = log.line_ids.filtered(lambda line: line.field_id.name == "email")
        self.assertEqual(len(email_line), 1)
        self.assertEqual(email_line.new_value, "ada@example.com")
        self.assertFalse(
            email_line.old_value, "A creation has no previous value to record"
        )

    def test_write_full_detail_records_old_and_new(self):
        self._make_rule()
        partner = self.Partner.create({"name": "Grace", "phone": "+1 111"})
        partner.write({"phone": "+1 222"})

        logs = self._logs(action="write", res_id=partner.id)
        self.assertEqual(len(logs), 1)
        line = logs.line_ids.filtered(lambda line: line.field_id.name == "phone")
        self.assertEqual(len(line), 1)
        self.assertEqual(line.old_value, "+1 111")
        self.assertEqual(line.new_value, "+1 222")

    def test_write_light_detail_leaves_old_value_blank(self):
        self._make_rule(detail_level="light")
        partner = self.Partner.create({"name": "Alan", "phone": "+1 111"})
        partner.write({"phone": "+1 222"})

        logs = self._logs(action="write", res_id=partner.id)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs.detail_level, "light")
        line = logs.line_ids.filtered(lambda line: line.field_id.name == "phone")
        self.assertEqual(line.new_value, "+1 222")
        self.assertFalse(line.old_value)

    def test_write_without_effective_change_records_nothing(self):
        self._make_rule()
        partner = self.Partner.create({"name": "Same", "phone": "+1 111"})
        partner.write({"phone": "+1 111"})
        self.assertFalse(self._logs(action="write", res_id=partner.id))

    def test_unlink_stores_snapshot_and_scrubs_excluded_fields(self):
        rule = self._make_rule(activate=False, keep_deleted_snapshot=True)
        rule.excluded_field_ids = [
            fields.Command.link(self._field("res.partner", "comment").id)
        ]
        rule.action_confirm()

        partner = self.Partner.create({
            "name": "To be deleted",
            "email": "gone@example.com",
            "comment": "<p>secret note</p>",
        })
        partner_id = partner.id
        partner.unlink()

        logs = self._logs(action="unlink", res_id=partner_id)
        self.assertEqual(len(logs), 1)
        self.assertFalse(logs.line_ids, "A deletion records no field-change lines")
        snapshot = json.loads(logs.deleted_snapshot)
        self.assertEqual(snapshot.get("email"), "gone@example.com")
        self.assertNotIn(
            "comment", snapshot, "Excluded fields must be scrubbed from the snapshot"
        )

    def test_unlink_without_snapshot_option(self):
        self._make_rule(keep_deleted_snapshot=False)
        partner = self.Partner.create({"name": "No snapshot"})
        partner_id = partner.id
        partner.unlink()

        logs = self._logs(action="unlink", res_id=partner_id)
        self.assertEqual(len(logs), 1)
        self.assertFalse(logs.deleted_snapshot)

    def test_excluded_field_never_appears_in_lines(self):
        rule = self._make_rule(activate=False)
        rule.excluded_field_ids = [
            fields.Command.link(self._field("res.partner", "phone").id)
        ]
        rule.action_confirm()

        partner = self.Partner.create({"name": "Hidden phone", "phone": "+1 000"})
        partner.write({"phone": "+1 999", "email": "shown@example.com"})

        create_log = self._logs(action="create", res_id=partner.id)
        self.assertFalse(create_log.line_ids.filtered(
            lambda line: line.field_id.name == "phone"
        ))
        write_log = self._logs(action="write", res_id=partner.id)
        self.assertTrue(write_log)
        self.assertFalse(write_log.line_ids.filtered(
            lambda line: line.field_id.name == "phone"
        ))
        self.assertTrue(write_log.line_ids.filtered(
            lambda line: line.field_id.name == "email"
        ))

    def _make_integration_user(self, login):
        group_ids = [self.env.ref("base.group_user").id]
        # Creating contacts needs the contact-creation privilege on top of the
        # plain internal-user group.
        partner_manager = self.env.ref(
            "base.group_partner_manager", raise_if_not_found=False
        )
        if partner_manager:
            group_ids.append(partner_manager.id)
        return self.env["res.users"].create({
            "name": "Integration Bot",
            "login": login,
            "group_ids": [fields.Command.set(group_ids)],
        })

    def test_excluded_user_produces_no_event(self):
        integration = self._make_integration_user("audit_excluded_bot")
        rule = self._make_rule(activate=False, excluded_user_ids=[
            fields.Command.link(integration.id)
        ])
        rule.action_confirm()

        config = self.env["audit.rule"]._audit_rule_config(
            "res.partner", self.company.id
        )
        self.assertIn(integration.id, config["excluded_user_ids"])

        silent = self.Partner.with_user(integration).create({"name": "Silent create"})
        silent.with_user(integration).write({"phone": "+1 555"})
        self.assertFalse(self._logs(res_id=silent.id))

        recorded = self.Partner.create({"name": "Recorded create"})
        self.assertTrue(
            self._logs(res_id=recorded.id),
            "Only the excluded user is silenced, not everyone else",
        )

    def test_exclusion_survives_archiving_the_user(self):
        """Archiving an excluded account must not silently resume recording it."""
        integration = self._make_integration_user("audit_archived_bot")
        rule = self._make_rule(activate=False, excluded_user_ids=[
            fields.Command.link(integration.id)
        ])
        rule.action_confirm()
        integration.write({"active": False})

        config = self.env["audit.rule"]._audit_rule_config(
            "res.partner", self.company.id
        )
        self.assertIn(integration.id, config["excluded_user_ids"])

    def test_untracked_action_is_not_recorded(self):
        self._make_rule(track_write=False)
        partner = self.Partner.create({"name": "Create only"})
        partner.write({"phone": "+1 777"})
        self.assertTrue(self._logs(action="create", res_id=partner.id))
        self.assertFalse(self._logs(action="write", res_id=partner.id))

    def test_export_records_exported_ids(self):
        self._make_rule()
        partners = self.Partner.create([
            {"name": "Export A"}, {"name": "Export B"}, {"name": "Export C"}
        ])
        partners.export_data(["name"])

        logs = self._logs(action="export")
        self.assertEqual(len(logs), 1)
        self.assertFalse(logs.line_ids)
        self.assertEqual(sorted(logs._audit_exported_ids()), sorted(partners.ids))
        self.assertEqual(logs.exported_count, 3)

        action = logs.action_view_exported_records()
        self.assertEqual(action["res_model"], "res.partner")
        self.assertEqual(sorted(action["domain"][0][2]), sorted(partners.ids))

    def test_read_tracking_records_one_event_per_record(self):
        self._make_rule(track_read=True)
        partners = self.Partner.create([{"name": "Read A"}, {"name": "Read B"}])
        self.Log.search([("action", "=", "read")]).unlink()

        partners.web_read({"display_name": {}})

        logs = self._logs(action="read")
        self.assertEqual(len(logs), 2)
        self.assertFalse(logs.line_ids)
        self.assertEqual(set(logs.mapped("res_id")), set(partners.ids))

    def test_read_not_recorded_when_option_is_off(self):
        self._make_rule(track_read=False)
        partner = self.Partner.create({"name": "Unwatched read"})
        partner.web_read({"display_name": {}})
        self.assertFalse(self._logs(action="read", res_id=partner.id))

    def test_unwatched_model_is_never_recorded(self):
        self._make_rule()
        tag = self.env["res.partner.category"].create({"name": "Unwatched tag"})
        tag.write({"name": "Unwatched tag renamed"})
        tag.unlink()
        self.assertFalse(self.Log.search([("res_model", "=", "res.partner.category")]))

    def test_recording_failure_never_aborts_the_host_write(self):
        """A broken audit side-effect must not roll back the user's action."""
        self._make_rule()
        original = type(self.env["audit.log"]).create

        def exploding_create(self, vals_list):
            raise ValueError("audit backend unavailable")

        type(self.env["audit.log"]).create = exploding_create
        try:
            with mute_logger("odoo.addons.%s.models.base_audit" % MODULE):
                partner = self.Partner.create({"name": "Survives audit failure"})
                partner.write({"phone": "+1 424"})
        finally:
            type(self.env["audit.log"]).create = original

        self.assertTrue(partner.exists())
        self.assertEqual(partner.phone, "+1 424")


@tagged("post_install", "-at_install")
class TestAuditSession(AuditTrailCommon):

    def test_events_are_attached_to_a_session_and_screen(self):
        self._make_rule()
        partner = self.Partner.create({"name": "Session contact"})
        log = self._logs(action="create", res_id=partner.id)

        self.assertTrue(log.session_id)
        self.assertEqual(log.session_id.user_id, self.env.user)
        self.assertTrue(log.page_action_id)
        self.assertEqual(log.page_action_id.res_model, "res.partner")
        self.assertEqual(log.page_action_id.session_id, log.session_id)
        self.assertGreaterEqual(log.session_id.log_count, 1)

    def test_activity_within_timeout_reuses_the_session(self):
        self._make_rule()
        first = self.Partner.create({"name": "First"})
        second = self.Partner.create({"name": "Second"})
        session_one = self._logs(action="create", res_id=first.id).session_id
        session_two = self._logs(action="create", res_id=second.id).session_id
        self.assertEqual(session_one, session_two)

    def test_gap_past_the_timeout_opens_a_new_session(self):
        self._make_rule()
        first = self.Partner.create({"name": "Before the gap"})
        session_one = self._logs(action="create", res_id=first.id).session_id
        self.assertTrue(session_one)

        stale = fields.Datetime.now() - timedelta(
            minutes=self.env["audit.session"]._audit_inactivity_minutes() + 5
        )
        session_one.write({"last_activity_datetime": stale})

        second = self.Partner.create({"name": "After the gap"})
        session_two = self._logs(action="create", res_id=second.id).session_id
        self.assertTrue(session_two)
        self.assertNotEqual(session_one, session_two)


@tagged("post_install", "-at_install")
class TestAuditCleanup(AuditTrailCommon):

    def _make_log(self, days_old):
        log = self.Log.create({
            "res_model": "res.partner",
            "res_id": 1,
            "record_name": "Old event",
            "action": "write",
            "user_id": self.env.uid,
            "company_id": self.company.id,
            "detail_level": "full",
            "line_ids": [fields.Command.create({
                "field_description": "Phone",
                "old_value": "a",
                "new_value": "b",
            })],
        })
        log.write({"date": fields.Datetime.now() - timedelta(days=days_old)})
        return log

    def test_cleanup_is_disabled_by_default(self):
        settings = self.Log._audit_cleanup_settings()
        self.assertFalse(settings["enabled"])
        self.assertEqual(settings["retention_days"], 180)
        self.assertEqual(settings["batch_size"], 1000)

        old_log = self._make_log(400)
        self.Log._cron_cleanup_logs()
        self.assertTrue(old_log.exists(), "Nothing may be deleted while clean-up is off")

    def test_cleanup_deletes_expired_events_and_their_lines(self):
        old_log = self._make_log(400)
        recent_log = self._make_log(3)
        line_ids = old_log.line_ids.ids

        config = self.env["audit.config"].create({
            "cleanup_enabled": True,
            "retention_days": 180,
            "batch_size": 1000,
        })
        config.action_save()

        self.Log._cron_cleanup_logs()
        self.assertFalse(old_log.exists())
        self.assertTrue(recent_log.exists())
        self.assertFalse(
            self.env["audit.log.line"].browse(line_ids).exists(),
            "Deleting an event must cascade to its field changes",
        )

    def test_saving_settings_toggles_the_scheduled_job(self):
        cron = self.env.ref("%s.ir_cron_audit_log_cleanup" % MODULE)
        self.assertFalse(cron.active, "The clean-up job ships disabled")

        config = self.env["audit.config"].create({
            "cleanup_enabled": True,
            "retention_days": 90,
            "batch_size": 500,
        })
        config.action_save()
        self.assertTrue(cron.active)

        settings = self.Log._audit_cleanup_settings()
        self.assertTrue(settings["enabled"])
        self.assertEqual(settings["retention_days"], 90)
        self.assertEqual(settings["batch_size"], 500)

        config.cleanup_enabled = False
        config.action_save()
        self.assertFalse(cron.active)

    def test_settings_screen_reloads_saved_values(self):
        config = self.env["audit.config"].create({
            "cleanup_enabled": True,
            "retention_days": 42,
            "batch_size": 7,
        })
        config.action_save()

        defaults = self.env["audit.config"].default_get(
            ["cleanup_enabled", "retention_days", "batch_size"]
        )
        self.assertTrue(defaults["cleanup_enabled"])
        self.assertEqual(defaults["retention_days"], 42)
        self.assertEqual(defaults["batch_size"], 7)

    def test_settings_reject_impossible_values(self):
        with self.assertRaises(ValidationError):
            self.env["audit.config"].create({
                "cleanup_enabled": True,
                "retention_days": 0,
                "batch_size": 100,
            })


@tagged("post_install", "-at_install")
class TestAuditSecurity(AuditTrailCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auditor = cls.env["res.users"].create({
            "name": "Aud Itor",
            "login": "audit_trail_auditor",
            "group_ids": [fields.Command.set([
                cls.env.ref("base.group_user").id,
                cls.env.ref("%s.group_audit_user" % MODULE).id,
            ])],
        })
        cls.plain_user = cls.env["res.users"].create({
            "name": "Plain User",
            "login": "audit_trail_plain",
            "group_ids": [fields.Command.set([cls.env.ref("base.group_user").id])],
        })
        # Deliberately NOT an administrator and NOT in base.group_erp_manager —
        # this is the exact seat the "Audit Administrator" role is meant to be:
        # able to manage watch rules, nothing more. The account owner used
        # during manual testing holds group_erp_manager implicitly, which is
        # why a real audit-manager-only login is required to catch this class
        # of bug at all.
        cls.manager_role = cls.env["res.users"].create({
            "name": "Audit Admin Role",
            "login": "audit_trail_manager_role",
            "group_ids": [fields.Command.set([
                cls.env.ref("base.group_user").id,
                cls.env.ref("%s.group_audit_manager" % MODULE).id,
            ])],
        })

    def test_manager_group_implies_auditor_group(self):
        manager_group = self.env.ref("%s.group_audit_manager" % MODULE)
        user_group = self.env.ref("%s.group_audit_user" % MODULE)
        self.assertIn(user_group, manager_group.implied_ids)

    def test_system_administrators_are_audit_administrators(self):
        manager_group = self.env.ref("%s.group_audit_manager" % MODULE)
        self.assertIn(manager_group, self.env.ref("base.group_system").implied_ids)
        self.assertTrue(self.env.ref("base.user_admin").has_group(
            "%s.group_audit_manager" % MODULE
        ))

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.addons.base.models.ir_model")
    def test_auditor_is_read_only_on_logs(self):
        self._make_rule()
        partner = self.Partner.create({"name": "Read only check"})
        log = self._logs(action="create", res_id=partner.id)

        self.assertTrue(log.with_user(self.auditor).read(["record_name"]))
        with self.assertRaises(AccessError):
            log.with_user(self.auditor).write({"record_name": "tampered"})
        with self.assertRaises(AccessError):
            log.with_user(self.auditor).unlink()

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.addons.base.models.ir_model")
    def test_auditor_may_read_but_not_change_rules(self):
        rule = self._make_rule()
        self.assertTrue(rule.with_user(self.auditor).read(["name"]))
        with self.assertRaises(AccessError):
            rule.with_user(self.auditor).write({"name": "tampered"})

    def test_audit_manager_role_can_open_a_rule_with_excluded_fields(self):
        """Regression: opening a Watch Rule as the Audit Administrator seat.

        excluded_field_ids is a Many2many onto ir.model.fields, which Odoo
        gates behind base.group_erp_manager ("Access Rights"). The account
        owner holds that group implicitly, so this only reproduces from a
        login that has group_audit_manager and nothing more — exactly
        cls.manager_role, not self.env.user.
        """
        rule = self._make_rule(activate=False)
        rule.excluded_field_ids = [
            fields.Command.link(self._field("res.partner", "phone").id)
        ]
        rule.action_confirm()

        as_manager = rule.with_user(self.manager_role)
        as_manager.read(["name", "excluded_field_ids"])
        self.assertTrue(as_manager.excluded_field_ids)

    def test_auditor_role_can_open_a_rule_with_excluded_fields(self):
        """Regression: opening a Watch Rule as the Auditor seat.

        Same root cause as test_audit_manager_role_can_open_a_rule_with_
        excluded_fields, one group over: excluded_field_ids is a Many2many
        onto ir.model.fields, so group_audit_user needs its own read grant
        on that model too. cls.auditor holds only group_audit_user (plus
        base.group_user), not group_audit_manager and not group_erp_manager,
        so this only reproduces from that login, not self.env.user.
        """
        rule = self._make_rule(activate=False)
        rule.excluded_field_ids = [
            fields.Command.link(self._field("res.partner", "phone").id)
        ]
        rule.action_confirm()

        as_auditor = rule.with_user(self.auditor)
        as_auditor.read(["name", "excluded_field_ids"])
        self.assertTrue(as_auditor.excluded_field_ids)

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.addons.base.models.ir_model")
    def test_every_internal_user_may_read_rules_but_not_logs(self):
        rule = self._make_rule()
        partner = self.Partner.create({"name": "Visibility check"})
        log = self._logs(action="create", res_id=partner.id)

        self.assertTrue(rule.with_user(self.plain_user).read(["name"]))
        with self.assertRaises(AccessError):
            log.with_user(self.plain_user).read(["record_name"])

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.addons.base.models.ir_model")
    def test_auditor_has_no_access_to_cleanup_settings(self):
        with self.assertRaises(AccessError):
            self.env["audit.config"].with_user(self.auditor).create({})

    def test_company_rules_exist_for_every_stored_model(self):
        for xml_id in (
            "audit_rule_company_rule",
            "audit_log_company_rule",
            "audit_log_line_company_rule",
            "audit_session_company_rule",
            "audit_page_action_company_rule",
        ):
            rule = self.env.ref("%s.%s" % (MODULE, xml_id))
            self.assertFalse(
                rule.groups,
                "Company rules must stay global, otherwise another group rule "
                "could be OR-ed in and bypass the company isolation",
            )
            self.assertIn("company_ids", rule.domain_force)


@tagged("post_install", "-at_install")
class TestAuditRecordButton(AuditTrailCommon):

    def test_view_logs_button_targets_the_exact_record(self):
        self._make_rule()
        partner = self.Partner.create({"name": "Button target"})
        action = partner.action_view_audit_logs()

        self.assertEqual(action["res_model"], "audit.log")
        self.assertIn(("res_model", "=", "res.partner"), action["domain"])
        self.assertIn(("res_id", "=", partner.id), action["domain"])
        logs = self.Log.search(action["domain"])
        self.assertTrue(logs)
        self.assertEqual(set(logs.mapped("res_id")), {partner.id})


@tagged("post_install", "-at_install")
class TestAuditDemoData(AuditTrailCommon):

    def test_demo_watch_rule_is_shipped_and_active(self):
        rule = self.env.ref("%s.demo_audit_rule_partner" % MODULE, raise_if_not_found=False)
        self.assertTrue(rule, "Demo data must ship a watch rule on Contacts")
        self.assertEqual(rule.model_name, "res.partner")
        self.assertEqual(rule.state, "active")
        self.assertEqual(rule.detail_level, "full")
        self.assertTrue(rule.keep_deleted_snapshot)
        self.assertFalse(rule.track_read)
        self.assertTrue(rule.excluded_user_ids)

    def test_demo_events_cover_every_action(self):
        logs = self.Log.search([("rule_id.model_name", "=", "res.partner")])
        self.assertGreaterEqual(len(logs), 15)
        recorded_actions = set(logs.mapped("action"))
        for action in ("create", "write", "unlink", "export", "read"):
            self.assertIn(action, recorded_actions)

    def test_demo_deletion_carries_a_snapshot(self):
        deletions = self.Log.search([
            ("action", "=", "unlink"), ("deleted_snapshot", "!=", False)
        ])
        self.assertTrue(deletions)
        snapshot = json.loads(deletions[0].deleted_snapshot)
        self.assertIsInstance(snapshot, dict)
        self.assertTrue(snapshot)

    def test_demo_export_event_reopens_its_records(self):
        exports = self.Log.search([("action", "=", "export")])
        self.assertTrue(exports)
        self.assertGreaterEqual(exports[0].exported_count, 3)

    def test_demo_sessions_link_screens_and_events(self):
        sessions = self.env["audit.session"].search([])
        self.assertGreaterEqual(len(sessions), 2)
        self.assertTrue(sessions.mapped("page_action_ids"))
        self.assertTrue(sessions.mapped("log_ids"))
