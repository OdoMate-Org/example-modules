from odoo import api, fields, models, _
from odoo.exceptions import UserError

from .odomate_selections import ROUTE_TYPE_SELECTION

MANAGER_GROUP = 'odomate_product_kind.group_odomate_product_kind_manager'


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        # Gate 1 — freeze the product kind snapshot on every line that does not
        # yet have one. Already-frozen lines are never recomputed, even if the
        # order is reset to draft and confirmed again.
        for order in self:
            for line in order.order_line:
                if not line.odomate_product_kind_snapshot_id and line.odomate_product_kind_id:
                    # Empty -> value is always allowed by the write guard.
                    line.odomate_product_kind_snapshot_id = line.odomate_product_kind_id.id
        return super().action_confirm()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Live link up to confirmation.
    odomate_product_kind_id = fields.Many2one(
        'odomate.product.kind',
        string="Product Kind",
        related='product_id.product_tmpl_id.odomate_product_kind_id',
        store=True,
        readonly=True,
    )
    # Frozen at action_confirm(); never copied on duplication. Not
    # readonly=True here — immutability for non-managers is enforced by the
    # write() guard below, and the views split editability by group so a
    # Product Kind Manager can correct the snapshot from the form.
    odomate_product_kind_snapshot_id = fields.Many2one(
        'odomate.product.kind',
        string="Product Kind (Snapshot)",
        copy=False,
        help="Product kind frozen at sales-order confirmation. Only a Product "
             "Kind Manager may change it once set.",
    )
    odomate_route_type_snapshot = fields.Selection(
        selection=ROUTE_TYPE_SELECTION,
        string="Route Type (Snapshot)",
        compute='_compute_odomate_route_type_snapshot',
        readonly=True,
    )

    @api.depends('odomate_product_kind_snapshot_id.route_type')
    def _compute_odomate_route_type_snapshot(self):
        for line in self:
            line.odomate_route_type_snapshot = \
                line.odomate_product_kind_snapshot_id.route_type or False

    def write(self, vals):
        # Model-level immutability of the snapshot (a view readonly alone would
        # be bypassed by direct ORM/import writes).
        if 'odomate_product_kind_snapshot_id' in vals and not self.env.su \
                and not self.env.user.has_group(MANAGER_GROUP):
            new_value = vals['odomate_product_kind_snapshot_id']
            for line in self:
                if line.odomate_product_kind_snapshot_id and \
                        line.odomate_product_kind_snapshot_id.id != new_value:
                    raise UserError(_(
                        "The Product Kind snapshot on a confirmed sale order line is "
                        "frozen and can only be changed by a Product Kind Manager."
                    ))
        return super().write(vals)
