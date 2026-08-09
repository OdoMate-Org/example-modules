import logging

from odoo import SUPERUSER_ID, _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

STAGE_SHIP = 'ship'
STAGE_INVOICE_CREATE = 'invoice_create'
STAGE_INVOICE_CONFIRM = 'invoice_confirm'


class AutoFulfillmentError(Exception):
    """Carries the automation stage that failed and the underlying reason."""

    def __init__(self, order, stage, reason):
        self.order_name = order.display_name
        self.warehouse_name = order.warehouse_id.display_name
        self.stage = stage
        self.reason = reason
        super().__init__(reason)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        automated = self.filtered(
            lambda order: order.warehouse_id and order.warehouse_id._has_sale_auto_fulfillment()
        )
        if not automated:
            return super().action_confirm()

        try:
            with self.env.cr.savepoint():
                result = super().action_confirm()
                for order in automated:
                    order._run_auto_fulfillment()
        except AutoFulfillmentError as error:
            self.env.invalidate_all(flush=False)
            self._log_auto_fulfillment_failure(error)
            raise UserError(self._auto_fulfillment_user_message(error)) from error
        return result

    def _run_auto_fulfillment(self):
        self.ensure_one()
        warehouse = self.warehouse_id

        if warehouse.auto_ship:
            try:
                self._auto_fulfillment_validate_delivery()
            except Exception as error:
                raise AutoFulfillmentError(self, STAGE_SHIP, _auto_fulfillment_reason(error)) from error

        invoices = self.env['account.move']
        if warehouse.auto_invoice_create:
            try:
                invoices = self._auto_fulfillment_create_invoice()
            except Exception as error:
                raise AutoFulfillmentError(self, STAGE_INVOICE_CREATE, _auto_fulfillment_reason(error)) from error

        if warehouse.auto_invoice_confirm and invoices:
            try:
                self._auto_fulfillment_post_invoice(invoices)
            except Exception as error:
                raise AutoFulfillmentError(self, STAGE_INVOICE_CONFIRM, _auto_fulfillment_reason(error)) from error

        return invoices

    def _auto_fulfillment_validate_delivery(self):
        self.ensure_one()
        pickings = self.picking_ids.filtered(lambda picking: picking.state not in ('done', 'cancel'))
        if not pickings:
            return pickings

        for move in pickings.move_ids:
            if move.state in ('done', 'cancel'):
                continue
            move.quantity = move.product_uom_qty
            move.picked = True

        result = pickings.with_context(
            skip_backorder=True,
            picking_ids_not_to_backorder=pickings.ids,
            skip_sms=True,
        ).button_validate()
        if isinstance(result, dict) and result.get('type') == 'ir.actions.act_window':
            raise UserError(_(
                "Odoo asked for a manual confirmation step (%(wizard)s) that automatic "
                "shipping cannot answer.",
                wizard=result.get('res_model') or result.get('name') or '',
            ))

        pending = pickings.filtered(lambda picking: picking.state not in ('done', 'cancel'))
        if pending:
            raise UserError(_(
                "The transfer(s) %(pickings)s could not be set to Done automatically.",
                pickings=", ".join(pending.mapped('name')),
            ))
        return pickings

    def _auto_fulfillment_create_invoice(self):
        self.ensure_one()
        if not self._get_invoiceable_lines():
            self.message_post(body=_(
                "Automatic invoicing skipped: there was nothing to invoice on this order "
                "at confirmation time. The order itself was confirmed normally."
            ))
            return self.env['account.move']
        return self._create_invoices()

    def _auto_fulfillment_post_invoice(self, invoices):
        self.ensure_one()
        draft_invoices = invoices.filtered(lambda move: move.state == 'draft')
        if draft_invoices:
            draft_invoices.action_post()
        return invoices

    def _auto_fulfillment_stage_label(self, stage):
        return {
            STAGE_SHIP: _("automatic delivery validation"),
            STAGE_INVOICE_CREATE: _("automatic invoice creation"),
            STAGE_INVOICE_CONFIRM: _("automatic invoice posting"),
        }.get(stage, stage)

    def _auto_fulfillment_user_message(self, error):
        return _(
            "Automatic fulfillment failed for %(order)s on warehouse %(warehouse)s.\n\n"
            "Stage: %(stage)s\n"
            "Reason: %(reason)s\n\n"
            "Nothing was kept: the order stays a quotation, no delivery was validated "
            "and no invoice was created. Fix the reason above and confirm the order again, "
            "or turn the automation off on the warehouse to confirm it manually.",
            order=error.order_name,
            warehouse=error.warehouse_name,
            stage=self._auto_fulfillment_stage_label(error.stage),
            reason=error.reason,
        )

    def _log_auto_fulfillment_failure(self, error):
        message = (
            "Automatic fulfillment failed - order: %s - warehouse: %s - stage: %s - reason: %s"
            % (error.order_name, error.warehouse_name, error.stage, error.reason)
        )
        _logger.warning(message)
        try:
            with self.env.registry.cursor() as log_cr:
                log_env = api.Environment(log_cr, SUPERUSER_ID, {})
                log_env['ir.logging'].create({
                    'name': 'sale_warehouse_auto_fulfillment',
                    'type': 'server',
                    'dbname': self.env.cr.dbname,
                    'level': 'ERROR',
                    'message': message,
                    'path': 'sale_warehouse_auto_fulfillment.models.sale_order',
                    'func': '_run_auto_fulfillment',
                    'line': error.stage,
                })
        except Exception:
            _logger.exception("Could not persist the automatic fulfillment failure in ir.logging.")


def _auto_fulfillment_reason(error):
    return str(error).strip() or error.__class__.__name__
