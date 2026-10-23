from datetime import timedelta

from psycopg2 import IntegrityError

from odoo import fields
from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestOdomateLaunchpad(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Usage = cls.env['odomate.launchpad.usage']
        cls.Pin = cls.env['odomate.launchpad.pin']
        cls.user_a = new_test_user(cls.env, login='lp_user_a', groups='base.group_user')
        cls.user_b = new_test_user(cls.env, login='lp_user_b', groups='base.group_user')
        cls.action = cls.env.ref('odomate_launchpad.action_odomate_launchpad')
        action_ref = 'ir.actions.client,%d' % cls.action.id
        Menu = cls.env['ir.ui.menu']
        cls.menu_zeta = Menu.create({'name': 'Zeta Test App', 'action': action_ref})
        cls.menu_alpha = Menu.create({'name': 'Alpha Test App', 'action': action_ref})
        cls.menu_beta = Menu.create({'name': 'Beta Test App', 'action': action_ref})
        cls.menu_gamma = Menu.create({'name': 'Gamma Test App', 'action': action_ref})
        cls.menu_child = Menu.create({
            'name': 'Child Test Menu',
            'parent_id': cls.menu_zeta.id,
            'action': action_ref,
        })
        cls.test_menus = cls.menu_zeta | cls.menu_alpha | cls.menu_beta | cls.menu_gamma

    def _log(self, user, menu, days_ago=0, times=1):
        when = fields.Datetime.now() - timedelta(days=days_ago)
        self.Usage.create([
            {'user_id': user.id, 'menu_id': menu.id, 'used_on': when}
            for _i in range(times)
        ])

    def _state(self, user):
        return self.Usage.with_user(user).get_launchpad_state(self.test_menus.ids)

    def test_usage_defaults(self):
        usage = self.Usage.with_user(self.user_a).create({'menu_id': self.menu_alpha.id})
        self.assertEqual(usage.user_id, self.user_a)
        self.assertTrue(usage.used_on)

    def test_log_open_creates_row_for_current_user(self):
        result = self.Usage.with_user(self.user_a).log_open(self.menu_beta.id)
        self.assertTrue(result)
        rows = self.Usage.search([('menu_id', '=', self.menu_beta.id)])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.user_id, self.user_a)

    def test_log_open_ignores_non_root_or_missing_menu(self):
        self.assertFalse(self.Usage.with_user(self.user_a).log_open(self.menu_child.id))
        self.assertFalse(self.Usage.with_user(self.user_a).log_open(0))
        self.assertFalse(self.Usage.search([('menu_id', '=', self.menu_child.id)]))

    def test_order_alphabetical_without_history(self):
        state = self._state(self.user_a)
        self.assertEqual(
            state['ordered_ids'],
            [self.menu_alpha.id, self.menu_beta.id, self.menu_gamma.id, self.menu_zeta.id],
        )
        self.assertEqual(state['pinned_ids'], [])

    def test_order_by_usage_then_name(self):
        self._log(self.user_a, self.menu_zeta, times=3)
        self._log(self.user_a, self.menu_gamma, times=1)
        self._log(self.user_a, self.menu_beta, times=1)
        state = self._state(self.user_a)
        self.assertEqual(
            state['ordered_ids'],
            [self.menu_zeta.id, self.menu_beta.id, self.menu_gamma.id, self.menu_alpha.id],
        )
        self.assertEqual(state['counts'][str(self.menu_zeta.id)], 3)

    def test_usage_older_than_30_days_ignored(self):
        self._log(self.user_a, self.menu_zeta, days_ago=40, times=5)
        self._log(self.user_a, self.menu_gamma, days_ago=2, times=1)
        state = self._state(self.user_a)
        self.assertEqual(state['ordered_ids'][0], self.menu_gamma.id)
        self.assertNotIn(str(self.menu_zeta.id), state['counts'])

    def test_usage_is_personal(self):
        self._log(self.user_b, self.menu_zeta, times=10)
        state = self._state(self.user_a)
        self.assertEqual(state['ordered_ids'][0], self.menu_alpha.id)

    def test_pins_come_first_by_sequence(self):
        self._log(self.user_a, self.menu_alpha, times=5)
        PinA = self.Pin.with_user(self.user_a)
        self.assertTrue(PinA.toggle_pin(self.menu_zeta.id))
        self.assertTrue(PinA.toggle_pin(self.menu_gamma.id))
        state = self._state(self.user_a)
        self.assertEqual(state['ordered_ids'][:3], [self.menu_zeta.id, self.menu_gamma.id, self.menu_alpha.id])
        self.assertEqual(state['pinned_ids'], [self.menu_zeta.id, self.menu_gamma.id])

    def test_toggle_pin_is_personal(self):
        self.Pin.with_user(self.user_b).toggle_pin(self.menu_beta.id)
        PinA = self.Pin.with_user(self.user_a)
        self.assertTrue(PinA.toggle_pin(self.menu_beta.id))
        self.assertFalse(PinA.toggle_pin(self.menu_beta.id))
        remaining = self.Pin.search([('menu_id', '=', self.menu_beta.id)])
        self.assertEqual(remaining.user_id, self.user_b)

    def test_pin_unique_per_user_and_menu(self):
        self.Pin.create({'user_id': self.user_a.id, 'menu_id': self.menu_alpha.id})
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError), self.cr.savepoint():
            self.Pin.create({'user_id': self.user_a.id, 'menu_id': self.menu_alpha.id})

    def test_record_rules_isolate_users(self):
        self._log(self.user_a, self.menu_alpha)
        self.Pin.create({'user_id': self.user_a.id, 'menu_id': self.menu_alpha.id})
        self.assertFalse(self.Usage.with_user(self.user_b).search([('menu_id', '=', self.menu_alpha.id)]))
        self.assertFalse(self.Pin.with_user(self.user_b).search([('menu_id', '=', self.menu_alpha.id)]))
        self.assertTrue(self.Usage.with_user(self.user_a).search([('menu_id', '=', self.menu_alpha.id)]))

    def test_set_as_home_only_for_current_user(self):
        self.assertFalse(self._state(self.user_a)['is_home'])
        self.Usage.with_user(self.user_a).set_launchpad_as_home()
        self.assertEqual(self.user_a.action_id.id, self.action.id)
        self.assertFalse(self.user_b.action_id)
        self.assertTrue(self._state(self.user_a)['is_home'])
        self.Usage.with_user(self.user_a).reset_launchpad_home()
        self.assertFalse(self.user_a.action_id)
        self.assertFalse(self._state(self.user_a)['is_home'])

    def test_menu_deletion_cascades(self):
        self._log(self.user_a, self.menu_gamma, times=2)
        self.Pin.create({'user_id': self.user_a.id, 'menu_id': self.menu_gamma.id})
        self.menu_gamma.unlink()
        self.assertFalse(self.Usage.search([('menu_id', '=', self.menu_gamma.id)]))
        self.assertFalse(self.Pin.search([('menu_id', '=', self.menu_gamma.id)]))

    def test_demo_data_loaded(self):
        if not self.env.ref('odomate_launchpad.demo_usage_discuss_01', raise_if_not_found=False):
            self.skipTest("Demo data is not loaded in this database.")
        admin = self.env.ref('base.user_admin')
        self.assertGreater(self.Usage.search_count([('user_id', '=', admin.id)]), 0)
        self.assertGreater(self.Pin.search_count([('user_id', '=', admin.id)]), 0)

    def test_write_and_unlink_own_records(self):
        usage = self.Usage.with_user(self.user_a).create({
            'menu_id': self.menu_alpha.id,
            'used_on': '2026-01-15 10:00:00',
        })
        usage.used_on = '2026-01-20 08:30:00'
        self.assertEqual(usage.used_on, fields.Datetime.to_datetime('2026-01-20 08:30:00'))
        pin = self.Pin.with_user(self.user_a).create({'menu_id': self.menu_alpha.id})
        pin.sequence = 3
        self.assertEqual(pin.sequence, 3)
        usage.unlink()
        pin.unlink()
        self.assertFalse(usage.exists())
        self.assertFalse(pin.exists())

    def test_name_search(self):
        self.Pin.with_user(self.user_a).create({'menu_id': self.menu_alpha.id})
        self.assertIsInstance(self.Usage.with_user(self.user_a).name_search('', limit=5), list)
        result = self.Pin.with_user(self.user_a).name_search('Alpha', limit=5)
        self.assertIsInstance(result, list)

    def test_invisible_menu_excluded(self):
        self.menu_beta.group_ids = [(6, 0, [self.env.ref('base.group_system').id])]
        state = self._state(self.user_a)
        self.assertNotIn(self.menu_beta.id, state['ordered_ids'])
