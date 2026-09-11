# Time Off Requests by Email — User Guide

Technical name: `odomate_hr_leave_email` · Odoo 19.0 · Depends on `hr_holidays`, `mail`

## Table of contents

1. [What this module does](#1-what-this-module-does)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration)
4. [Writing a request as an employee](#4-writing-a-request-as-an-employee)
5. [Reading the Email Requests log](#5-reading-the-email-requests-log)
6. [Refusal reasons in full](#6-refusal-reasons-in-full)
7. [Access rights](#7-access-rights)
8. [Multi-company behaviour](#8-multi-company-behaviour)
9. [Limitations](#9-limitations)

---

## 1. What this module does

One published email address turns an incoming message into an ordinary Time Off
request. The request lands in Time Off exactly like one typed in the web client:
same model (`hr.leave`), same approval flow, same calendar.

The module never guesses. If it cannot tell **who** wrote, **when** they want
off, or **which** Time Off type to use, it refuses, writes one row in a log, and
(optionally) answers the sender with the accepted date formats.

Three moving parts:

| Part | What it is |
|---|---|
| `mail.alias` `timeoff-request` | The published address. Ships with the module, points at `hr.leave`, accepts mail from authenticated employees only. |
| `odomate.hr.leave.email.log` | One row per incoming message — created or refused, and why. Never edited by anyone. |
| `mail.template` "Time Off by Email: Request Refused" | The answer sent back to the sender on refusal. |

## 2. Installation

1. Copy `odomate_hr_leave_email` into your addons path.
2. **Apps → Update Apps List**.
3. Search for *Time Off Requests by Email* and click **Activate**.

`hr_holidays` and `mail` are installed automatically if they are not there yet.

Installing the module changes nothing on its own: the feature ships **off**.

## 3. Configuration

### 3.1 An alias domain must exist first

Odoo can only receive mail on an alias when at least one **Alias Domain** record
exists. A freshly created database has none.

**Settings → General Settings → Discuss → Alias Domain** — set it (for example
`ourcompany.com`) before going further. Until you do, the Time Off settings
block shows the warning:

> No alias domain is configured yet, so the address cannot receive anything.
> Set one under Settings / General Settings / Discuss / Alias Domain first.

You also need a working incoming mail server (**Settings → Technical → Email →
Incoming Mail Servers**) or a catch-all forwarded to Odoo — this module uses
Odoo's standard mail gateway and adds nothing to it.

### 3.2 Switch the feature on

**Settings → Time Off** (the *Time Off* settings tab) → block **Time Off
Requests by Email**:

| Setting | Field | Meaning |
|---|---|---|
| Requests by Email | `leave_email_enabled` | Master switch. Off after install. |
| Time Off Email Address | `leave_email_address` | Read-only. The address to publish, e.g. `timeoff-request@ourcompany.com`. |
| Time Off Type for Email Requests | `leave_email_type_id` | The type every email request gets. |
| Reply on Refusal | `leave_email_reply_on_failure` | On by default. Sends the explanation email back. |

The Time Off type selector shows types of the current company plus company-less
types. Pick one that does **not** require an allocation if you want requests to
go through without a balance check — for example an *Unpaid* type. The module
reads whatever you choose here; it never searches for a type on its own.

Both the address and the type are checked at the moment a message arrives, so
archiving the chosen type later starts refusing requests with *Time Off type not
configured* rather than crashing.

## 4. Writing a request as an employee

The employee sends a plain email to the published address. Rules:

- **Who**: the sender address must match the employee's login, the email on
  their user, or `work_email` on their employee record. Anything else is refused
  as *Unknown sender*.
- **When**: the first two dates in the body are used, in the order they appear.
  Accepted formats: `YYYY-MM-DD` and `DD/MM/YYYY`. Subject lines are ignored.
- **How long**: first date = first day off, second date = last day off. Only one
  date in the message means one day off.

Worked examples:

| Body of the message | Result |
|---|---|
| `Hi, I'd like 2026-03-09 to 2026-03-13 off.` | Request from 9 March to 13 March 2026 (5 calendar days). |
| `Off 09/03/2026 - 13/03/2026, thanks` | Same request — the European format is read identically. |
| `Just 2026-03-09 please` | One-day request on 9 March 2026. |
| `From 13/03/2026 to 09/03/2026` | Refused, *End date before start date*. |
| `Taking a few days off soon` | Refused, *No date found*. |

Attachments (a doctor's note, for example) ride along with Odoo's normal mail
handling and end up on the request's chatter. Their content is never read.

The created request starts in **To Approve**, like any other. The module never
approves anything.

## 5. Reading the Email Requests log

**Time Off → Reporting → Email Requests**

Every message that reached the address is one row — nothing is silently dropped.
Green rows were turned into requests, red rows were refused.

| Column | Field | Notes |
|---|---|---|
| Received On | `received_date` | When the gateway processed the message. |
| From | `email_from` | The raw sender address. |
| Subject | `subject` | Subject line as received. |
| Employee | `employee_id` | Empty for an unresolved sender. |
| Result | `state` | Created / Rejected. |
| Reason | `failure_reason` | Only filled on a refusal. |
| Time Off Request | `leave_id` | Click through to the created `hr.leave`. |

Filters cover Created, Rejected, Unknown Sender, No Date Found and Type Not
Configured; **Group By** offers Result, Reason, Employee and Received On.

The form view is read-only, and so is the list — the system writes these rows,
people read them. Time Off Managers may delete rows; nobody can create or edit
one from the interface.

**The message body is never stored in the log.** Only the sender address and the
subject are kept. The message itself lives on the created request's chatter,
under the usual Time Off access rules.

## 6. Refusal reasons in full

| Reason | Trigger | What the sender is told |
|---|---|---|
| Unknown sender | No employee matches the sender address | Write from your work address, or ask HR to add the address to your employee file |
| No date found | No `YYYY-MM-DD` or `DD/MM/YYYY` in the body | The two accepted formats, with examples |
| End date before start date | Second date is earlier than the first | The end date comes before the start date |
| Time Off type not configured | The configured type is empty, archived or deleted | Requests by email are not fully configured; contact HR |
| Unexpected error | Anything else — the request could not be created | Something went wrong; contact HR |
| Feature disabled | Reserved | Not used: with the feature off, no log row is written at all |

Every refusal email also repeats the accepted date formats, so a confused sender
can retry without asking anyone.

## 7. Access rights

| Group | Read | Write | Create | Delete |
|---|---|---|---|---|
| `hr_holidays.group_hr_holidays_user` (Time Off Officer) | ✔ | — | — | — |
| `hr_holidays.group_hr_holidays_manager` (Time Off Administrator) | ✔ | — | — | ✔ |
| Everyone else, including plain internal users | — | — | — | — |

No new security group is created and no group is granted to anyone at install.
Rows are written by the mail gateway's own elevated context, not through a
user-facing permission — which is why nobody has create or write rights.

An internal user without a Time Off group who opens a log record by direct URL
gets an Access Error. That is intended.

## 8. Multi-company behaviour

- The address is **global**: one alias, shared by every company. The company of a
  request comes from the employee, never from the reader's active company.
- A log row carries the resolved employee's company. Rows whose sender could not
  be resolved carry no company at all.
- A record rule keeps each reader to rows of their allowed companies, plus every
  company-less row:
  `['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]`.
  Unresolved senders therefore stay visible to Time Off staff in any company,
  which is what you want when nobody knows yet who wrote.
- When one user has an employee record in several companies, the module keeps
  the employee whose company matches that user's own company.

## 9. Limitations

- **No allocation check is added.** If the configured type requires an
  allocation and the employee has none, Odoo's own validation refuses the
  request, and the log records it as *Unexpected error* rather than as a
  balance problem. Configuring a type that needs no allocation avoids this.
- **Half days and hours are not supported.** Every email request is whole days.
  Times written in the message are ignored.
- **Only the first two dates count.** A message listing three separate periods
  produces one request covering the first two dates found.
- **Dates are read from the body only**, never from the subject line, and only
  in the two documented formats. `March 9th`, `9 Mar 2026` and `03/09/2026`
  (US order) are not recognised — the third one is read as 3 September.
- **On a refusal the message itself is not kept.** The log row and the reply
  explain what happened, but the original text is not stored anywhere. The
  mail gateway also reports the message as unprocessed in the server log, since
  no record was created for it.
- **No allocation, no approval and no cancellation by email.** The address only
  creates requests; every later step happens in Odoo.
- **One address for the whole database.** Per-company or per-department
  addresses are not supported.
