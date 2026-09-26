import json

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestAuditTrailBasics(TransactionCase):

    def test_demo_data_loaded(self):
        for model in ('audit.rule', 'audit.log', 'audit.log.line', 'audit.session'):
            self.assertGreater(self.env[model].search_count([]), 0, model)
        self.assertFalse(self.env['audit.rule'].search([('state', '=', 'active')]))

    def test_name_search(self):
        for model in ('audit.rule', 'audit.log', 'audit.log.line', 'audit.session'):
            self.assertIsInstance(self.env[model].name_search('', limit=5), list)

    def test_crud_session_and_log(self):
        rule = self.env['audit.rule'].create({
            'name': 'Currencies',
            'model_id': self.env['ir.model']._get('res.currency').id,
        })
        self.assertEqual(rule.company_id, self.env.company)
        session = self.env['audit.session'].create({'browser': 'Firefox', 'ip_address': '10.1.1.1'})
        log = self.env['audit.log'].create({
            'rule_id': rule.id,
            'res_id': 1,
            'record_name': 'USD',
            'action': 'write',
            'session_id': session.id,
            'line_ids': [(0, 0, {'field_description': 'Symbol', 'old_value': '$', 'new_value': 'US$'})],
        })
        self.assertEqual(log.res_model, 'res.currency')
        self.assertEqual(log.company_id, self.env.company)
        self.assertEqual(log.line_ids.res_model, 'res.currency')
        log.write({'record_name': 'US Dollar'})
        self.assertEqual(log.line_ids.record_name, 'US Dollar')
        rule.name = 'Currencies (all)'
        self.assertEqual(rule.name, 'Currencies (all)')
        log.unlink()
        self.assertFalse(log.exists())
        session.unlink()
        rule.unlink()
        self.assertFalse(rule.exists())


