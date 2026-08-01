# SPEC.md — the business specification this module was generated from

This is the finalized specification produced during the OdoMate refinement
conversation, verbatim. The module in this folder was generated from it —
code, views, security, demo data, tests, and the user guide in `doc/` —
and published after human security review, unedited apart from publication
metadata (store banner reference).

Generated with OdoMate (https://www.odomate.pro) — July 2026, Odoo 19 Community.

---

## Module: sale_discount_approval
Apply a single order-level or invoice-level discount (percent or fixed amount) that fans out to all lines, with an optional company-level approval gate for large discounts.

### Models
- **sale.order** (inherited): discount_type (Selection: percent/amount, default percent), discount_rate (Float, digits (16,2)), amount_discount (Monetary, computed `_amount_all`, stored, readonly), amount_untaxed/amount_tax/amount_total (Monetary, computed `_amount_all` override, stored, readonly), state (Selection extended with `waiting` = "Waiting Approval", inserted between `sent` and `sale`), margin_test (Float, computed, mirrors `margin` when `sale_margin` is installed, else False)
  - Relations: One2many order_line (existing, reused)
  - Computed fields: `_amount_all` override drives amount_discount + standard totals; `margin_test` conditional on sale_margin

- **sale.order.line** (inherited): discount (Float — redefined; no longer solely pricelist-driven, also written by the order-level input, which overwrites any pricelist-computed value when applied), total_discount (Float, stored, holds the discounted unit value for Amount-type discounts)
  - Relations: Many2one order_id (existing)

- **account.move** (inherited): discount_type (Selection: percent/amount, default percent), discount_rate (Float, digits (16,2)), amount_discount (Monetary, computed `_compute_amount` override, stored, readonly)
  - Relations: One2many invoice_line_ids (existing, reused)

- **account.move.line** (inherited): discount (Float — redefined, written by the invoice-level input, overwrites any pricelist-derived value)

- **res.company** (inherited): so_double_validation (Selection: one_step/two_step, default one_step), so_double_validation_limit (Float, discount % threshold)

- **res.config.settings** (inherited): so_order_approval (Boolean, UI toggle; `set_values` maps it to company_id.so_double_validation), so_double_validation (Selection, related to company_id), so_double_validation_limit (Float, related to company_id)

### Business Rules
- **Order-level apply** (onchange on discount_type/discount_rate/order_line, and via the (update) link / button_dummy):
  - Percent: every line's `discount` is set to `discount_rate` directly.
  - Amount: converted to a uniform percentage — `discount_rate / (Σ qty × unit price) × 100` — written to every line's `discount`; `total_discount` set to the discounted unit value. Guarded against a zero order total (no division by zero).
  - **Rounding rule (confirmed)**: approximate is acceptable — a uniform percentage across lines means the resulting total may not equal the entered amount to the cent when lines carry different taxes; documented as "approximately €X off," not exact.
- **Order totals**: `_amount_all` override additionally computes `amount_discount = Σ(qty × unit price × line.discount / 100)`. Informational only — the discount is already reflected in each line's subtotal.
- **Invoice-level apply**: same percent/amount logic runs over `invoice_line_ids` via an onchange. A zero-total guard is added here too (the source spec lacked one; added per standard defensive practice so an empty/zero invoice can't divide by zero).
- **Discount carried to invoice** (`_prepare_invoice`): discount_type, discount_rate, and amount_discount are copied onto the invoice values so it starts pre-populated with the order's discount.
- **Pricelist interaction (confirmed)**: if pricelist-based automatic line discounts are active, applying the order-level discount overwrites whatever discount the pricelist had computed on each line — the manual order-level input always wins once applied.
- **Negative discounts (confirmed)**: discount_rate accepts negative values on both sale.order and account.move, functioning as a surcharge (price increase) fanned out the same way as a positive discount. No validation blocks negative values.
- **Approval gate**:
  - On `action_confirm`: if company `so_double_validation == 'two_step'` and the **average of ALL order line discounts** (confirmed: includes 0%-discount lines and negative/surcharge lines in the average, unweighted) exceeds `so_double_validation_limit`, state is set to `waiting` and confirmation is halted. Otherwise confirmation proceeds via `super()`.
  - Edge case to note: because the average includes 0% and negative lines, a mix of a large discount and a surcharge (or several undiscounted lines) can dilute the average below the limit even though one line is steeply discounted — accepted as the confirmed business rule, not a bug.
  - `action_approve` (Sales Manager only, `sales_team.group_sale_manager`): visible only when state is `waiting`; proceeds with standard confirmation logic.
  - `action_reject` (Sales Manager only): visible only when state is `waiting`; sends the order back to `draft` for the salesperson to revise.

### Views & UX
- **sale.order form** (inherit `sale.view_order_form`): Approve and Reject buttons placed before the state widget, both manager-only and visible only when state = waiting; totals/footer group extended with discount_type + discount_rate (visible only under `sale.group_discount_per_so_line`), an amount_discount line, and margin_test (shown only if sale_margin installed); an (update) link (`button_dummy`) visible in draft/sent to re-trigger the fan-out; line discount column forced to 2 decimal digits; hidden total_discount field on the line.
- **account.move form** (inherit `account.view_move_form`): line discount column forced to 2 digits; amount_discount shown read-only just after the tax totals; a discount_type + discount_rate group placed before the narration field.
- **res.config.settings form** (inherit `sale.res_config_settings_view_form`): "Sale Discount Approval" toggle inside the Pricing block; enabling it reveals the so_double_validation_limit input.
- **QWeb reports/portal**: inherits `sale.report_saleorder_document`, `account.report_invoice_document`, `sale.sale_order_portal_content_totals_table`, and `account.document_tax_totals_template` to inject a Discount row into the totals table on printed and portal documents; per-line discount rendered to 2 decimals.
- **Analysis**: `sale.report` and `account.invoice.report` gain a discount column for pivot/graph views.
- OWL complexity: none — all standard field widgets, buttons, and QWeb inheritance; no custom client actions.
- Responsive/mobile: relies on standard Odoo form/list responsiveness; no custom handling needed.

### Security
- No new models → no new `ir.model.access.csv` entries.
- UI-level gating only:
  - Approve / Reject buttons and the approval workflow: restricted to `sales_team.group_sale_manager`.
  - Discount inputs (discount_type/discount_rate on both order and invoice): restricted to `sale.group_discount_per_so_line`.
- **Prerequisite**: the entire discount feature is invisible unless Settings → Sales → Discounts (`sale.group_discount_per_so_line`) is enabled — call this out to whoever configures the environment.
- Multi-company: so_double_validation / so_double_validation_limit live directly on res.company, so no additional company record rule is needed beyond the existing company scoping of res.company itself.

### Demo Data
- 1 `res.company` config demo record: `so_double_validation = 'two_step'`, `so_double_validation_limit = 15.0` (so the approval scenario is reachable out of the box).
- 4-5 `sale.order` demo records covering:
  - 1 quotation with a 10% order-level Percent discount, confirmed normally (average 10% < 15% limit).
  - 1 quotation with mixed line prices and a fixed Amount discount (e.g. €500 off a €5,000 order), showing the approximate-rounding behavior.
  - 1 quotation with a 20% order-level discount that lands in "Waiting Approval" after confirm is attempted (average > 15% limit).
  - 1 order in "Waiting Approval" ready to demo both the Approve (by a Sales Manager demo user) and Reject (back to draft) paths.
  - 1 order mixing a discounted line and a negative (surcharge) line, to demonstrate the average-dilution edge case.
- 1-2 `account.move` demo invoices generated from a discounted order, showing the discount carried over automatically.

### Constraints & Notes
- Amount-type discount is approximate, not exact-to-the-cent, by confirmed design (§ rounding rule) — document this for end users so "€500 off" is understood as "approximately €500."
- Order-level discount overwrites pricelist-computed line discounts on apply; there is no "merge" or "max of the two" behavior.
- Negative discount_rate (surcharge) is permitted at both order and invoice level with no floor validation.
- Approval-gate average is computed across all order lines unweighted (0% and negative lines included), which can mask a single deeply-discounted line — accepted trade-off per confirmed business rule, not treated as a defect.
- margin_test is a soft-dependency field: populated only when `sale_margin` is installed; otherwise always False, and the footer should hide it in that case.
- Invoice-side zero-total division guard added proactively (not in the original notes) to prevent a crash on an empty/zero invoice — treated as a baseline correctness fix rather than an open question.
