# Sale Discount Approval — User Guide

## Overview

**Sale Discount Approval** lets you apply a single discount to an entire sale
order or customer invoice — as a **Percent** or a fixed **Amount** — and spread
it evenly across every line. Large discounts can optionally be routed to a
**Sales Manager** for approval before the order is confirmed.

## Prerequisites

The discount fields are only visible when the standard Odoo **Discounts**
feature is enabled:

> **Settings → Sales → Pricing → Discounts** (*Discount per line*,
> `sale.group_discount_per_so_line`).

If this group is off, the discount inputs described below stay hidden.

## Configuration

1. Go to **Settings → Sales**.
2. In the **Pricing** block enable **Sale Discount Approval**.
3. Set **Discount Approval Limit (%)** — the average line-discount threshold
   above which an order needs manager approval (for example `15`).
4. Save.

Internally this maps to the company fields `so_double_validation`
(`one_step` / `two_step`) and `so_double_validation_limit`.

## Applying an order-level discount

On a quotation (`Sales → Orders → Quotations`):

1. Pick a **Discount Type** — `Percent` or `Amount`.
2. Enter a **Discount Rate**.
   * **Percent** — every line's `discount` is set to that percentage directly.
   * **Amount** — the amount is converted to a uniform percentage
     `rate ÷ (Σ qty × unit price) × 100` and applied to every line.
3. The fan-out runs automatically on change; you can also click the
   **(update)** link (draft/sent only) to re-run it.

> **Worked example (Amount).** An order of two lines — 10 × €300 (=€3,000) and
> 20 × €100 (=€2,000), total **€5,000** — with an **Amount** discount of
> **€500** yields a uniform **10%** on both lines. The **per-line** percentage
> is rounded to 2 decimals, so an individual line's discounted subtotal can be
> off by a few cents from a perfectly even split — treat each line as
> *approximately* its share, not exact to the cent.

The **Discount** field on the order footer shows the informational total. For
an **Amount**-type discount with at least one discountable line, it always
equals the **Discount Rate** you entered exactly (e.g. entering **€700**
always shows **Discount: €700.00**, even though the per-line percentage that
achieves it is rounded). For a **Percent**-type discount it is computed as
`Σ(qty × unit price × line discount ÷ 100)`, which is already exact since the
percentage is applied to lines unconverted. If the order has no discountable
lines (or they total zero), the Discount field shows **0.00** regardless of
the entered rate, since nothing was actually discounted yet. The line
subtotals already reflect the discount, so this field is for reference only.

### Surcharges

A **negative** Discount Rate is allowed and behaves as a price increase
(surcharge), fanned out the same way. No validation blocks negative values.

### Pricelist interaction

Applying the order-level discount **overwrites** any discount the pricelist had
computed on each line. There is no merge — the manual input always wins once
applied.

## The approval gate

When **two-step** approval is active, confirming an order compares the
**unweighted average of all order-line discounts** (including 0% and negative
lines) against the limit:

* **average ≤ limit** — the order confirms normally.
* **average > limit** — the order moves to **Waiting Approval** and confirmation
  is halted.

From a *Waiting Approval* order, a **Sales Manager** (`sales_team.group_sale_manager`)
sees two buttons:

* **Approve** — confirms the order through the standard flow.
* **Reject** — sends the order back to **Draft** for revision.

Both actions are enforced on the server, not just hidden in the UI: calling
either one as a user outside `sales_team.group_sale_manager` (e.g. over RPC)
is rejected with an access error, and each only acts on orders actually in
**Waiting Approval** — calling **Approve** on an order that never reached that
state (still **Draft**) leaves it untouched rather than confirming it.

> **Edge case — average dilution.** Because 0% and negative lines are included
> unweighted, a single steeply-discounted line can be diluted below the limit.
> Example: one line at **25%** and one surcharge line at **−20%** average to
> **2.5%**, so the order confirms without approval. This is the confirmed
> business rule, not a defect.

## Invoices

* Invoice lines accept the same **Discount Type** / **Discount Rate** inputs
  (in *Other Info*, before the notes), fanned out over `invoice_line_ids`.
* When an order is invoiced, its discount type, rate and amount are copied onto
  the invoice so it starts pre-populated.
* A zero-total guard prevents any division-by-zero on an empty invoice.
* The invoice's **Discount** total follows the same rule as the order footer:
  exact to the entered **Discount Rate** for Amount-type discounts, computed
  from line percentages for Percent-type, and **0.00** when there are no
  discountable lines.

## Documents & analysis

* A **Discount** row is injected into printed quotations, printed invoices and
  the online portal totals.
* The invoice analysis report (`account.invoice.report`) exposes a **Discount %**
  column for pivot and graph views.
* Sales Analysis (`sale.report`) exposes the same **Discount %** measure for
  quotations and orders — open **Sales → Reporting → Sales**, switch to pivot
  or graph, and add **Discount %** to see it alongside the standard measures.

## Field reference

| Model | Field | Meaning |
|-------|-------|---------|
| `sale.order` / `account.move` | `discount_type` | `percent` or `amount` |
| `sale.order` / `account.move` | `discount_rate` | value entered by the user |
| `sale.order` / `account.move` | `amount_discount` | computed informational total — exact to `discount_rate` for Amount-type, computed from lines for Percent-type |
| `sale.order` | `margin_test` | mirrors `margin` when *Sale Margin* is installed, else 0 |
| `sale.order.line` | `total_discount` | discounted unit value for Amount discounts |
| `res.company` | `so_double_validation` | `one_step` / `two_step` |
| `res.company` | `so_double_validation_limit` | approval threshold in % |

## Known limitations

* For Amount-type discounts, individual **line** discount percentages are
  rounded to 2 decimals, so a single line's discounted subtotal can be off by
  a few cents from a perfectly even split. The order/invoice **Discount**
  footer total itself is exact to the entered amount — only the per-line
  breakdown is approximate.
* The approval average is **unweighted** and includes 0% and negative lines.
* `margin_test` is populated only when the **Sale Margin** app is installed.