@tagged('post_install', '-at_install')
class TestAuditTrail(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner_model = cls.env['ir.model']._get('res.partner')
        cls.pricelist_model = cls.env['ir.model']._get('product.pricelist')
        cls.Rule = cls.env['audit.rule']
        cls.Log = cls.env['audit.log']
        # Starter demo rules may already exist for these models: remove them so
        # every test starts from a known configuration.
        cls.Rule.search([('company_id', '=', cls.company.id)]).action_set_draft()
        cls.Rule.search([('company_id', '=', cls.company.id)]).with_context(
            audit_force_unlink=True).unlink()
        cls.rule = cls.Rule.create({
            'name': 'Contacts',
            'model_id': cls.partner_model.id,
            'company_id': cls.company.id,
        })
        cls.auditor = new_test_user(
            cls.env, login='audit_auditor', groups='base.group_user,audit_trail.group_audit_user')
        cls.audit_admin = new_test_user(
            cls.env, login='audit_admin_user', groups='base.group_user,audit_trail.group_audit_manager')

    def setUp(self):
        super().setUp()
        # The active-rule map is cached across transactions; tests roll back.
        self.Rule._invalidate_rule_map()
        self.addCleanup(self.Rule._invalidate_rule_map)

    def _logs(self, record, action=None):
        domain = [('res_model', '=', record._name), ('res_id', '=', record.id)]
        if action:
            domain.append(('action', '=', action))
        return self.Log.search(domain)

    # ------------------------------------------------------------------
    # audit.rule configuration
    # ------------------------------------------------------------------
    def test_rule_defaults(self):
        self.assertEqual(self.rule.state, 'draft')
        self.assertEqual(self.rule.detail_level, 'full')
        self.assertTrue(self.rule.track_create)
        self.assertTrue(self.rule.track_write)
        self.assertTrue(self.rule.track_unlink)
        self.assertTrue(self.rule.track_export)
        self.assertFalse(self.rule.track_read)
        self.assertEqual(self.rule.model_name, 'res.partner')

    def test_duplicate_rule_refused_with_existing_name(self):
        with self.assertRaises(ValidationError) as ctx:
            self.Rule.create({
                'name': 'Second contacts rule',
                'model_id': self.partner_model.id,
                'company_id': self.company.id,
            })
        self.assertIn('Contacts', str(ctx.exception))

    def test_active_rule_locks_configuration(self):
        self.rule.action_confirm()
        self.assertEqual(self.rule.state, 'active')
        with self.assertRaises(UserError):
            self.rule.write({'detail_level': 'light'})
        self.rule.write({'name': 'Contacts (renamed)'})
        self.rule.action_set_draft()
        self.rule.write({'detail_level': 'light'})
        self.assertEqual(self.rule.detail_level, 'light')

    def test_active_rule_cannot_be_deleted(self):
        self.rule.action_confirm()
        with self.assertRaises(UserError):
            self.rule.unlink()

    # ------------------------------------------------------------------
    # Recording create / write / unlink
    # ------------------------------------------------------------------
    def test_draft_rule_records_nothing(self):
        partner = self.env['res.partner'].create({'name': 'Silent Partner'})
        partner.write({'phone': '+1 555 0100'})
        self.assertFalse(self._logs(partner))

    def test_create_is_logged_with_initial_values(self):
        self.rule.action_confirm()
        partner = self.env['res.partner'].create({'name': 'Nova Logistics', 'phone': '+1 555 0101'})
        log = self._logs(partner, 'create')
        self.assertEqual(len(log), 1)
        self.assertEqual(log.user_id, self.env.user)
        self.assertEqual(log.record_name, 'Nova Logistics')
        self.assertEqual(log.detail_level, 'full')
        self.assertEqual(log.company_id, self.company)
        name_line = log.line_ids.filtered(lambda l: l.field_id.name == 'name')
        self.assertEqual(name_line.new_value, 'Nova Logistics')
        self.assertFalse(name_line.old_value)

    def test_write_full_detail_keeps_old_and_new(self):
        partner = self.env['res.partner'].create({'name': 'Harbor Foods', 'phone': '+1 555 0102'})
        self.rule.action_confirm()
        partner.write({'phone': '+1 555 0199'})
        log = self._logs(partner, 'write')
        self.assertEqual(len(log), 1)
        phone_line = log.line_ids.filtered(lambda l: l.field_id.name == 'phone')
        self.assertEqual(phone_line.old_value, '+1 555 0102')
        self.assertEqual(phone_line.new_value, '+1 555 0199')
        self.assertEqual(phone_line.field_description, 'Phone')
        # Related search fields on the line
        self.assertEqual(phone_line.res_model, 'res.partner')
        self.assertEqual(phone_line.action, 'write')
        self.assertEqual(phone_line.user_id, self.env.user)

    def test_write_light_detail_skips_old_value(self):
        self.rule.detail_level = 'light'
        partner = self.env['res.partner'].create({'name': 'Pine Studio', 'phone': '+1 555 0103'})
        self.rule.action_confirm()
        partner.write({'phone': '+1 555 0104'})
        log = self._logs(partner, 'write')
        self.assertEqual(log.detail_level, 'light')
        phone_line = log.line_ids.filtered(lambda l: l.field_id.name == 'phone')
        self.assertFalse(phone_line.old_value)
        self.assertEqual(phone_line.new_value, '+1 555 0104')

    def test_write_without_change_logs_nothing(self):
        partner = self.env['res.partner'].create({'name': 'Same Value Ltd', 'phone': '+1 555 0105'})
        self.rule.action_confirm()
        partner.write({'phone': '+1 555 0105'})
        self.assertFalse(self._logs(partner, 'write'))

    def test_excluded_field_is_not_recorded(self):
        phone_field = self.env['ir.model.fields']._get('res.partner', 'phone')
        self.rule.excluded_field_ids = [(6, 0, phone_field.ids)]
        partner = self.env['res.partner'].create({'name': 'Quiet Phone', 'phone': '+1 555 0106'})
        self.rule.action_confirm()
        partner.write({'phone': '+1 555 0107', 'city': 'Denver'})
        log = self._logs(partner, 'write')
        self.assertFalse(log.line_ids.filtered(lambda l: l.field_id.name == 'phone'))
        self.assertTrue(log.line_ids.filtered(lambda l: l.field_id.name == 'city'))

    def test_excluded_user_is_not_recorded(self):
        self.rule.excluded_user_ids = [(6, 0, self.env.user.ids)]
        self.rule.action_confirm()
        partner = self.env['res.partner'].create({'name': 'Invisible Co'})
        self.assertFalse(self._logs(partner))

    def test_unlink_keeps_deleted_copy(self):
        partner = self.env['res.partner'].create({'name': 'Gone Tomorrow', 'city': 'Austin'})
        partner_id = partner.id
        self.rule.action_confirm()
        partner.unlink()
        log = self.Log.search([('res_model', '=', 'res.partner'), ('res_id', '=', partner_id),
                               ('action', '=', 'unlink')])
        self.assertEqual(len(log), 1)
        self.assertEqual(log.record_name, 'Gone Tomorrow')
        data = json.loads(log.deleted_data)
        self.assertEqual(data['name'], 'Gone Tomorrow')
        self.assertEqual(data['city'], 'Austin')

    def test_unlink_without_copy(self):
        self.rule.keep_deleted_copy = False
        partner = self.env['res.partner'].create({'name': 'No Copy Inc'})
        partner_id = partner.id
        self.rule.action_confirm()
        partner.unlink()
        log = self.Log.search([('res_model', '=', 'res.partner'), ('res_id', '=', partner_id)])
        self.assertEqual(log.action, 'unlink')
        self.assertFalse(log.deleted_data)

    def test_other_company_rule_does_not_record(self):
        other_company = self.env['res.company'].create({'name': 'Audit Other Co'})
        self.rule.action_set_draft()
        self.rule.company_id = other_company
        self.rule.action_confirm()
        partner = self.env['res.partner'].create({'name': 'Main Company Partner'})
        self.assertFalse(self._logs(partner))

    def test_disabled_action_is_not_recorded(self):
        self.rule.track_create = False
        self.rule.action_confirm()
        partner = self.env['res.partner'].create({'name': 'Not Tracked Create'})
        self.assertFalse(self._logs(partner, 'create'))
        partner.write({'city': 'Boise'})
        self.assertTrue(self._logs(partner, 'write'))

    # ------------------------------------------------------------------
    # Export / read
    # ------------------------------------------------------------------
    def test_export_logs_single_event_with_ids(self):
        partners = self.env['res.partner'].create([{'name': 'Export A'}, {'name': 'Export B'}])
        self.rule.action_confirm()
        partners.export_data(['name'])
        log = self.Log.search([('action', '=', 'export'), ('res_model', '=', 'res.partner')])
        self.assertEqual(len(log), 1)
        self.assertEqual(sorted(json.loads(log.exported_res_ids)), sorted(partners.ids))
        action = log.action_view_exported_records()
        self.assertEqual(action['res_model'], 'res.partner')
        self.assertEqual(action['domain'], [('id', 'in', sorted(partners.ids))])

    def test_read_only_logged_for_lists(self):
        partners = self.env['res.partner'].create([{'name': 'List A'}, {'name': 'List B'}])
        self.rule.track_read = True
        self.rule.action_confirm()
        spec = {'name': {}}
        self.env['res.partner'].web_search_read([('id', 'in', partners[:1].ids)], spec)
        self.assertFalse(self.Log.search([('action', '=', 'read')]))
        self.env['res.partner'].web_search_read([('id', 'in', partners.ids)], spec)
        self.assertEqual(len(self.Log.search([('action', '=', 'read')])), 1)

    def test_read_not_logged_when_off(self):
        partners = self.env['res.partner'].create([{'name': 'List C'}, {'name': 'List D'}])
        self.rule.action_confirm()
        self.env['res.partner'].web_search_read([('id', 'in', partners.ids)], {'name': {}})
        self.assertFalse(self.Log.search([('action', '=', 'read')]))

    # ------------------------------------------------------------------
    # Buttons, sessions, clean-up
    # ------------------------------------------------------------------
    def test_view_logs_button_on_watched_record(self):
        partner = self.env['res.partner'].create({'name': 'Button Partner'})
        action = partner.action_audit_view_logs()
        self.assertEqual(action['res_model'], 'audit.log')
        self.assertIn(('res_model', '=', 'res.partner'), action['domain'])
        self.assertIn(('res_id', '=', partner.id), action['domain'])

    def test_session_log_count(self):
        session = self.env['audit.session'].create({
            'user_id': self.env.user.id,
            'login_date': fields.Datetime.now(),
            'browser': 'Firefox 128',
            'ip_address': '10.0.0.5',
        })
        self.rule.action_confirm()
        partner = self.env['res.partner'].create({'name': 'Session Partner'})
        self._logs(partner).session_id = session
        self.assertEqual(session.log_count, 1)
        self.assertEqual(session.company_id, self.env.user.company_id)

    def test_cleanup_respects_company_switch_and_age(self):
        self.rule.action_confirm()
        partner = self.env['res.partner'].create({'name': 'Old History'})
        partner.write({'city': 'Reno'})
        old_log = self._logs(partner, 'create')
        recent_log = self._logs(partner, 'write')
        old_log.date = fields.Datetime.now() - relativedelta(months=8)
        # Disabled by default: nothing is removed
        self.assertFalse(self.company.audit_cleanup_enabled)
        self.assertEqual(self.company.audit_cleanup_age_months, 6)
        self.Log._cron_cleanup_logs()
        self.assertTrue(old_log.exists())
        self.company.audit_cleanup_enabled = True
        self.Log._cron_cleanup_logs()
        self.assertFalse(old_log.exists())
        self.assertTrue(recent_log.exists())

    def test_cleanup_age_must_be_positive(self):
        with self.assertRaises(ValidationError):
            self.company.audit_cleanup_age_months = 0

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------
    def test_auditor_is_read_only(self):
        self.rule.action_confirm()
        partner = self.env['res.partner'].create({'name': 'Auditor Visible'})
        log = self._logs(partner)
        self.assertTrue(log.with_user(self.auditor).read(['record_name']))
        with self.assertRaises(AccessError):
            self.Rule.with_user(self.auditor).create({
                'name': 'Forbidden', 'model_id': self.pricelist_model.id,
                'company_id': self.company.id})
        with self.assertRaises(AccessError):
            log.with_user(self.auditor).unlink()

    def test_audit_admin_can_delete_but_not_edit_history(self):
        self.rule.action_confirm()
        partner = self.env['res.partner'].create({'name': 'Admin Visible'})
        log = self._logs(partner)
        with self.assertRaises(AccessError):
            log.with_user(self.audit_admin).write({'record_name': 'Tampered'})
        log.with_user(self.audit_admin).unlink()
        self.assertFalse(log.exists())

    def test_audit_admin_manages_rules(self):
        rule = self.Rule.with_user(self.audit_admin).create({
            'name': 'Price Lists', 'model_id': self.pricelist_model.id,
            'company_id': self.company.id})
        rule.action_confirm()
        self.assertEqual(rule.state, 'active')

    def test_system_admin_gets_audit_admin(self):
        self.assertTrue(self.env.ref('base.user_admin').has_group('audit_trail.group_audit_manager'))
