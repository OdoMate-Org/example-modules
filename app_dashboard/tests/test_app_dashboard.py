from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestAppDashboard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Users = cls.env['res.users']
        cls.Menu = cls.env['ir.ui.menu']
        cls.dashboard_action = cls.env.ref('app_dashboard.action_apps_dashboard')
        cls.dashboard_menu = cls.env.ref('app_dashboard.menu_apps_dashboard_root')
        cls.user = new_test_user(cls.env, login='app_dash_user', groups='base.group_user')
        client_action = cls.env['ir.actions.client'].create({
            'name': 'Test App Action',
            'tag': 'app_dashboard.test_tag',
        })
        cls.open_app = cls.Menu.create({
            'name': 'Open Test App',
            'action': f'ir.actions.client,{client_action.id}',
            'web_icon': 'app_dashboard,static/description/icon.svg',
        })
        cls.restricted_app = cls.Menu.create({
            'name': 'Restricted Test App',
            'action': f'ir.actions.client,{client_action.id}',
            'web_icon': 'app_dashboard,static/description/icon.svg',
            'group_ids': [(4, cls.env.ref('base.group_system').id)],
        })
        cls.sub_menu = cls.Menu.create({
            'name': 'Sub Menu',
            'parent_id': cls.open_app.id,
            'action': f'ir.actions.client,{client_action.id}',
        })

        cls.folder_app = cls.Menu.create({
            'name': 'Folder Test App',
            'web_icon': 'app_dashboard,static/description/icon.svg',
        })
        cls.Menu.create({
            'name': 'Folder Child',
            'parent_id': cls.folder_app.id,
            'action': f'ir.actions.client,{client_action.id}',
        })

    def _app_ids(self, data):
        return [app['id'] for app in data['apps']]

    def test_default_values(self):
        self.assertEqual(self.user.home_screen_mode, 'default_menu')
        self.assertFalse(self.user.favorite_app_menu_ids)

    def test_home_screen_mode_sets_and_clears_home_action(self):
        self.user.home_screen_mode = 'apps_dashboard'
        self.assertEqual(self.user.action_id.id, self.dashboard_action.id)
        self.user.home_screen_mode = 'default_menu'
        self.assertFalse(self.user.action_id)

    def test_default_menu_keeps_admin_assigned_action(self):
        other_action = self.env['ir.actions.client'].create({'name': 'Other', 'tag': 'app_dashboard.other'})
        self.user.action_id = other_action.id
        self.user.home_screen_mode = 'default_menu'
        self.assertEqual(self.user.action_id.id, other_action.id)

    def test_user_can_choose_own_home_screen(self):
        self.user.with_user(self.user).write({'home_screen_mode': 'apps_dashboard'})
        self.assertEqual(self.user.home_screen_mode, 'apps_dashboard')
        self.assertEqual(self.user.action_id.id, self.dashboard_action.id)

    def test_eligible_apps_follow_menu_groups(self):
        data = self.Users.with_user(self.user).get_app_dashboard_data()
        app_ids = self._app_ids(data)
        self.assertIn(self.open_app.id, app_ids)
        self.assertIn(self.folder_app.id, app_ids)
        self.assertNotIn(self.restricted_app.id, app_ids)
        self.assertNotIn(self.sub_menu.id, app_ids)
        self.assertNotIn(self.dashboard_menu.id, app_ids)

    def test_admin_sees_restricted_app(self):
        admin = self.env.ref('base.user_admin')
        data = self.Users.with_user(admin).get_app_dashboard_data()
        self.assertIn(self.restricted_app.id, self._app_ids(data))

    def test_toggle_favorite(self):
        Users = self.Users.with_user(self.user)
        self.assertTrue(Users.toggle_app_favorite(self.open_app.id))
        self.assertIn(self.open_app, self.user.favorite_app_menu_ids)
        data = Users.get_app_dashboard_data()
        self.assertEqual(data['favorite_ids'], [self.open_app.id])
        app = next(a for a in data['apps'] if a['id'] == self.open_app.id)
        self.assertTrue(app['is_favorite'])
        self.assertFalse(Users.toggle_app_favorite(self.open_app.id))
        self.assertNotIn(self.open_app, self.user.favorite_app_menu_ids)

    def test_cannot_favorite_ineligible_app(self):
        Users = self.Users.with_user(self.user)
        self.assertFalse(Users.toggle_app_favorite(self.restricted_app.id))
        self.assertFalse(Users.toggle_app_favorite(self.sub_menu.id))
        self.assertFalse(self.user.favorite_app_menu_ids)

    def test_stale_favorite_is_hidden_without_error(self):
        self.user.favorite_app_menu_ids = [(4, self.restricted_app.id), (4, self.open_app.id)]
        data = self.Users.with_user(self.user).get_app_dashboard_data()
        self.assertEqual(data['favorite_ids'], [self.open_app.id])
        self.assertNotIn(self.restricted_app.id, self._app_ids(data))
        self.assertIn(self.restricted_app, self.user.favorite_app_menu_ids)

    def test_user_without_apps_gets_empty_list(self):
        portal = new_test_user(self.env, login='app_dash_portal', groups='base.group_portal')
        data = self.Users.with_user(portal).get_app_dashboard_data()
        self.assertEqual(data['apps'], [])
        self.assertEqual(data['favorite_ids'], [])
        self.assertFalse(self.Users.with_user(portal).toggle_app_favorite(self.open_app.id))

    def test_priority_apps_come_first_among_others(self):
        self.env['app_dashboard.priority.app'].create({'menu_id': self.folder_app.id, 'sequence': 10})
        Users = self.Users.with_user(self.user)
        data = Users.get_app_dashboard_data()
        app_ids = self._app_ids(data)
        self.assertEqual(app_ids.index(self.folder_app.id), 0)
        folder_entry = next(a for a in data['apps'] if a['id'] == self.folder_app.id)
        self.assertTrue(folder_entry['is_priority'])

    def test_apps_sorted_by_usage_frequency(self):
        Users = self.Users.with_user(self.user)
        for _ in range(3):
            Users.register_app_open(self.folder_app.id)
        Users.register_app_open(self.open_app.id)
        data = Users.get_app_dashboard_data()
        app_ids = self._app_ids(data)
        self.assertLess(app_ids.index(self.folder_app.id), app_ids.index(self.open_app.id))

    def test_manual_reorder_overrides_default_order(self):
        Users = self.Users.with_user(self.user)
        for _ in range(3):
            Users.register_app_open(self.folder_app.id)
        Users.reorder_apps([self.open_app.id, self.folder_app.id])
        data = Users.get_app_dashboard_data()
        app_ids = self._app_ids(data)
        self.assertLess(app_ids.index(self.open_app.id), app_ids.index(self.folder_app.id))
        self.assertTrue(data['has_manual_order'])

    def test_reorder_ignores_ineligible_app(self):
        Users = self.Users.with_user(self.user)
        Users.reorder_apps([self.restricted_app.id, self.open_app.id])
        tile = self.env['app_dashboard.tile'].search([
            ('user_id', '=', self.user.id), ('menu_id', '=', self.restricted_app.id),
        ])
        self.assertFalse(tile)

    def test_apply_default_home_screen_bulk_updates_users(self):
        self.Users._app_dashboard_apply_default_home_screen('apps_dashboard')
        self.assertEqual(self.user.home_screen_mode, 'apps_dashboard')
        self.assertEqual(self.user.action_id.id, self.dashboard_action.id)
        self.Users._app_dashboard_apply_default_home_screen('default_menu')
        self.assertEqual(self.user.home_screen_mode, 'default_menu')

    def test_demo_favorites_helper_ignores_missing_xmlids(self):
        self.Users._app_dashboard_set_demo_favorites(
            'app_dashboard.nonexistent_user', ['base.menu_administration'])
        user_xmlid = self.user.get_external_id().get(self.user.id)
        if not user_xmlid:
            self.env['ir.model.data'].create({
                'module': 'app_dashboard', 'name': 'test_dash_user',
                'model': 'res.users', 'res_id': self.user.id,
            })
            user_xmlid = 'app_dashboard.test_dash_user'
        self.Users._app_dashboard_set_demo_favorites(
            user_xmlid, ['app_dashboard.no_such_menu', 'base.menu_administration'])
        self.assertEqual(self.user.favorite_app_menu_ids, self.env.ref('base.menu_administration'))

    def test_apply_default_home_screen_skips_portal_users(self):
        portal = new_test_user(self.env, login='app_dash_portal', groups='base.group_portal')
        self.Users._app_dashboard_apply_default_home_screen('apps_dashboard')
        self.assertEqual(self.user.action_id.id, self.dashboard_action.id)
        self.assertNotEqual(portal.action_id.id, self.dashboard_action.id)
        self.Users._app_dashboard_apply_default_home_screen('default_menu')

    def test_priority_app_defaults(self):
        PriorityApp = self.env['app_dashboard.priority.app']
        first = PriorityApp.create({'menu_id': self.open_app.id})
        second = PriorityApp.create({'menu_id': self.folder_app.id})
        self.assertGreater(second.sequence, first.sequence)
        self.assertEqual(first.display_name, self.open_app.display_name)
