# User Guide: Product Sample Requests

> Sales reps request product samples for customers, managers approve and ship them, and Odoo reminds the rep to follow up and measures how many samples turn into orders.

---

## Table of Contents

1. [What does this module do](#1-what-does-this-module-do)
2. [Where to find it in Odoo](#2-where-to-find-it-in-odoo)
3. [First-run setup](#3-first-run-setup)
4. [Creating a sample request](#4-creating-a-sample-request)
5. [Core workflow](#5-core-workflow)
6. [Follow-up reminder and outcome](#6-follow-up-reminder-and-outcome)
7. [Reporting and conversion rate](#7-reporting-and-conversion-rate)
8. [Access roles](#8-access-roles)
9. [Limitations](#9-limitations)

---

## 1. What does this module do

The module replaces e-mails and spreadsheets for product samples. A sales rep creates a **Sample Request** (`sample.request`) for a customer with one or more products and quantities, then submits it. A sales manager approves or rejects it. Once the samples have gone out, the manager clicks **Mark as Sent**, and Odoo schedules a follow-up to-do for the rep 14 days later. The rep records whether the customer ordered, and the Reporting menu shows the sample-to-order conversion rate per sales rep.

| Capability | Details |
|---|---|
| Sample requests with product lines | Customer, Sales Rep, Reason, Reason Details and a **Products** tab (Product, Quantity). Each request gets a reference such as `SR/2026/0001`. |
| Approval workflow | Draft → Submitted → Approved → Sent → Followed Up, plus Rejected and Cancelled. Every status change is logged in the chatter. |
| Mandatory rejection reason | The **Reject** button opens a dialog where a reason is required. The reason is shown on the request. |
| Manager notification on submit | **Submit** creates a To-Do activity "Sample request awaiting approval" for every **Sample Request / Manager**, so nobody has to remember to check the Approvals menu. |
| Automatic follow-up to-do | **Mark as Sent** creates a To-Do activity "Follow up on sample request" for the rep, due on Sent Date + 14 days. |
| Outcome logging | The **Log Outcome** dialog records Ordered / Still Thinking / Not Interested and can link a Sales Order. |
| Conversion reporting | Pivot and graph views by Sales Rep and Status, with the **Converted** and **Conversion Rate (%)** measures. |
| Record visibility | Reps see only their own requests. Managers see everyone's. |

---

## 2. Where to find it in Odoo

After installation, the main menu has a new app called **Sample Requests** with these menus:

- **My Requests**: your own requests (the "My Requests" filter is on by default). Opens in kanban view, grouped by status. List, form, pivot and graph views are also available.
- **Approvals** (managers only): every request with status **Submitted**, waiting for a decision. You cannot create requests from this menu.
- **All Requests** (managers only): every request from every sales rep.
- **Reporting**: the *Sample Request Analysis* pivot and graph, opened with the **Sent or Followed Up** filter already on.

---

## 3. First-run setup

There is nothing to configure beyond user access. The module ships no settings page.

1. Go to **Settings → Users & Companies → Users** and open a user.
2. In the access rights section, set **Sample Request** to **User** (sales reps) or **Manager** (people who approve and ship samples).
3. Save. The **Sample Requests** app appears in that user's main menu.

| Who | Group to assign |
|---|---|
| Sales rep who asks for samples | `Sample Request / User` |
| Sales manager or logistics lead who approves and ships | `Sample Request / Manager` |

> Tip: The administrator account receives **Sample Request / Manager** automatically at install, so the app is visible right away.
>
> Tip: `Sample Request / User` also gives **Sales / User: Own Documents Only**, so reps can look up sales orders when they log an outcome.

---

## 4. Creating a sample request

**Path:** `Sample Requests` → `My Requests` → `New`

| Field | Description |
|---|---|
| **Reference** | Set automatically when you save (for example `SR/2026/0007`). Read-only. |
| **Customer** | Required. The company or contact who receives the samples. |
| **Sales Rep** | Required. Defaults to you. Only a manager can change it, and only while the request is a draft. |
| **Reason** | Optional: Deal in Progress, New Prospect, Existing Customer, Trade Show, Other. |
| **Reason Details** | Free text for the approver, for example "Pilot run for the Q3 tender, 2 colours". |
| **Products** tab | One line per product: **Product** and **Quantity**. The quantity must be greater than zero. |

**Status flow:**

```
Draft ──Submit──▶ Submitted ──Approve──▶ Approved ──Mark as Sent──▶ Sent ──Log Outcome──▶ Followed Up
  │                  │
  │                  ├──Reject (reason required)──▶ Rejected
  │                  │
  └──Cancel──────────┴──Cancel──▶ Cancelled
```

> Warning: Rejected and Cancelled are final. To try again, open the request and use **Actions → Duplicate**. The copy starts as a new Draft with the same customer, reason and product lines.

---

## 5. Core workflow

### Journey 1: Sales rep requests samples

**Step 1: Fill in the request.** Choose the **Customer**, optionally a **Reason** and **Reason Details**, then add at least one line in the **Products** tab.

**Step 2: Click Submit.**
- If the **Products** tab is empty, Odoo stops you with "Add at least one product to … before submitting it."
- The status changes to **Submitted** and the request appears under **Approvals** for every manager.
- Every user with **Sample Request / Manager** gets a To-Do activity "Sample request awaiting approval" on the request, due today. The to-do is closed automatically as soon as any manager approves or rejects the request, or the rep cancels it — nobody needs to clear it by hand.

> Warning: After you submit, you can no longer edit the customer, reason, sales rep or products. If something is wrong, click **Cancel** (allowed while the request is Draft or Submitted), then duplicate the request and fix the copy.

### Journey 2: Manager decides

Open **Sample Requests → Approvals** and open a request.

- **Approve**: the status changes to **Approved**, and **Decided By** is set to you.
- **Reject**: a dialog asks for a **Rejection Reason** (required). Click **Reject** in the dialog. The status changes to **Rejected**, a red "Rejected" ribbon appears, and the reason and **Decided By** are shown on the form.

Any user with **Sample Request / Manager** can decide on any request. Approval is not tied to the rep's own manager.

### Journey 3: Manager ships the samples

When the parcel leaves, open the approved request and click **Mark as Sent**:

- **Sent Date** is set to today. If a manager had already filled in a Sent Date, that date is kept.
- The status changes to **Sent**.
- A To-Do activity is scheduled for the sales rep (see [section 6](#6-follow-up-reminder-and-outcome)).

While the request is **Sent**, a manager can still correct **Sent Date** on the form. Changing the date later does **not** move the to-do that was already created, so adjust the activity's due date by hand if needed.

### Deleting

Only **Draft** or **Cancelled** requests can be deleted. Any other request gives "Only draft or cancelled sample requests can be deleted." Cancel the request instead, so its history is kept.

---

## 6. Follow-up reminder and outcome

### The reminder

**Mark as Sent** creates exactly one activity on the request:

| Property | Value |
|---|---|
| Type | To-Do |
| Summary | Follow up on sample request |
| Assigned to | The request's **Sales Rep** |
| Due date | **Sent Date** + 14 days |

Example: Sent Date is **3 March 2026**, so the to-do is due on **17 March 2026**. The rep sees it in the activity menu (clock icon) and in the request's chatter.

### Logging the outcome

On a **Sent** request, the rep who owns it (or any manager) clicks **Log Outcome**. The *Log Follow-up Outcome* dialog opens:

| Field | Description |
|---|---|
| **Outcome** | Required: **Ordered**, **Still Thinking** or **Not Interested**. |
| **Sales Order** | Only shown for **Ordered**. Optional. You can pick only orders whose customer is the request's customer or one of its contacts. You cannot create a new order from here. |

Click **Log Outcome**. Odoo then:
- sets the status to **Followed Up** and saves **Follow-up Outcome**,
- marks the follow-up to-do as done, with the feedback "Outcome: Ordered" (or the outcome you chose),
- shows a green "Ordered" ribbon if the outcome is Ordered.

> Tip: If the order is not in Odoo yet, log **Ordered** without a sales order. Later, open the request and fill in **Sales Order** on the form. The field stays editable for Ordered requests.
>
> Note: **Still Thinking** also closes the request and its to-do. No second reminder is scheduled. If you want another reminder, schedule a new activity in the chatter yourself.

---

## 7. Reporting and conversion rate

**Path:** `Sample Requests` → `Reporting`

The *Sample Request Analysis* pivot opens with:
- **Rows:** Sales Rep
- **Columns:** Status
- **Measures:** **Count**, **Converted**, **Conversion Rate (%)**
- **Filter:** **Sent or Followed Up** (already on)

Each request stores two values:

| Measure | Value per request | How the pivot adds it up |
|---|---|---|
| **Converted** | 1 if Followed Up with outcome Ordered, else 0 | Sum |
| **Conversion Rate (%)** | 100 if Followed Up with outcome Ordered, else 0 | Average |

So, with the default filter on:

```
Conversion Rate = ordered requests ÷ (sent + followed-up requests) × 100
```

**Worked example.** Anna has 10 requests that are Sent or Followed Up: 2 are still **Sent**, and 8 are **Followed Up** (3 Ordered, 4 Still Thinking, 1 Not Interested).

| Sales Rep | Count | Converted | Conversion Rate (%) |
|---|---|---|---|
| Anna | 10 | 3 | (3 × 100 + 7 × 0) ÷ 10 = **30.00** |

> Warning: If you remove the **Sent or Followed Up** filter, drafts, rejected and cancelled requests are counted as 0 and push the rate down. In the example, adding 5 drafts and 1 rejected request would show 3 ÷ 16 = **18.75 %**. Keep the filter on when you read the rate, or look at the rate in the **Sent** and **Followed Up** columns only.

Other useful filters and groupings in the search panel: **Pending Approval**, **Awaiting Follow-up**, **Converted to Order**, **Sent Date** (by period), and group by **Outcome**, **Reason** or **Customer**.

The graph view shows a bar chart of requests per Sales Rep and Status, and now offers the same **Conversion Rate (%)** measure as the pivot — open the measures dropdown and pick **Conversion Rate (%)** to compare reps at a glance instead of reading the pivot table. Bars are no longer stacked, so each rep's bar height is directly comparable (a stacked average would not add up to anything meaningful).

---

## 8. Access roles

| Action | Sample Request / User (rep) | Sample Request / Manager |
|---|---|---|
| See requests | Own only (Sales Rep = me) | All |
| Create request | Yes, for themself | Yes, for any rep |
| Edit request / products | Only while Draft | Yes, in any status (the form locks most fields after Draft) |
| Submit | Own drafts | Any draft |
| Cancel (Draft / Submitted) | Own | Any |
| Approve / Reject / Mark as Sent | No | Yes |
| Edit Sent Date while Sent | No | Yes |
| Log Outcome (on Sent) | Own | Any |
| Link Sales Order on an Ordered request | Own | Any |
| Delete | Own Draft / Cancelled | Any Draft / Cancelled |
| Menus | My Requests, Reporting | My Requests, Approvals, All Requests, Reporting |

`Sample Request / Manager` includes everything in `Sample Request / User`. `Sample Request / User` includes **Sales / User: Own Documents Only**. In Reporting, a rep sees statistics for their own requests only.

To assign roles: **Settings → Users & Companies → Users** → select a user → **Sample Request** access field.

---

## 9. Limitations

| Topic | Limitation |
|---|---|
| Multi-company | Requests have no Company field and no company record rule. In a multi-company database, managers see requests from all companies. The reference sequence is shared by all companies. |
| Conversion rate | Meaningful only with the **Sent or Followed Up** filter on (it is on by default in Reporting). Without it, drafts, rejected and cancelled requests count as 0. |
| Linked sales order | Not checked against the sampled products, quantities or amounts. Any order of the customer or its contacts can be linked, including draft quotations or cancelled orders. |
| Sales order choice | Limited to orders whose customer is the request's customer or one of its child contacts. An order placed under a parent company or an unrelated partner cannot be selected. You cannot create an order from the request. |
| Stock / delivery | Marking as sent does not create a delivery order and does not move stock. Shipping is done outside this module. |
| Approval routing | Any manager can approve any request. There are no approval levels, amount limits or per-team approvers. Submitting notifies every manager with a To-Do activity (no e-mail is sent). |
| Follow-up timing | The 14-day delay is fixed in code. Changing Sent Date after Mark as Sent does not move the existing to-do. **Still Thinking** closes the request without a second reminder. |
| Final states | Rejected, Cancelled and Followed Up cannot be reopened. Use **Duplicate** to start again. |
| Sample cost | Product costs or values of the samples are not tracked or reported. |
