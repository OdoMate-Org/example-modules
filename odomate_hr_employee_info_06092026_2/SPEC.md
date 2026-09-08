# SPEC.md — the business specification this module was generated from

This is the business-level specification the module in this folder was generated
from — code, views, security, demo data, tests, and the user guides in `doc/`.
It is written in the voice of the person who would ask for it: an HR manager who
owns the company's employee master file, uses Odoo every day, and has no
knowledge of how Odoo is built inside. No model names, field names or technical
design appear in it; everything in `models/`, `views/` and `security/` was
derived by OdoMate from the plain requirements below.

**Provenance, stated plainly.** This specification was written by the OdoMate
team as an independent description of what an employee-dependants and
identity-document feature should do. It contains no third-party code, text or
configuration. The module was generated from this document alone.

**What was verified before publication.** The module installs on a freshly
created Odoo 19 Community database on the first attempt with no errors
(41 modules in 16.0s), its own 29 automated tests pass with no failures, its
Ukrainian translation is complete, and all fourteen acceptance criteria in §6
were walked by hand against the running database.

Generated with OdoMate (https://www.odomate.pro) — September 2026, Odoo 19
Community. Published unedited apart from publication metadata (store listing
page, banner and icon).

**Three rounds, all of them the generator's own work.** The module was generated
from this document, then enhanced twice, each time from a written brief and never
by hand:

- **v2** removed an undeclared privilege escalation (the module had granted
  `hr.group_hr_manager` to the admin user on install) and closed the write path on
  the computed joining date so it cannot be overwritten through the ORM, an import
  or the API.
- **v3** fixed a layout fault on the employee form. Odoo renders a `<group>` as a
  grid of alternating label and input cells, and a `<button>` placed directly in a
  group consumes one cell — so the module's send-warning button knocked the
  alternation out of phase and pushed everything below it into the wrong column,
  including Odoo's own passport fields. The generated fix gives each button
  `colspan="2"` and anchors the passport additions on their container rather than
  on a field inside it.

---

## 1. What I want (the problem)

Every time somebody asks me a question about a person, I end up in a spreadsheet.

- *"Who is Anna's emergency contact, and is that number still current?"* — I have a name and a phone number typed into a single line by whoever set the record up. No relationship, no second person, no date of birth for the child we insure.
- *"How many of our people have dependants?"* — I cannot answer without opening records one at a time.
- *"Whose identity document expires this quarter?"* — the document reference is on the record. The date it stops being valid is nowhere.
- And then a new person starts, somebody gives them a login so they can get into the system, and **there is no employee record behind that login**. The person exists in the system and does not exist in HR. We find out two weeks later, usually because their first absence request has nowhere to go.

This costs me three things:

- **I cannot act in an emergency.** One name and one number, of unknown age, is not a plan.
- **I am always late on documents.** I find out an identity document expired when somebody is turned away at a border or a bank.
- **My headcount is quietly wrong.** People with a login and no employee record are invisible to every other thing HR does.

I want the employee record to hold the people and the papers behind the person — and I want the system to stop creating logins that no employee stands behind.

---

## 2. What I want to be able to do

### a) Record the people behind the employee

On each employee, a list of the family members and dependants I hold details for. For each one:

- their **name**,
- **how they are related** to the employee,
- a **contact number**,
- their **date of birth**.

I want the relationship to come from a short list I maintain myself — *spouse, father, mother, son, daughter, guardian* — not free text, so that two people typing "husband" and "Spouse" do not end up as two different things when I come to count.

### b) Mark one of them as the emergency contact

Exactly **one** person in that list can be flagged as the one to call. When I flag someone, the emergency-contact name and number already on the employee record should update to match, so that anybody who only ever looks at that one line still sees the right person. If I flag a second person, the flag moves — it never sits on two.

### c) Not type the spouse twice

The employee's personal details already have a place for a spouse's name and date of birth. When both are filled in and that person is not already in the list, I want them added to the list as the spouse, so I am not maintaining the same fact in two places.

### d) Record identity documents properly

For the **identification reference** the company holds for this person — the national ID, tax number or equivalent — I want two things the record does not currently give me:

- the **date it stops being valid**,
- somewhere to **attach a scan** of it.

For the **passport**, the number and its expiry date are already on the record; I want somewhere to attach a scan next to them.

### e) Be warned before an identity document expires

I want a **daily check** that emails the person before one of those two documents expires.

- Two lead times, set once by an administrator and applied to everyone: how many days ahead to warn about the **identification reference** (about a fortnight is right — these are usually renewed quickly), and how many days ahead to warn about the **passport** (about six months — renewing one takes a season, not a week).
- A **button on the employee record** to send that warning right now, for the times when I want to chase somebody today rather than wait for the daily check.

### f) See when somebody actually joined

I want a **joining date** on the employee that is worked out from the earliest employment record we hold for them, not typed in by hand — because the hand-typed one is wrong on about a third of our people.

### g) See the notice period without going hunting

On the employment record, show the **notice period** the company works to, so the person having the conversation does not have to go and find the policy.

### h) Never have a login without an employee behind it

When somebody is given a **login for internal staff**, I want an **employee record created automatically**, carrying their name and linked to the login in both directions — from the login I can reach the employee, from the employee I can reach the login.

Two conditions on that, because I have been bitten:

- It applies only to **logins for internal staff**. Customer- and supplier-facing logins, and the system's own technical accounts, must not produce employee records.
- An administrator can **switch the behaviour off**, for the case where employees are loaded from somewhere else and the automatic record would be a duplicate.

---

## 3. What I want to see on screen

- **On the employee's personal page, a "Dependants" section** — a simple list I can add rows to: name, relationship, contact number, date of birth, and the emergency-contact flag. This is private information, so it belongs on the private page, not the one colleagues can see.
- **On the same page, the identity block** — the identification reference with its expiry date and its attachment beside it, and the passport with its expiry date and its attachment beside it. I want the two to look the same as each other, so nobody has to think about which is which.
- **On the employee's record, the joining date** — read-only, next to the employment details.
- **On the employment record, the notice period** — read-only, near the salary.
- **In Settings, under the Employees section, two fields**: how many days ahead to warn about the identification reference, and how many days ahead to warn about the passport. Plus the switch that turns off automatic employee creation.
- **On a login, the employee it belongs to**, as a link I can click through.
- **On the employee record, a button that sends the expiry warning now** — one for the identification reference, one for the passport. Each should be greyed out or hidden when there is no expiry date to warn about.

---

## 4. What I want to be warned about

- **Dependant details are private.** Names, dates of birth and phone numbers of somebody's children are the most sensitive thing on the record. They must be visible to the HR team and to nobody else — not to the employee's manager by default, not to colleagues.

  *An earlier draft of this line also said "and to the employee themself". Odoo 19 Community restricts the whole personal page to the HR role and ships no self-service profile screen, so there is nowhere to show an employee their own dependants without building the self-service that §5 excludes. The employee's own access is still enforced underneath — see criterion 14 — so the day self-service is added, the data is already safe.*
- **The emergency contact is one person.** If I flag a second, the first is unflagged. I want that to be obvious rather than something I discover later.
- **Automatic employee creation is a one-way door on the day it is switched on.** Every new internal login from that moment makes an employee record. It will not go back and create records for people who already have logins, and it will not delete an employee if the login is deleted.
- **Changing a lead time does not re-send anything.** If I change the passport warning from 180 days to 90, nobody who was already warned gets warned again, and nobody who fell between the two settings gets caught up. The next warning is the next one due.
- **The warning goes to the person, not to me.** If somebody ignores it, nothing escalates. I find out by looking.

---

## 5. What is intentionally NOT included (keep the first version honest)

- **No general document register.** This module warns about exactly two dates that live on the employee record — the identification reference and the passport. Visas, work permits, driving licences, professional certifications and everything else that expires belong in a dedicated employee-documents module with document types, renewal and history. This module does not try to be that.
- **No self-service.** The employee cannot edit their own dependants or upload their own scan. HR does it.
- **No verification.** Nothing checks that an identification reference is a real number, in the right format, or belongs to the person named.
- **No creating a login from an employee.** The automatic step runs one way only: login → employee. Creating an employee never creates a login.
- **No duplicate detection.** If the same person ends up with two employee records, nothing notices.
- **No payroll and no allowances.** Recording that somebody has three dependants does not make any payment happen. Nothing here reaches into pay.
- **No history of changes.** If a dependant's phone number is corrected, the old one is gone.

---

## 6. How we'll know it works (acceptance criteria)

All fourteen were walked by hand against a fresh Odoo 19 Community install before
publication, including criterion 14, which is exercised as an ordinary employee
rather than as an administrator.

1. I can add three dependants to an employee — a spouse, a child and a parent — each with a name, a relationship from my list, a phone number and a date of birth, and they are all still there after saving and reopening.
2. I can add a new relationship kind ("Guardian") to the list and immediately choose it on a dependant.
3. I flag the spouse as the emergency contact and the employee's emergency-contact name and phone number change to match.
4. I then flag the parent instead, and the flag moves off the spouse — only one person carries it.
5. I fill in a spouse's name and date of birth on the personal page of an employee who has no dependants recorded, and that spouse appears in the dependants list without my typing them again.
6. I set an expiry date on the identification reference, attach a scan, save, reopen, and both are there.
7. I set the warning lead time for identification references to a number of days, set an employee's identification expiry date exactly that many days from today, run the daily check, and that employee receives an email saying the document is about to expire.
8. I run the same daily check again with an employee whose identification expires next year, and **no** email is sent for them.
9. I press the "send the warning now" button on an employee with a passport expiry date and that employee receives the email immediately.
10. The joining date on an employee matches the start date of their earliest employment record, and I cannot type over it.
11. I create a new **internal** login for a new starter, and an employee record appears for them, carrying their name, linked to that login — and from the employee record I can click through to the login and back.
12. I create a **customer-facing** login and **no** employee record appears.
13. I switch the automatic creation off in Settings, create another internal login, and no employee record appears.
14. **As an ordinary employee** — somebody with no HR role at all — I sign in, open a colleague's record, and there is no dependants section for me; nor can I reach their dependants any other way.

   *An earlier draft of this criterion also required that I could see my **own** dependants. That half was unbuildable: Odoo 19 Community gates the personal page on the HR role and has no self-service profile action, so satisfying it would have meant building the self-service that §5 rules out. The half that matters — one employee must not read another's private family details — is kept, and the underlying rule limiting an ordinary employee to their own records is kept with it.*
