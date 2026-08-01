from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError

from odoo.addons.odomate_product_kind import (
    SALE_REPORT_SEARCH_VIEW_MARKER,
    _post_init_hook,
    _uninstall_hook,
)


@tagged('post_install', '-at_install')
class TestOdomateProductKind(TransactionCase):
    """Behaviour of the Product Kind classification and its snapshot chain."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Kind = cls.env['odomate.product.kind']
        cls.root = cls.Kind.create({
            'name': 'Test Finished Goods', 'code': 'T-FG', 'route_type': 'sold',
        })
        cls.child = cls.Kind.create({
            'name': 'Test Furniture', 'code': 'T-FURN', 'route_type': 'manufactured',
            'parent_id': cls.root.id,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})
        cls.product = cls.env['product.template'].create({
            'name': 'Oak Table',
            'odomate_product_kind_id': cls.child.id,
        })

    # ------------------------------------------------------------------
    # odomate.product.kind
    # ------------------------------------------------------------------
    def test_complete_name_compute(self):
        self.assertEqual(self.root.complete_name, 'Test Finished Goods')
        self.assertEqual(self.child.complete_name, 'Test Finished Goods / Test Furniture')

    def test_complete_name_recurses_on_rename(self):
        self.root.name = 'Products'
        self.assertEqual(self.child.complete_name, 'Products / Test Furniture')

    def test_recursion_forbidden(self):
        # Either our @api.constrains ValidationError or Odoo's built-in
        # _parent_store "Recursion Detected" UserError (ValidationError is a
        # UserError subclass, so UserError catches both).
        with self.assertRaises(UserError):
            self.root.parent_id = self.child.id
            self.env.flush_all()

    def test_code_uniqueness_within_company(self):
        company = self.env.company
        self.Kind.create({'name': 'A', 'code': 'DUP', 'route_type': 'other',
                          'company_id': company.id})
        with self.assertRaises(ValidationError):
            self.Kind.create({'name': 'B', 'code': 'DUP', 'route_type': 'other',
                              'company_id': company.id})

    def test_global_code_uniqueness(self):
        self.Kind.create({'name': 'GA', 'code': 'GLOB', 'route_type': 'other',
                          'company_id': False})
        with self.assertRaises(ValidationError):
            self.Kind.create({'name': 'GB', 'code': 'GLOB', 'route_type': 'other',
                              'company_id': False})

    def test_name_uniqueness_same_parent(self):
        with self.assertRaises(ValidationError):
            self.Kind.create({'name': 'Test Furniture', 'route_type': 'other',
                              'parent_id': self.root.id})

    def test_name_allowed_under_different_parent(self):
        other_root = self.Kind.create({'name': 'Other Root', 'route_type': 'other'})
        child = self.Kind.create({'name': 'Test Furniture', 'route_type': 'other',
                                  'parent_id': other_root.id})
        self.assertEqual(child.name, 'Test Furniture')

    def test_sequence_code_uniqueness_within_company(self):
        company = self.env.company
        self.Kind.create({'name': 'SC-A', 'sequence_code': 'SEQDUP',
                          'route_type': 'other', 'company_id': company.id})
        with self.assertRaises(ValidationError):
            self.Kind.create({'name': 'SC-B', 'sequence_code': 'SEQDUP',
                              'route_type': 'other', 'company_id': company.id})

    def test_archive_blocked_with_active_children(self):
        with self.assertRaises(ValidationError):
            self.root.active = False

    def test_archive_leaf_allowed(self):
        leaf = self.Kind.create({'name': 'Leaf', 'route_type': 'service'})
        leaf.active = False
        self.assertFalse(leaf.active)

    def test_counts_over_subtree(self):
        # product is on child; root should count it via child_of subtree.
        self.assertEqual(self.root.product_count, 1)
        self.assertEqual(self.child.product_count, 1)

    # ------------------------------------------------------------------
    # product.template related fields
    # ------------------------------------------------------------------
    def test_product_related_fields(self):
        self.assertEqual(self.product.odomate_route_type, 'manufactured')
        self.assertFalse(self.product.odomate_requires_engineering)

    # ------------------------------------------------------------------
    # sale.order.line snapshot
    # ------------------------------------------------------------------
    def _make_sale_order(self):
        variant = self.product.product_variant_id
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': variant.id,
                'product_uom_qty': 1.0,
            })],
        })

    def test_sale_line_live_link(self):
        order = self._make_sale_order()
        line = order.order_line
        self.assertEqual(line.odomate_product_kind_id, self.child)
        self.assertFalse(line.odomate_product_kind_snapshot_id)

    def test_sale_confirm_freezes_snapshot(self):
        order = self._make_sale_order()
        order.action_confirm()
        line = order.order_line
        self.assertEqual(line.odomate_product_kind_snapshot_id, self.child)

    def test_snapshot_survives_reclassification(self):
        order = self._make_sale_order()
        order.action_confirm()
        line = order.order_line
        # Reclassify the product after confirmation.
        self.product.odomate_product_kind_id = self.root.id
        self.assertEqual(line.odomate_product_kind_id, self.root)
        self.assertEqual(line.odomate_product_kind_snapshot_id, self.child)

    def test_snapshot_immutable_for_non_manager(self):
        order = self._make_sale_order()
        order.action_confirm()
        line = order.order_line
        user = self.env['res.users'].create({
            'name': 'Sales Rep', 'login': 'odomate_rep',
            'group_ids': [(6, 0, [
                self.env.ref('sales_team.group_sale_manager').id,
            ])],
        })
        with self.assertRaises(UserError):
            line.with_user(user).write({
                'odomate_product_kind_snapshot_id': self.root.id,
            })

    def test_snapshot_editable_for_manager(self):
        order = self._make_sale_order()
        order.action_confirm()
        line = order.order_line
        manager = self.env['res.users'].create({
            'name': 'Kind Manager', 'login': 'odomate_mgr',
            'group_ids': [(6, 0, [
                self.env.ref('sales_team.group_sale_manager').id,
                self.env.ref('odomate_product_kind.group_odomate_product_kind_manager').id,
            ])],
        })
        line.with_user(manager).write({
            'odomate_product_kind_snapshot_id': self.root.id,
        })
        self.assertEqual(line.odomate_product_kind_snapshot_id, self.root)

    # ------------------------------------------------------------------
    # mrp.production snapshot
    # ------------------------------------------------------------------
    def test_manual_mo_snapshots_current_kind(self):
        variant = self.product.product_variant_id
        mo = self.env['mrp.production'].create({
            'product_id': variant.id,
            'product_qty': 1.0,
            'product_uom_id': variant.uom_id.id,
        })
        self.assertEqual(mo.odomate_product_kind_snapshot_id, self.child)

    # ------------------------------------------------------------------
    # mrp.bom live link
    # ------------------------------------------------------------------
    def test_bom_kind_computed(self):
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product.id,
            'product_qty': 1.0,
        })
        self.assertEqual(bom.odomate_product_kind_id, self.child)
        # Live link: reclassify product -> BoM follows.
        self.product.odomate_product_kind_id = self.root.id
        self.assertEqual(bom.odomate_product_kind_id, self.root)

    # ------------------------------------------------------------------
    # sale.report search-view hooks (self-healing)
    # ------------------------------------------------------------------
    def _marker_views(self):
        return self.env['ir.ui.view'].search([
            ('model', '=', 'sale.report'),
            ('name', '=', SALE_REPORT_SEARCH_VIEW_MARKER),
        ])

    def test_post_init_hook_is_idempotent(self):
        _post_init_hook(self.env)
        _post_init_hook(self.env)
        self.assertEqual(len(self._marker_views()), 1)

    def test_post_init_hook_repairs_stale_view(self):
        # Odoo validates view arch eagerly on create(), so a genuinely
        # nonexistent field can't be used to simulate a stale copy here.
        # A placeholder arch (valid field, but not our canonical one) still
        # proves the point: the hook must replace ANY existing marker view
        # rather than short-circuit on "a view with this name exists" — that
        # short-circuit was the original bug that let a stale/orphaned copy
        # survive indefinitely.
        base_view = self.env['ir.ui.view'].search([
            ('model', '=', 'sale.report'),
            ('type', '=', 'search'),
            ('inherit_id', '=', False),
        ], limit=1, order='priority')
        self.env['ir.ui.view'].create({
            'name': SALE_REPORT_SEARCH_VIEW_MARKER,
            'model': 'sale.report',
            'inherit_id': base_view.id,
            'arch': '''<?xml version="1.0"?>
<data>
    <xpath expr="//search" position="inside">
        <field name="partner_id"/>
    </xpath>
</data>''',
        })
        _post_init_hook(self.env)
        views = self._marker_views()
        self.assertEqual(len(views), 1)
        self.assertIn('odomate_product_kind_id', views.arch)
        self.assertIn('group_odomate_route_type', views.arch)

    def test_uninstall_hook_removes_view(self):
        _post_init_hook(self.env)
        self.assertEqual(len(self._marker_views()), 1)
        _uninstall_hook(self.env)
        self.assertEqual(len(self._marker_views()), 0)
