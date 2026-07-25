from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    # Live link (no snapshot) — used only for filtering and the counter on the
    # Product Kind card. Recomputed whenever the product's kind changes.
    odomate_product_kind_id = fields.Many2one(
        'odomate.product.kind',
        string="Product Kind",
        compute='_compute_odomate_product_kind_id',
        store=True,
        readonly=True,
    )

    @api.depends(
        'product_id.product_tmpl_id.odomate_product_kind_id',
        'product_tmpl_id.odomate_product_kind_id',
    )
    def _compute_odomate_product_kind_id(self):
        for bom in self:
            if bom.product_id:
                bom.odomate_product_kind_id = bom.product_id.product_tmpl_id.odomate_product_kind_id
            else:
                bom.odomate_product_kind_id = bom.product_tmpl_id.odomate_product_kind_id
