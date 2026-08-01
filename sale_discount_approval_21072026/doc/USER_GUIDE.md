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
> **€500** yields a uniform **10%** on both lines. Because lines can carry
> different taxes, treat the result as *approximately €500 off*, not exact to
> the cent.

The **Discount** field on the order footer shows the informational total
`Σ(qty × unit price × line discount ÷ 100)`. The line subtotals already reflect
the discount, so this value is for reference only.

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

## Documents & analysis

* A **Discount** row is injected into printed quotations, printed invoices and
  the online portal totals.
* The invoice analysis report (`account.invoice.report`) exposes a **Discount %**
  column for pivot and graph views.

## Field reference

| Model | Field | Meaning |
|-------|-------|---------|
| `sale.order` / `account.move` | `discount_type` | `percent` or `amount` |
| `sale.order` / `account.move` | `discount_rate` | value entered by the user |
| `sale.order` / `account.move` | `amount_discount` | computed informational total |
| `sale.order` | `margin_test` | mirrors `margin` when *Sale Margin* is installed, else 0 |
| `sale.order.line` | `total_discount` | discounted unit value for Amount discounts |
| `res.company` | `so_double_validation` | `one_step` / `two_step` |
| `res.company` | `so_double_validation_limit` | approval threshold in % |

## Known limitations

* Amount discounts are **approximate**, not exact-to-the-cent, when lines carry
  different taxes.
* The approval average is **unweighted** and includes 0% and negative lines.
* `margin_test` is populated only when the **Sale Margin** app is installed.
