import logging

from . import models

_logger = logging.getLogger(__name__)

# Shared by both hooks so install/upgrade and uninstall can never drift out
# of sync on the marker string used to identify our injected view.
SALE_REPORT_SEARCH_VIEW_MARKER = 'sale.report.search.odomate.product.kind'


def _post_init_hook(env):
    """Attach the Product Kind / Route Type group-by and filter fields to the
    Sales Analysis (sale.report) search view.

    The core search view's technical XML ID is not stable across Odoo
    versions/branches, so it is located dynamically (the base, non-inherited
    search view for the model) instead of via a hardcoded external ID.

    Idempotent delete-then-recreate: Odoo calls post_init_hook on every
    install AND every subsequent upgrade, so this always drops any existing
    copy first before re-creating it fresh. That makes the hook self-healing
    — a copy left stale or orphaned by a prior broken uninstall (referencing
    fields that no longer exist) is wiped and replaced rather than merely
    skipped, and re-running the hook never accumulates duplicates.
    """
    View = env['ir.ui.view']
    View.search([
        ('model', '=', 'sale.report'),
        ('name', '=', SALE_REPORT_SEARCH_VIEW_MARKER),
    ]).unlink()
    base_view = View.search([
        ('model', '=', 'sale.report'),
        ('type', '=', 'search'),
        ('inherit_id', '=', False),
    ], limit=1, order='priority')
    if not base_view:
        _logger.warning(
            "odomate_product_kind: no base search view found for sale.report; "
            "skipping the Product Kind / Route Type search-view patch."
        )
        return
    View.create({
        'name': SALE_REPORT_SEARCH_VIEW_MARKER,
        'model': 'sale.report',
        'inherit_id': base_view.id,
        'arch': '''<?xml version="1.0"?>
<data>
    <xpath expr="//search" position="inside">
        <field name="odomate_product_kind_id"/>
        <field name="odomate_route_type"/>
        <filter name="group_odomate_product_kind" string="Product Kind"
                context="{'group_by': 'odomate_product_kind_id'}"/>
        <filter name="group_odomate_route_type" string="Route Type"
                context="{'group_by': 'odomate_route_type'}"/>
    </xpath>
</data>''',
    })


def _uninstall_hook(env):
    """Remove the injected sale.report search-view patch before this
    module's own fields (odomate_product_kind_id, odomate_route_type) are
    dropped, so uninstalling never leaves an orphaned view behind that
    references fields which no longer exist."""
    env['ir.ui.view'].search([
        ('model', '=', 'sale.report'),
        ('name', '=', SALE_REPORT_SEARCH_VIEW_MARKER),
    ]).unlink()
