# SPEC.md — the business specification this module was generated from

This is the finalized specification produced during the OdoMate refinement
conversation, verbatim. The module in this folder was generated from it —
code, views, security, demo data, tests, and the user guide in `doc/` —
and published after human security review, unedited apart from publication
metadata (store banner reference).

Generated with OdoMate (https://www.odomate.pro) — August 2026, Odoo 19 Community.

---

## Module: sale_warehouse_auto_fulfillment
Per-warehouse automatic shipping, invoice creation, and invoice confirmation triggered by a single Sales Order confirmation.

### Models
- **stock.warehouse** (extended): auto_ship (Boolean, default False), auto_invoice_create (Boolean, default False), auto_invoice_confirm (Boolean, default False)
  - No new relations; fields live on the existing warehouse record, displayed next to the warehouse's short code (`code`).

- **sale.order** (extended, method override only, no new fields): overrides `action_confirm()`.
  - No new persisted fields. Reads `warehouse_id.auto_ship`, `warehouse_id.auto_invoice_create`, `warehouse_id.auto_invoice_confirm` at confirmation time.

- **ir.logging** (reused, not extended): automation failures are written here through a separate database cursor/transaction so the entry survives the rollback described below.

### Business Rules
- State flow unchanged: draft/sent -> sale -> (done). Automation is chained onto the existing `action_confirm()` transition, not a new state machine.
- Execution order on confirm, when warehouse flags are set: (1) standard order confirmation, (2) if `auto_ship`: validate the order's delivery in full — all lines, full ordered quantity, no backorder, no stock-availability check (negative stock allowed by design) — (3) if `auto_invoice_create`: run standard invoice creation, respecting each product's own invoicing policy (ordered vs. delivered quantities) exactly as the manual "Create Invoice" button does — (4) if `auto_invoice_confirm` AND an invoice was actually created in step 3: post that invoice.
- **"Nothing to invoice" is not a failure.** If step 3 produces zero invoiceable lines (e.g. a delivered-quantity-policy product with `auto_ship` off), invoicing is skipped silently, a note is added to the order's chatter, and the confirmation proceeds/succeeds normally.
- **`auto_invoice_confirm` has no independent effect.** It only posts an invoice that this same automation run just created. If `auto_invoice_create` is off, `auto_invoice_confirm` does nothing (there is nothing to confirm).
- **Failure handling (real errors only — delivery validation error, invoice creation error, invoice posting error):** the entire automation, including the order's state change to confirmed, runs inside one database savepoint. On any real error: roll back the savepoint completely (order reverts to quotation, no delivery, no invoice — nothing half-done), write a failure record to `ir.logging` via an independent cursor (so it survives the rollback), then raise a blocking `UserError` naming the stage that failed and the underlying reason (e.g. "Invoice could not be posted: customer has no receivable account") instead of the raw traceback.
- Serial/lot-tracked products are out of scope: if automatic delivery validation cannot complete because a lot/serial is required, this is treated as a real failure (full rollback + blocking message), not a silent skip.
- No per-order override and no exceptions list — every quotation confirmed from an automatic warehouse is automated the same way, no exceptions (explicit user decision).
- With all three warehouse flags off, `action_confirm()` behaves exactly as standard Odoo — the override is a no-op pass-through.

### Views & UX
- Form view (stock.warehouse, inherited): three checkboxes added next to the warehouse `code` field — "Ship Automatically", "Create Invoice Automatically", "Confirm Invoice Automatically".
- No changes to the Sales Order form, list, or Confirm button — automation runs invisibly behind the existing action. After confirm: delivery shows Done, invoice smart-button count increases, invoice shows Posted (or the order stays a quotation with a blocking error if something failed).
- No new menus, screens, wizards, or reports.
- OWL complexity: none — pure server-side Python logic on an existing method.
- No mobile-specific considerations (standard responsive form view).

### Security
- No new groups or access levels. Reuses existing Inventory (warehouse edit) and Sales (order confirm) permissions.
- No new ir.model.access.csv rows required — only existing models (stock.warehouse, sale.order) gain fields/method overrides; ir.logging already has its standard access.
- No new record rules; multi-company behavior follows the existing warehouse/order company scoping already in Odoo.

### Demo Data
- 2 warehouses: "Main Warehouse" (code WH) — all three flags ON; "Project Warehouse" (code PROJ) — all three flags OFF.
- 3 demo products: "Standard Widget" and "Office Chair" (in-stock, invoice policy = Ordered Quantities, sufficient on-hand qty for the happy-path scenarios), plus "Custom Fixture" (invoice policy = Delivered Quantities, used to demonstrate the silent-skip case when only `auto_invoice_create` is on).
- 5–6 draft quotations pre-created and ready to confirm, covering: (1) all flags on — full auto flow, (2) ship-only, (3) invoice-create-only (including one using "Custom Fixture" to show the silent skip), (4) all flags off on Project Warehouse — manual baseline, (5) an order for a product with zero on-hand stock on Main Warehouse — demonstrates negative-stock auto-shipment.

### Constraints & Notes
- No partial shipping: automatic delivery is always all-or-nothing for the whole order.
- No stock-availability check on automatic shipment — negative stock is intended behavior; only enable `auto_ship` on warehouses with trusted stock figures.
- No invoice emailing — invoices are posted, never sent.
- No log/report UI for automation history in the order itself; auditability is via `ir.logging` only (developer-facing), since a rolled-back order shows no trace of the attempt.
- Setting is strictly per warehouse; there is no per-order override or exception list.
