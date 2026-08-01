from odoo import api, fields, models, _
from odoo.exceptions import UserError

from .odomate_selections import ROUTE_TYPE_SELECTION

MANAGER_GROUP = 'odomate_product_kind.group_odomate_product_kind_manager'


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # Frozen at MO creation; never copied on duplication. Not readonly=True
    # here — immutability for non-managers is enforced by the write() guard
    # below, and the view splits editability by group so a Product Kind
    # Manager can correct the snapshot from the form.
    odomate_product_kind_snapshot_id = fields.Many2one(
        'odomate.product.kind',
        string="Product Kind (Snapshot)",
        copy=False,
        help="Product kind frozen when the manufacturing order was created: "
             "inherited from the originating sale order line when present, "
             "otherwise taken from the product's current kind.",
    )
    odomate_route_type_snapshot = fields.Selection(
        selection=ROUTE_TYPE_SELECTION,
        string="Route Type (Snapshot)",
        compute='_compute_odomate_route_type_snapshot',
        readonly=True,
    )

    @api.depends('odomate_product_kind_snapshot_id.route_type')
    def _compute_odomate_route_type_snapshot(self):
        for production in self:
            production.odomate_route_type_snapshot = \
                production.odomate_product_kind_snapshot_id.route_type or False

    @api.model_create_multi
    def create(self, vals_list):
        productions = super().create(vals_list)
        # Gate 2 — freeze the snapshot once, by priority: sale order line first,
        # then the product's current kind. An explicit value passed in vals
        # (e.g. by a manager or demo data) is respected and not overwritten.
        for production in productions:
            if production.odomate_product_kind_snapshot_id:
                continue
            kind = self.env['odomate.product.kind']
            sale_line = production._odomate_source_sale_line()
            if sale_line and sale_line.odomate_product_kind_snapshot_id:
                kind = sale_line.odomate_product_kind_snapshot_id
            elif sale_line and sale_line.odomate_product_kind_id:
                kind = sale_line.odomate_product_kind_id
            elif production.product_id:
                kind = production.product_id.product_tmpl_id.odomate_product_kind_id
            if kind:
                # No sudo needed: the write() guard below only blocks
                # overwriting an already-set snapshot with a different value;
                # at this point the field is still empty, so the guard's own
                # condition is false regardless of the acting user's group.
                production.odomate_product_kind_snapshot_id = kind.id
        return productions

    def _odomate_source_sale_line(self):
        """Return the originating sale.order.line if the installation links MOs
        to sale lines (field only present with sale_mrp-style bridges)."""
        self.ensure_one()
        if 'sale_line_id' in self._fields:
            return self.sale_line_id
        return self.env['sale.order.line']

    def write(self, vals):
        # Model-level immutability of the snapshot for non-managers.
        if 'odomate_product_kind_snapshot_id' in vals and not self.env.su \
                and not self.env.user.has_group(MANAGER_GROUP):
            new_value = vals['odomate_product_kind_snapshot_id']
            for production in self:
                if production.odomate_product_kind_snapshot_id and \
                        production.odomate_product_kind_snapshot_id.id != new_value:
                    raise UserError(_(
                        "The Product Kind snapshot on a manufacturing order is frozen "
                        "and can only be changed by a Product Kind Manager."
                    ))
        return super().write(vals)
