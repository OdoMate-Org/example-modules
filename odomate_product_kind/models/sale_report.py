from odoo import fields, models

from .odomate_selections import ROUTE_TYPE_SELECTION


class SaleReport(models.Model):
    _inherit = 'sale.report'

    # Snapshot-first, live-fallback: a confirmed line already has
    # odomate_product_kind_snapshot_id frozen, so the report reflects the
    # kind as it was at confirmation time, exactly like the Sale Order line
    # itself. A draft/quotation line has no snapshot yet, so it falls back to
    # the product's current (live) kind.
    odomate_product_kind_id = fields.Many2one(
        'odomate.product.kind', string="Product Kind", readonly=True,
    )
    odomate_route_type = fields.Selection(
        selection=ROUTE_TYPE_SELECTION, string="Route Type", readonly=True,
    )

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['odomate_product_kind_id'] = (
            "COALESCE(l.odomate_product_kind_snapshot_id, l.odomate_product_kind_id)"
        )
        res['odomate_route_type'] = """(
            SELECT k.route_type FROM odomate_product_kind k
            WHERE k.id = COALESCE(l.odomate_product_kind_snapshot_id, l.odomate_product_kind_id)
        )"""
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += """,
            l.odomate_product_kind_id,
            l.odomate_product_kind_snapshot_id"""
        return res
