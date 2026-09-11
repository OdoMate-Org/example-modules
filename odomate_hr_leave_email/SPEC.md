# SPEC.md — the business specification this module was generated from

This is the business-level specification the module in this folder was generated
from — code, views, security, demo data, tests, and the user guides in `doc/`.
It is written in the voice of the person who would ask for it: the HR officer who
retypes fifteen emailed time-off requests a week, who uses Odoo every day and has
no knowledge of how Odoo is built inside. No model names, field names or technical
design appear in it; everything in `models/`, `views/` and `security/` was derived
by OdoMate from the plain requirements below.

**Provenance, stated plainly.** This specification was written by the OdoMate team
as an independent description of what requesting time off by email should do. It
contains no third-party code, text or configuration. The module was generated from
this document alone.

**What was verified before publication.** All seventeen acceptance criteria in
section 6 were walked by hand against a running database when the module was first
generated, including criterion 15, which is checked by reading the rendered settings
screen rather than the configuration values behind it. The published version was then
re-measured on a freshly created Odoo 19 Community database: it installs on the first
attempt with no errors (47 modules), installs equally cleanly on a Ukrainian database
(47 modules, no errors), and its automated tests pass with no failures and no errors —
Odoo's runner reports **31 tests, 0 failed, 0 errors**. Criterion 17, which requires
the refusal replies to reach the sender in Ukrainian, is the one the published version
changed; **8 of 8** of those messages now load, where the first generated version
loaded none. See the note below.

**Nothing in this module was corrected by hand.** Where two earlier modules in this series carry a
hand-applied translation correction disclosed in their own `SPEC.md`, this one does
not. The same generator-wide fault was present in the first generated version — the
Ukrainian catalogue was complete and correct, and Odoo loaded **none** of the eight
messages the module raises from Python, which are precisely the refusal replies sent
back to an employee whose request could not be read. Odoo's `CodeTranslations`
accepts a code entry only when it carries the extracted comment `#. odoo-python`, and
`PoFileReader` merges a module's own `.pot` over its `.po` before reading, which
strips that comment. It was fixed by generating a second version rather than by
editing the file: the whole change is eight added comment lines, the removal of the
generated `.pot`, and the version string. Every `msgid` and every `msgstr` is
byte-identical to the first version, and **8 of 8** now load. The fault itself is
reported to the platform rather than treated as this module's problem.

