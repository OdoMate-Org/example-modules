from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    odomate_product_kind_id = fields.Many2one(
        'odomate.product.kind',
        string="Product Kind",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        index=True,
        help="Manufacturing classification of this product. A live link — "
             "changing it reclassifies the product and its BoM immediately, but "
             "already-confirmed sales and manufacturing documents keep their snapshot.",
    )

    # Read-only derived attributes for display (non-stored related fields).
    odomate_route_type = fields.Selection(
        related='odomate_product_kind_id.route_type',
        string="Route Type", readonly=True,
    )
    odomate_manufacturing_mode = fields.Selection(
        related='odomate_product_kind_id.manufacturing_mode',
        string="Manufacturing Mode", readonly=True,
    )
    odomate_requires_engineering = fields.Boolean(
        related='odomate_product_kind_id.requires_engineering',
        string="Requires Engineering", readonly=True,
    )
    odomate_requires_team_planning = fields.Boolean(
        related='odomate_product_kind_id.requires_team_planning',
        string="Requires Team Planning", readonly=True,
    )
