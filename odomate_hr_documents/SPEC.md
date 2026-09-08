# SPEC.md — the business specification this module was generated from

This is the business-level specification the module in this folder was generated
from — code, views, security, demo data, tests, and the user guides in `doc/`.
It is written in the voice of the person who would ask for it: an HR manager
responsible for making sure every person working here is legally allowed to, who
uses Odoo every day and has no knowledge of how Odoo is built inside. No model
names, field names or technical design appear in it; everything in `models/`,
`views/` and `security/` was derived by OdoMate from the plain requirements
below.

**Provenance, stated plainly.** This specification was written by the OdoMate
team as an independent description of what an employee-document-expiry feature
should do. It contains no third-party code, text or configuration. The module
was generated from this document alone.

**What was verified before publication.** The module installs on a freshly
created Odoo 19 Community database on the first attempt with no errors
(41 modules in 12.85s), its automated tests pass with no failures and no errors
(Odoo's runner reports 68 tests, of which 54 are the module's own test methods
and the rest are framework checks it runs against the module), its Ukrainian
translation is complete (88 of 88 strings), and all twenty-five acceptance
criteria were walked by hand against the running database.

Generated with OdoMate (https://www.odomate.pro) — September 2026, Odoo 19
Community. Published unedited apart from publication metadata (store listing
page, banner and icon).

**Two rounds, both of them the generator's own work.** The module was generated
from this document, then enhanced once, from a written brief and never by hand:

- **v2** removed an undeclared privilege escalation — the module had granted
  `hr.group_hr_manager` to the administrator's user record as an install side
  effect, changing an existing user's group memberships without saying so — and
  corrected the module's display name to match the name its own user guide tells
  the reader to search for. Odoo's `hr` module grants that group natively, so
  removing the record takes nothing away; this was confirmed against a control
  database with the module absent.

---


# Employee Documents — Spec (Level 1: Business User)

> **Who wrote this:** the HR manager responsible for making sure every person working here is legally allowed to, and that we can prove it. They use Odoo every day and have **no** idea how Odoo is built inside. This is how they would ask for it, in plain words.

**What app this touches:** the **Employees** app — a new **Documents** area, plus a button on each employee's record.

---

## 1. What I want (the problem)

Roughly a third of our people hold a document that stops being valid on a date: a work permit, a residence permit, a visa, a driving licence for the people who drive, a forklift certificate, a first-aid certificate, a professional licence for the engineers.

Today all of that lives in a shared spreadsheet with a column of dates and a colour code, maintained by whoever remembers. What actually happens:

- **We find out late.** Somebody notices a red cell in the week the permit expires, and a renewal that needs six weeks now needs to happen in five days.
- **Nobody owns the chase.** The spreadsheet does not email anyone. If the person who maintains it is on leave, the month passes.
- **I cannot prove anything.** An inspector asks to see the current permit for four named people. The scans are in four different mailboxes.
- **Renewal loses the history.** When a permit is renewed, somebody types over the old date and replaces the old scan. If a question is later asked about a period two years ago, we can no longer say what document covered it.
- **The same document exists twice.** Two people add the same certificate, with different expiry dates, and nobody can tell which is real.

I want a place where each of these documents lives once, with its scan, with its dates, where the system chases the person before it expires, where renewing keeps the old version, and where I can pull "everything expiring in the next 30 days" in one click.

---

## 2. What I want to be able to do

### a) Define the kinds of document we track

A short list I maintain: *Work permit, Residence permit, Driving licence, Forklift certificate, First-aid certificate, Professional licence*.

For each kind I want to say **how it should be chased**, because they are not the same:

- **On the day it expires** — for the ones that are trivially renewed and only need a nudge.
- **A set number of days before** — one email, that many days ahead. This is the normal case, and the number of days differs per kind: a work permit needs 60 days, a first-aid certificate needs 14.
- **Every day from a set number of days before, until it expires** — for the ones where one email is not going to be enough.
- **On the day it expires and every day after, for a set number of days** — for the ones where somebody is now working without a valid document and I need it in their face until it is fixed.

So each kind of document carries: its name, a number of days, and which of those four chasing patterns applies.

### b) Record a document against a person

For each document: the **employee**, the **kind**, a **free description**, the **date it was issued**, the **date it stops being valid**, and one or more **scans attached**. The system gives it its own **reference number** so I can refer to it in an email without ambiguity.

### c) Move a document through three states

- **Draft** — being entered, not yet checked. Nothing is chased.
- **Valid** — checked by HR, this is the live document. It is what gets chased.
- **Expired** — past its date.

I move a document from Draft to Valid myself, and I want to be **stopped** if I try to mark a document valid when its expiry date has already passed — that is always a mistake or a typo.

Documents whose date has passed should go to Expired **on their own**, without me doing anything.

### d) Not end up with two live copies of the same thing

An employee may hold only **one valid document of a given kind at a time**. If somebody tries to create a second valid work permit for the same person, I want it refused, with a message telling them to renew the existing one instead. Draft and expired copies may exist alongside — it is *valid* that is exclusive.

### e) Renew a document without losing what it replaced

Renewal should be a deliberate step, not an edit. When I renew, I am asked for:

- the **new issue date**,
- the **new expiry date**,
- the **new scan** — required, because a renewal without the new document is not a renewal,
- a **reason** in a sentence: what actually happened.

The system then **files the previous dates and the previous scan into that document's history**, puts the new details on the document, sets it back to Valid, and writes a note in the document's message thread saying what the old expiry date was, what the new one is, and why.

Two things must be refused: a new expiry date that is not in the future, and a new expiry date that is before the new issue date.

Afterwards I want to open the document and read its **renewal history** — each past version with its dates, its scan, who renewed it, when, and why.

### f) Be chased automatically, and chase manually when I want to

- A **daily check** that expires what has expired and sends the emails each document kind's pattern calls for.
- The email goes to the employee.
- It also puts a **to-do on the person's manager**, dated the expiry date — because the employee ignoring it is exactly the case I need to catch.
- A **button on the document** to send that email now, for when I am chasing somebody today.

### g) Find things without hunting

- A **Documents** list I can filter to *Valid*, *Expired*, *Draft*, *expiring within 7 days*, *expiring within 30 days*.
- **Group** that list by employee, by kind of document, and by state.
- A column showing **how long is left** in plain words — "Expired 12 days", "Today", "Tomorrow", or a number of days.
- On each employee's record, a **button showing how many documents they have**, which opens just theirs.
- From a document, a way to jump to the **employee** it belongs to.

### h) Keep our blank forms somewhere sensible

A small, separate library of the **blank forms and templates** the HR team hands out — the medical declaration, the equipment agreement, the permit application form. Each is a name, a note about when to use it, and the file itself. This is company paperwork, not anybody's personal document, and it has nothing to do with expiry dates. I just want it to stop living on somebody's desktop.

---

## 3. What I want to see on screen

- **A Documents area in the Employees app**, containing three screens: **Documents** (the real ones, against people), **Document Types** (the kinds and how each is chased), and **Forms & Templates** (the blank paperwork).
- **On a document:** the reference number across the top, the state shown as a bar I can see at a glance, the employee, the kind, the issue and expiry dates, how long is left, the description, the scans, and the message thread underneath. Buttons: **Mark valid**, **Renew**, **Send reminder now**, **Set to draft**, and a counter opening the **renewal history**.
- **On the Documents list:** employee, kind, expiry date, how long is left, state. Expired rows should be visually obvious without my reading the dates.
- **The renewal form:** four things only — new issue date, new expiry date, new scan, reason. Nothing else on it.
- **The renewal history:** a read-only list — when it was renewed, by whom, the dates that were replaced, the scan that was replaced, and the reason.
- **On each employee's record, a Documents button with a count**, opening that person's documents, ready to add another.
- **On a document type:** its name, the number of days, and the four chasing patterns as clearly labelled choices, worded so I can tell them apart without a manual.

---

## 4. What I want to be warned about

- **Nothing is chased until a document is Valid.** A document left in Draft with a date next week is silent. That is deliberate — a draft is unverified — but it means a document forgotten in Draft is a document nobody is chasing. I want that visible in the list, not a surprise.
- **The daily check only runs if the system is running it.** If scheduled work is switched off in this database, no email is ever sent and the screens will still look fine.
- **Renewal replaces the scan.** The previous scan is kept in the history, but the document itself carries only the current one. If somebody renews with the wrong file attached, the correction is another renewal, not an undo.
- **These documents are personal data.** A residence permit scan identifies somebody's immigration status. Access has to be narrow and it has to stay narrow.
- **The to-do goes to the manager on file.** If the employee has no manager recorded, there is nobody to give it to, and only the email is sent.

---

## 5. What is intentionally NOT included (keep the first version honest)

- **No approval workflow.** A document is entered by HR and marked valid by HR. Nobody else approves it, and there is no rejection path.
- **No blocking.** An expired work permit does not stop the person being scheduled, paid, or granted absence. This module tells people; it never prevents anything.
- **No self-service upload.** The employee cannot add or renew their own documents. HR does it. (They receive the emails; they do not act in the system.)
- **No reading of the document.** Nothing extracts a date or a number from the scan. Every date is typed in by a person.
- **No escalation beyond the manager.** One email to the employee, one to-do for the manager. Nothing reaches me, HR, or a director if both are ignored.
- **No identity documents that live on the employee record.** The identification reference and the passport sit on the employee's own record and are warned about by the **Employee Information** module. This module deliberately does not take them over — a document here is a separate record with a type, a renewal path and a history, which those two fields are not. That seam is known and accepted; it is not an oversight.
- **No printable output.** No certificate, no PDF, no export beyond the standard spreadsheet export every list already has.
- **No reminders about the blank forms library.** It has no dates and is never chased.

---

## 6. How we'll know it works (acceptance criteria)

1. I can create a document type "Work permit" with 60 days and the *a set number of days before* pattern, and it appears in the list of types. ✅
2. I can record a work permit against an employee — kind, issue date, expiry date, a scan attached — and it saves with its own reference number. ✅
3. The new document is in **Draft**, and the daily check sends nothing for it. ✅
4. I press **Mark valid** and the state becomes Valid. ✅
5. I try to mark valid a document whose expiry date is yesterday, and I am refused with a message. ✅
6. I try to create a **second valid work permit** for the same employee and I am refused with a message telling me to renew the existing one. ✅
7. I create a work permit for that employee in **Draft** and it is allowed — only *valid* is exclusive. ✅
8. With the type set to 60 days before, I set an employee's work permit to expire in exactly 60 days, run the daily check, and that employee receives an email. ✅
9. The same run creates a **to-do for that employee's manager**, dated the expiry date. ✅
10. I run the daily check on a document that expired yesterday and its state becomes **Expired** without my touching it. ✅
11. With a type set to *every day from N days before until it expires*, three consecutive daily runs inside that window each send an email; a run outside the window sends none. ✅
12. I press **Renew** on a valid document, and I am asked for exactly four things: new issue date, new expiry date, new scan, reason. ✅
13. I try to renew with an expiry date in the past and I am refused; I try an expiry date before the new issue date and I am refused. ✅
14. I renew properly. The document now shows the **new** dates and the **new** scan, is Valid, and its message thread contains a note giving the old expiry date, the new one, and my reason. ✅
15. The document's **renewal history** now has one entry, holding the **old** issue and expiry dates and the **old** scan, with my name and the time. ✅
16. I filter the Documents list to *expiring within 30 days* and get exactly the documents whose expiry date falls in that window. ✅
17. I group the Documents list by employee, by kind, and by state. ✅
18. On an employee's record, the **Documents** button shows the right count and opens only that person's documents. ✅
19. I add a blank "Medical declaration" form to **Forms & Templates** with a file attached, and it is there with no dates and nothing chasing it. ✅
20. **As an ordinary employee** — signed in with no HR role — I can see **my own** documents and **cannot** see a colleague's, and I cannot create, edit or delete any document at all. ✅