Generated with OdoMate (https://www.odomate.pro) — September 2026, Odoo 19
Community. Published unedited apart from publication metadata (store listing page,
banner and icon).

---



# Leave Requests by Email — Spec (Level 1: Business User)

> **Who wrote this:** the HR officer who processes time-off requests. They use Odoo every day and have **no** idea how Odoo is built inside.

**What app this touches:** the **Time Off** app — its settings, and the requests that arrive in it.

---

## 1. What I want (the problem)

Half our people do not open Odoo. Drivers, warehouse, the two site teams — they have a phone and an email address and that is it. When they want a day off they email me, and I retype it.

- I retype maybe fifteen of these a week. Every one is a name, two dates and a reason moved from one screen to another.
- I mistype them. The wrong person, the wrong month, a day short.
- The request has no trail. If somebody says "I sent that on the 3rd", the proof is in my mailbox, not in Odoo.
- People email the wrong person, or email me while I am away, and the request sits unread for a week.

I want them to be able to **email a single address** and have the request appear in Time Off, against the right person, with the right dates, waiting for approval like any other.

## 2. What I want to be able to do

### a) Have one address that turns email into a time-off request

We publish one address — something like `leave@ourcompany.com`. A message sent to it creates a time-off request in Odoo, for the person who sent it, in the ordinary *waiting for approval* state.

### b) Have it find the right person

The sender's address is matched against employees' work email addresses and their login. If it matches nobody, **nothing is created** — see (d).

### c) Have it read the dates out of the message

The message body says when. It should understand the ordinary ways people write it:

- `2026-10-14` to `2026-10-17` — one date, then another
- `14/10/2026 - 17/10/2026`
- a single date, meaning one day

The **first** date found is the start and the **second** is the end; a single date means a one-day request. The subject line becomes the description, so I can see at a glance what it is.

### d) **Never guess.** This is the rule that matters most.

If the sender is not an employee, or no date can be found, or the dates are the wrong way round, or the type of leave cannot be decided — **no request is created**. Instead:

- the sender gets a **reply** saying what was missing and how to write it properly, and
- the attempt is **written down**, so I can see what came in and why it was refused.

A half-filled request with a missing employee or a missing date is worse than no request. Somebody has to notice it, work out what happened, and delete it — and until they do it sits in the approval queue looking real.

### e) Decide which kind of leave it is

There are many kinds of time off and an email cannot be trusted to pick one. So: **we configure one kind that email requests use** — typically the one that needs no allocation, like unpaid leave — and every email request is created as that. If somebody wants their annual leave, HR changes the type before approving. The rule is written down and predictable rather than clever.

### f) See what has come in

A list of every message the address received: when, who from, whether a request was created, which request, and if not, the reason. Not a debugging log — the thing I look at when somebody says "I emailed you last Tuesday".

### g) Configure it without a developer

In the Time Off settings: whether email requests are switched on, the address, the kind of leave they become, and whether to reply to messages that could not be understood.

## 3. What I want to see on screen

- **In Time Off → Configuration → Settings:** a *Requests by email* block with an on/off switch, **the full address shown as an address** — `leave@ourcompany.com`, not an empty box with a prefix in it — the kind of leave to use, and the reply switch. If the system has no email domain configured yet, the block **says so**, because without one the address receives nothing.
- **In Time Off → Reporting (or Configuration), an *Email requests* list:** date received, sender, subject, outcome — *created* or *not created* — the reason where it was not, and a link to the request where it was.
- **On the created request:** an ordinary time-off request, nothing special about it, except that the original message is in its message thread so anybody can read what was actually sent.
- **A green outcome and a red one should be tellable apart at a glance** in the list, without reading the reason column.

## 4. What I want to be warned about

- **Email has to be set up first.** Odoo must already be fetching mail and must have an email domain configured. This module adds the address; it does not fetch mail — Odoo does that already.
- **Anybody who can send email to that address, and whose address matches an employee, can create a request.** That is the point, and it is also the risk: email addresses are easy to fake. Requests still have to be approved by a human, and that is the control.
- **It reads dates, not sentences.** "The week after next" creates nothing. That is deliberate: refusing is safe, guessing is not.
- **One kind of leave for all email requests.** Somebody who emails asking for annual leave gets whatever type we configured, and HR changes it. The alternative — matching words in the subject against leave-type names — sounds helpful and produces wrong approvals.
- **A request created from email is not approved.** It waits, exactly like one typed into Odoo.
- **Attachments come along** with the message but are not read.

## 5. What is intentionally NOT included (keep the first version honest)

- **No approval by email.** Managers cannot approve by replying. Approval happens in Odoo.
- **No natural-language dates.** No "next Monday", no "the 3rd till the 7th", no month names.
- **No leave-type detection from the message.** See section 4.
- **No half-day or hourly requests.** Whole days only. An email cannot say "the afternoon of the 14th" in a way we would trust.
- **No allocation requests.** This creates time-off *requests*, never allocations.
- **No portal or web form.** Email only.
- **No second address per company or per department.** One address.
- **No editing of an email request from the log.** The log records what happened; the request is edited in Time Off like any other.

## 6. How we'll know it works (acceptance criteria)

These are checked by handing a message to the system the way the mail gateway does, not by sending real email — the mail gateway itself is Odoo's and is not ours to test. The setup: an employee whose work email is `anita@example.com`, email requests switched on, and the configured leave type set to one that needs no allocation.

1. **A well-formed message creates a request.** Subject *"Time off — family visit"*, body *"I would like leave from 2026-10-14 to 2026-10-17."*, from `anita@example.com` → a time-off request exists for Anita, from the 14th to the 17th, description *"Time off — family visit"*, of the configured type, in the **waiting for approval** state. ✅
2. **The other date format works too.** The same message written `14/10/2026 - 17/10/2026` produces the same dates. ✅
3. **One date means one day.** A body with a single date produces a request whose start and end are that same day. ✅
4. **The original message is on the request**, readable in its message thread. ✅
5. **An unknown sender creates nothing.** From `someone@elsewhere.com` — **no** time-off request exists afterwards, for anybody. ✅
6. **No date creates nothing.** From Anita, body *"I need some time off, I will confirm the dates later"* — **no** request. ✅
7. **Dates the wrong way round create nothing.** *"from 2026-10-17 to 2026-10-14"* — no request, and the recorded reason says the dates are reversed rather than "no date found". ✅
8. **Every refusal is written down.** Each of criteria 5, 6 and 7 leaves one row in the email-requests list, with the sender, the subject, the outcome *not created*, and a reason that distinguishes those three cases from each other. ✅
9. **Every success is written down too**, with the outcome *created* and a link that opens the request. ✅
10. **The sender is told.** With replies switched on, a refusal produces an outgoing message addressed to the sender; with them switched off, it does not. ✅
11. **Switched off means off.** With email requests disabled, the same well-formed message from criterion 1 creates **no** request and no log row. ✅
12. **The request belongs to the right company.** For an employee in the second company, the created request carries that employee's company, not the company of whoever happens to be processing mail. ✅
13. **A person with two employee records** — one per company — does not produce two requests, and the one produced is for the employee whose company matches their user. ✅
14. **The employee can see their own request** in *My Time Off*, and the approval flow that follows is Odoo's ordinary one — this module adds no state and no approval step of its own. ✅
15. **Open the settings screen and look at it.** The *Requests by email* block renders inside Time Off's own settings page, with the switch, the **complete address shown as an address** and the leave-type selector all visible and labelled; and with no email domain configured it shows a visible warning instead of a blank field. **This one is checked by looking at the rendered screen, not by reading the configuration values behind it.** ✅
16. **As an ordinary employee** — `base.group_user`, no HR role — I see **no** email-requests list and **no** *Requests by email* settings block, and opening a log row **directly at its address** is refused. My own time-off requests are unaffected. ✅
17. **Ukrainian.** With the Ukrainian locale installed, the settings block, the list, every outcome and every refusal reason — including the text of the reply sent to the sender — are in Ukrainian. ✅
