# Office Equipment Tracker — User Guide

## Table of Contents

1. [Overview](#1-overview)
2. [Installation](#2-installation)
3. [Roles & Access](#3-roles--access)
4. [The Equipment Record](#4-the-equipment-record)
5. [Status Workflow](#5-status-workflow)
6. [Working Views](#6-working-views)
7. [Business Rules](#7-business-rules)
8. [Demo Data](#8-demo-data)
9. [Limitations](#9-limitations)

## 1. Overview

Office Equipment Tracker keeps a single, always-current record of every
piece of company office equipment — laptops, phones, monitors and
peripherals — and who currently holds each item. It answers the everyday
questions of an office or IT manager: *Who has this laptop? When did they
take it? Which monitors are free right now? What is in repair?*

The module intentionally tracks **only the current assignment**. It does
not keep a per-item assignment history; reassigning an item simply
overwrites the current holder.

## 2. Installation

1. Place the `office_equipment_tracker` folder in your Odoo addons path.
2. Update the Apps list and install **Office Equipment Tracker**.
3. The `hr` module installs automatically as a dependency (equipment is
   assigned to `hr.employee` records).

## 3. Roles & Access

| Group | Capability |
|-------|-----------|
| **Equipment Administrator** | Full create / read / write / delete on all equipment; runs the check-out, return, repair and retire actions. |
| **Equipment Viewer** (all internal users) | Read-only. Sees only the equipment where the current holder's linked user is the logged-in user. |

Access is enforced by three record rules:

- Administrators see **all** records.
- Viewers see only records where `employee_id.user_id = current user`.
- A global multi-company rule limits every user to their allowed companies.

Grant the **Equipment Administrator** group under
*Settings > Users & Companies > Users*.

## 4. The Equipment Record

Open **Equipment > All Equipment** and create a record. Fields:

| Field | Description |
|-------|-------------|
| **Name** | Required. A human label, e.g. *Dell Latitude 7420*. |
| **Serial Number** | Optional. Unique across all non-retired equipment. |
| **Equipment Type** | Laptop / Phone / Monitor / Peripheral / Other. |
| **Status** | Available / Checked Out / In Repair / Retired. |
| **Current Holder** | The `hr.employee` who currently holds the item. |
| **Check-out Date** | Set automatically when the item is checked out. |
| **Return Date** | Set automatically when the item is returned. |
| **Condition Notes** | Free text — damage, repair reason, end-of-life note. |
| **Company** | Owning company (multi-company installs only). |

## 5. Status Workflow

The form header shows a status bar and the workflow action buttons. The
buttons are visible **only to Equipment Administrators** (a read-only
Equipment Viewer never sees them), and each button appears only in the
state where it applies:

- **Check Out** — shown only on an *Available* record. Requires a current
  holder. Sets the status to *Checked Out*, stores today's date as the
  check-out date, and clears the return date. Blocked if the current
  holder already has **3 items checked out** (see *Check-out limit* below).
- **Return** — shown only on a *Checked Out* record. Sets the status back
  to *Available*, clears the current holder, and stores today's date as
  the return date.
- **Send to Repair** — shown on *Available* or *Checked Out* records. Sets
  the status to *In Repair* and clears the current holder. Condition notes
  are preserved.
- **Retire** — shown on any non-retired record. Sets the status to
  *Retired* and clears the current holder. Condition notes are preserved.

Because check-out is offered only from *Available*, an item always flows
through *Available* before it can be checked out — you cannot jump into
*Checked Out* directly from *In Repair* or *Retired*.

```
                 Check Out
   Available  ───────────────▶  Checked Out
       ▲                             │
       │            Return           │
       └─────────────────────────────┘

   Any active state ──Send to Repair──▶ In Repair
   Any active state ──────Retire──────▶ Retired
```

### Worked example

You register *MacBook Pro 14* (status *Available*). You set the current
holder to **Marcus Reed** and click **Check Out**. The status becomes
*Checked Out* and the check-out date is set to today. Six weeks later
Marcus returns it: click **Return** — the holder is cleared, the status
returns to *Available*, and the return date is set to today.

## 6. Working Views

- **List view** (default) shows name, serial number, type, status, holder,
  check-out and return dates. Rows are colour-coded: green for available,
  blue for checked out, red for in repair, muted grey for retired.
- **Form view** groups identification and assignment fields side by side,
  with condition notes as a full-width text area and the workflow buttons
  in the header.
- **Search view** offers status filters (Available / Checked Out / In
  Repair / Retired) and Group By Employee, Equipment Type, or Status.

## 7. Business Rules

- **Holder required when checked out** — saving a *Checked Out* item
  without a current holder is rejected.
- **Serial-number uniqueness** — a serial number cannot be shared by two
  active (non-retired) items. A retired item's serial number may be reused
  by a new item. This is backed by a partial unique database index, so it
  holds even under concurrent creation.
- **Check-out limit** — an employee cannot hold more than **3** checked-out
  items at once. Clicking **Check Out** when the current holder is already
  at the limit is rejected with a message naming the employee, their
  current count, and the limit. Selecting several *Available* items and
  checking them all out to the same employee in one action counts them
  together against the limit. If the combined total would exceed 3, the
  whole action is rejected — because Check Out is a single button click,
  none of the selected items are checked out, not just the one that would
  have pushed the employee over the limit. The limit applies only to the
  **Check Out** button — it is not enforced on direct record imports or API
  writes that set the status to *Checked Out*.

## 8. Demo Data

Installing in demo mode loads 15 equipment records — 8 checked out to
different demo employees with check-out dates spread over the last six
months, 4 available, 2 in repair (with descriptive notes), and 1 retired.

## 9. Limitations

- **No assignment history.** Only the current holder is stored; reassigning
  overwrites the previous holder. Historical tracking would require a
  separate log model.
- **No overdue or reminder logic.** There are no scheduled notifications or
  overdue-return alerts in this scope.
- **No valuation.** The module tracks assignment, not financial value or
  depreciation.
