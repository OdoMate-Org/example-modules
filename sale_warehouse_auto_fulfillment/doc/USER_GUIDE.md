# Sale Warehouse Auto Fulfillment — User Guide

## Table of contents

1. [What this module does](#1-what-this-module-does)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration)
4. [Daily use](#4-daily-use)
5. [The three switches in detail](#5-the-three-switches-in-detail)
6. [What happens when something fails](#6-what-happens-when-something-fails)
7. [Demo data walkthrough](#7-demo-data-walkthrough)
8. [Field reference](#8-field-reference)
9. [Limitations](#9-limitations)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. What this module does

Confirming a quotation in standard Odoo creates a delivery order and stops
there. Somebody then has to open the transfer, click **Validate**, go back to
the order, click **Create Invoice**, open the draft invoice and click
**Confirm** — four extra clicks and three screens for an order that never
needed a human decision.

This module adds three checkboxes to the warehouse form. When they are on,
pressing **Confirm** on a sales order that ships from that warehouse also:

1. validates the delivery in full,
2. creates the customer invoice,
3. posts that invoice.

Nothing else in the Sales app changes. There is no new menu, no new screen, no
new button and no new model — the automation runs invisibly behind the existing
**Confirm** button.

The setting is **strictly per warehouse**. There is no per-order override and no
exception list: every quotation confirmed from an automatic warehouse is
automated the same way.

## 2. Installation

1. Copy the `sale_warehouse_auto_fulfillment` folder into your Odoo addons path.
2. In Odoo, go to **Apps**, click **Update Apps List**, then search for
   *Sale Warehouse Auto Fulfillment* and click **Activate**.
3. The module depends on **Sales**, **Inventory** (through `sale_stock`) and
   **Invoicing** (`account`). Odoo installs them automatically if they are
   missing.

No new access group is created. Whoever can edit a warehouse today (Inventory
administrators) can turn the automation on; whoever can confirm a sales order
today triggers it.

## 3. Configuration

Go to **Inventory ▸ Configuration ▸ Warehouses** and open a warehouse. Next to
the **Short Name** (`code`) field you will find three new checkboxes:

| Checkbox | Technical field | Default |
|---|---|---|
| Ship Automatically | `auto_ship` | unchecked |
| Create Invoice Automatically | `auto_invoice_create` | unchecked |
| Confirm Invoice Automatically | `auto_invoice_confirm` | unchecked |

All three are off after installation, so installing the module changes nothing
until you deliberately switch something on.

> **Important:** only enable **Ship Automatically** on warehouses whose stock
> figures you trust. Automatic shipping performs **no availability check** — see
> section 5.

## 4. Daily use

There is no new workflow to learn.

1. Create a quotation as usual (**Sales ▸ Orders ▸ Quotations ▸ New**).
2. Check that **Warehouse** on the *Other Info* tab points at the automated
   warehouse.
3. Click **Confirm**.

Depending on the switches, when the page comes back you will see:

- the **Delivery** smart button showing a transfer in state **Done**,
- the **Invoices** smart button counter increased by one,
- that invoice already in state **Posted**.

If something went wrong, the order is still a **Quotation** and a blocking
message explains why (section 6).

## 5. The three switches in detail

### Ship Automatically (`auto_ship`)

Validates the order's delivery immediately after the order is confirmed:

- **all lines, full ordered quantity** — no partial shipping,
- **no backorder** is ever created,
- **no stock availability check** — if you sell 10 units of a product with 0 on
  hand, the transfer is still set to Done and on-hand stock becomes **−10**.
  This is intentional, not a bug.

### Create Invoice Automatically (`auto_invoice_create`)

Runs exactly what the manual **Create Invoice** button runs, so each product
keeps its own **Invoicing Policy**:

| Product invoicing policy | `auto_ship` on | `auto_ship` off |
|---|---|---|
| Ordered quantities | invoice for the ordered quantity | invoice for the ordered quantity |
| Delivered quantities | invoice for the delivered quantity | **nothing to invoice — skipped silently** |

**"Nothing to invoice" is not a failure.** When there are no invoiceable lines,
the step is skipped, a note is written to the order's chatter
("Automatic invoicing skipped: there was nothing to invoice on this order at
confirmation time.") and the confirmation succeeds normally.

Worked example — a warehouse with `auto_invoice_create` on and `auto_ship`
**off**, and an order with two lines:

| Line | Policy | Qty | Result |
|---|---|---|---|
| Standard Widget | Ordered | 5 × 45.00 | invoiced → 225.00 |
| Custom Fixture | Delivered | 2 × 320.00 | not invoiced (0 delivered) |

One draft invoice is created, for **225.00**. The Custom Fixture line stays
"To Invoice" until somebody delivers it.

If the order had contained *only* the Custom Fixture line, no invoice would be
created at all and the chatter note would appear instead.

### Confirm Invoice Automatically (`auto_invoice_confirm`)

Posts the invoice that this same automation run has just created.

**It has no independent effect.** With `auto_invoice_create` off there is
nothing for it to post, so a warehouse with only this switch on behaves exactly
like standard Odoo. It never touches invoices created by anyone else, and it
never posts an older draft invoice.

Invoices are posted, **never emailed**.

## 6. What happens when something fails

A *real* error means one of these three:

- the delivery could not be validated (for example a lot/serial number is
  required, or Odoo asked for a confirmation wizard),
- the invoice could not be created,
- the invoice could not be posted (for example the customer has no receivable
  account).

When one of them happens, the whole run — **including the order's state change
to Confirmed** — is rolled back inside a single database savepoint. The result
is all-or-nothing:

- the order goes back to **Quotation**,
- no delivery order is left behind,
- no invoice, draft or posted, is left behind.

You then get a blocking message naming the stage and the underlying reason, for
example:

> Automatic fulfillment failed for S00042 on warehouse Main Warehouse.
>
> Stage: automatic invoice posting
> Reason: The customer has no receivable account.
>
> Nothing was kept: the order stays a quotation, no delivery was validated and
> no invoice was created. Fix the reason above and confirm the order again, or
> turn the automation off on the warehouse to confirm it manually.

Because the order itself is rolled back, it carries **no trace** of the attempt.
The failure is instead written to `ir.logging` through an independent database
transaction, so it survives the rollback. Developers can read it from the shell
or from **Settings ▸ Technical ▸ Logging** (developer mode) by filtering on
`name = sale_warehouse_auto_fulfillment`.

## 7. Demo data walkthrough

Install the module in a database **with demo data** to get a ready-made
playground.

**Warehouses**

| Warehouse | Code | Ship | Create invoice | Post invoice |
|---|---|---|---|---|
| Main Warehouse | `WH` | on | on | on |
| Project Warehouse | `PROJ` | off | off | off |

**Products**

| Product | Invoicing policy | On hand in `WH` |
|---|---|---|
| Standard Widget | Ordered quantities | 150 |
| Office Chair | Ordered quantities | 60 |
| Custom Fixture | Delivered quantities | 0 |

**Quotations** — six drafts are pre-created, each with the scenario written in
its **Customer Reference** field:

| Scenario | Order content | What to do |
|---|---|---|
| 1 — full auto flow | Standard Widget ×5, Office Chair ×2 | confirm as-is |
| 2 — ship only | Standard Widget ×12 | first leave only **Ship Automatically** on `WH` |
| 3a — invoice create only | Office Chair ×4 | first leave only **Create Invoice Automatically** on `WH` |
| 3b — silent skip | Custom Fixture ×2 | same switches as 3a; no invoice is created, a chatter note appears |
| 4 — manual baseline | Standard Widget ×6, Project Warehouse | confirm as-is, nothing is automated |
| 5 — negative stock | Custom Fixture ×10 | confirm as-is; delivery is Done and on-hand becomes −10 |

Scenarios 2, 3a and 3b need you to change the `WH` switches first, because the
switches live on the warehouse and not on the order. Remember to set all three
back on afterwards if you want to replay scenario 1 or 5.

## 8. Field reference

Model `stock.warehouse` (extended):

| Field | Type | Label | Meaning |
|---|---|---|---|
| `auto_ship` | Boolean | Ship Automatically | validate the delivery in full on order confirmation |
| `auto_invoice_create` | Boolean | Create Invoice Automatically | run standard invoice creation on order confirmation |
| `auto_invoice_confirm` | Boolean | Confirm Invoice Automatically | post the invoice this run just created |

Model `sale.order` (extended): no new fields. `action_confirm()` is overridden;
with all three warehouse switches off it is a plain pass-through to standard
Odoo.

Model `ir.logging` (reused, not extended): automation failures are stored here.

## 9. Limitations

Stated honestly, these are deliberate design decisions, not bugs:

- **No partial shipping.** Automatic delivery is all-or-nothing for the whole
  order. If you need to ship part of an order, turn `auto_ship` off for that
  warehouse.
- **No stock availability check.** Negative stock is intended behaviour on
  automatic warehouses.
- **Lot/serial-tracked products are out of scope.** If validation cannot
  complete because a lot or serial number is required, that is a real failure:
  full rollback and a blocking message, not a silent skip.
- **No per-order override and no exceptions list.** The switches are per
  warehouse only.
- **No invoice emailing.** Invoices are posted, never sent to the customer.
- **No automation history on the order.** A rolled-back order shows no trace of
  the attempt; auditability is through `ir.logging` only, which is
  developer-facing.
- **Nothing is retried.** A failed confirmation must be confirmed again by hand
  once the cause is fixed.

## 10. Troubleshooting

| Symptom | Cause | What to do |
|---|---|---|
| Confirm behaves like standard Odoo | the order's warehouse has `auto_ship` and `auto_invoice_create` both off | check **Other Info ▸ Warehouse** on the order, then the warehouse form |
| Only `Confirm Invoice Automatically` is on and nothing happens | it has no independent effect | also switch on **Create Invoice Automatically** |
| Delivery is Done but no invoice was created | every line uses the *Delivered quantities* policy and `auto_ship` is off | switch on **Ship Automatically**, or invoice manually |
| Chatter says "Automatic invoicing skipped" | there was genuinely nothing to invoice | expected behaviour; invoice manually once quantities are delivered |
| Order stays a Quotation with a blocking message | a real error at one of the three stages | read the *Reason* line, fix it, confirm again |
| Stock went negative | `auto_ship` performs no availability check | expected; only enable it on warehouses with trusted stock figures |
| I need the failure history | the order was rolled back, so it has none | developer mode ▸ **Settings ▸ Technical ▸ Logging**, filter `name = sale_warehouse_auto_fulfillment` |

---

*Generated by OdoMate — https://odomate.pro — support@odomate.pro*
