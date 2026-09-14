from odoo.tests import TransactionCase, tagged

FULL_LIST = {"ir.ui.menu.full_list": True}

SUITE_ROOT = "odomate_hr_bundle.menu_odomate_hr_suite_root"
SUITE_CONFIG = "odomate_hr_bundle.menu_odomate_hr_suite_config"

SUITE_ROOT_CHILDREN = [
    "odomate_hr_documents.menu_odomate_hr_documents_root",
    "odomate_hr_custody.menu_odomate_hr_custody_root",
    "odomate_hr_notices.menu_odomate_hr_notices_root",
    "odomate_hr_transfer.menu_odomate_hr_transfer",
    "odomate_hr_resignation.menu_odomate_hr_resignation_root",
    "odomate_hr_dashboard.menu_hr_overview_analysis",
]

SUITE_CONFIG_CHILDREN = [
    "odomate_hr_employee_info_06092026_2.odomate_hr_relationship_menu",
    "odomate_hr_notices.menu_odomate_hr_announcement_category",
    "odomate_hr_resignation.menu_odomate_hr_clearance_item",
    "odomate_hr_notices.menu_odomate_hr_reminder",
]


@tagged("post_install", "-at_install")
class TestOdomateHrBundleMenus(TransactionCase):
    """Install-time structure tests for the HR Suite menu arrangement."""

    def _menu(self, xmlid):
        return self.env.ref(xmlid).with_context(**FULL_LIST)

    def _child_xmlids(self, folder):
        data = self.env["ir.model.data"].sudo()
        names = []
        for child in folder.child_id:
            record = data.search(
                [("model", "=", "ir.ui.menu"), ("res_id", "=", child.id)], limit=1
            )
            names.append("%s.%s" % (record.module, record.name))
        return names

    def test_suite_root_folder_definition(self):
        folder = self._menu(SUITE_ROOT)
        self.assertEqual(folder.name, "HR Suite")
        self.assertEqual(folder.parent_id, self.env.ref("hr.menu_hr_root"))
        self.assertEqual(folder.sequence, 35)
        self.assertFalse(folder.action)
        self.assertFalse(folder.group_ids)

    def test_suite_config_folder_definition(self):
        folder = self._menu(SUITE_CONFIG)
        self.assertEqual(folder.name, "HR Suite")
        self.assertEqual(
            folder.parent_id, self.env.ref("hr.menu_human_resources_configuration")
        )
        self.assertEqual(folder.sequence, 90)
        self.assertFalse(folder.action)
        self.assertFalse(folder.group_ids)

    def test_suite_root_has_exactly_six_children_in_order(self):
        folder = self._menu(SUITE_ROOT)
        self.assertEqual(len(folder.child_id), 6)
        self.assertEqual(self._child_xmlids(folder), SUITE_ROOT_CHILDREN)
        self.assertEqual(
            folder.child_id.mapped("sequence"), [10, 20, 30, 40, 50, 60]
        )

    def test_suite_config_has_exactly_four_children_in_order(self):
        folder = self._menu(SUITE_CONFIG)
        self.assertEqual(len(folder.child_id), 4)
        self.assertEqual(self._child_xmlids(folder), SUITE_CONFIG_CHILDREN)
        self.assertEqual(folder.child_id.mapped("sequence"), [10, 20, 30, 40])

    def test_no_folder_is_empty(self):
        for xmlid in (SUITE_ROOT, SUITE_CONFIG):
            self.assertTrue(
                self._menu(xmlid).child_id,
                "HR Suite folder %s must not be empty" % xmlid,
            )

    def test_no_duplicate_top_level_entries(self):
        employees = self._menu("hr.menu_hr_root")
        top_level = employees.child_id
        self.assertEqual(
            len(top_level.filtered(lambda m: m == self._menu(SUITE_ROOT))), 1
        )
        for xmlid in SUITE_ROOT_CHILDREN:
            self.assertNotIn(
                self.env.ref(xmlid).id,
                top_level.ids,
                "%s must sit under HR Suite, not directly under Employees" % xmlid,
            )

    def test_config_entries_left_hr_configuration_top_level(self):
        configuration = self._menu("hr.menu_human_resources_configuration")
        for xmlid in SUITE_CONFIG_CHILDREN:
            self.assertNotIn(
                self.env.ref(xmlid).id,
                configuration.child_id.ids,
                "%s must sit under the Configuration HR Suite folder" % xmlid,
            )

    def test_member_menus_keep_their_own_identity(self):
        for xmlid in SUITE_ROOT_CHILDREN + SUITE_CONFIG_CHILDREN:
            menu = self._menu(xmlid)
            self.assertTrue(menu.name, "%s lost its own label" % xmlid)
            self.assertTrue(menu.active, "%s was deactivated" % xmlid)

    def test_bundle_owns_only_menu_records(self):
        owned = self.env["ir.model.data"].sudo().search(
            [("module", "=", "odomate_hr_bundle")]
        )
        self.assertTrue(owned)
        self.assertEqual(set(owned.mapped("model")), {"ir.ui.menu"})

    def test_bundle_ships_no_access_rules_or_groups(self):
        data = self.env["ir.model.data"].sudo()
        for model in ("ir.model.access", "ir.rule", "res.groups"):
            self.assertFalse(
                data.search_count(
                    [("module", "=", "odomate_hr_bundle"), ("model", "=", model)]
                ),
                "odomate_hr_bundle must not ship %s records" % model,
            )
