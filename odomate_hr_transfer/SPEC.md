# SPEC.md — the business specification this module was generated from

This is the business-level specification the module in this folder was generated
from — code, views, security, demo data, tests, and the user guides in `doc/`.
It is written in the voice of the person who would ask for it: the HR manager who
moves people around, who uses Odoo every day and has no knowledge of how Odoo is
built inside. No model names, field names or technical design appear in it;
everything in `models/`, `views/` and `security/` was derived by OdoMate from the
plain requirements below.

**Provenance, stated plainly.** This specification was written by the OdoMate team
as an independent description of what an employee-transfer feature should do. It
contains no third-party code, text or configuration. The module was generated from
this document alone.

**What was verified before publication.** The module installs on a freshly created
Odoo 19 Community database on the first attempt with no errors, and its automated
tests pass with no failures and no errors (Odoo's runner reports 0 failed, 0 errors
of 32 tests). Its Ukrainian translation is complete and actually loads: all 18
Python code entries reach a Ukrainian installation, measured with Odoo's own
translation loader, where the version before this one loaded none of them. The
screens were read off the screen rather than only queried through the data layer —
the register shows the applied demo transfer as "Research & Development →
Customer Success", the approved one carries the waiting-for-its-date banner, and
the employee's own form shows the Transfers button beside a two-entry version
history.

**No hand corrections.** Three defects found after the first build — a transfer
that reported its "from" values as the new ones once applied, a Ukrainian
catalogue Odoo would not load, and a demo record showing a blank "From Department"
— were each fixed by asking OdoMate for a new version, not by editing the
generated code. Four versions were generated; the fourth is what ships here.

Generated with OdoMate (https://www.odomate.pro) — September 2026, Odoo 19
Community. Published unedited apart from publication metadata (store listing page,
banner and icon).

---


# Employee Transfer — Spec (Level 1: Business User)

> **Who wrote this:** the HR manager who moves people around. They use Odoo every day and have **no** idea how Odoo is built inside.

**What app this touches:** the **Employees** app — a new **Transfers** area — and the employee's own record, which the transfer writes to.

---

## 1. What I want (the problem)

People move. Somebody changes department, gets a new job title, moves to another office, gets a new manager, or goes to work for another company in the group. Today all of that is done by opening the employee's record and typing over what is there.

- **The old information disappears.** Once I type the new department over the old one, nothing anywhere says the person used to be somewhere else. Six months later, "when did she move to Support?" has no answer.
- **It happens on the wrong day.** The move is agreed for the first of next month, but I either do it now — and the reports are wrong for a month — or I write myself a note and forget.
- **Nobody approves it.** Anyone with access to the employee record can change somebody's department and their manager, silently.
- **A move between our companies is worst of all.** It gets done by creating a *new* employee record in the other company and switching the old one off. Then the person has two records, their time-off balance is on the old one, their loan is on the old one, and their years of service start again from zero.

I want a move to be a **thing that is written down, approved, dated, and then applied** — and I want the employee's history to still be there afterwards.

## 2. What I want to be able to do

### a) Record the move

A transfer record holds: **who is moving**, **the date it takes effect**, **what changes** — any combination of department, job position, work location, manager, and company — and **why**.

Only what I fill in changes. If I set a new department and nothing else, the job position, the location and the manager stay exactly as they are.

### b) See what it will actually do, before it happens

On the transfer I want the **current value and the new value side by side**, for each of the five things. Not a form of empty boxes: "Department: Support → Professional Services" is what tells me I have filled it in right.

### c) Have it approved

- **Draft** — I am still writing it.
- **Waiting for approval** — I have sent it.
- **Approved** — an HR manager has agreed. For a move to another company, the approving person must be somebody who actually works with that company; approving a move into a company you cannot see is how people end up in the wrong place.
- **Refused**, with a reason, or **Cancelled**.

### d) Apply it on the day it says, not the day I pressed the button

An approved transfer dated the first of next month **takes effect on the first of next month**. I do not have to be at my desk that morning, and I do not have to pre-date anything.

### e) Keep the history

This is the point of the whole module. After the move, the employee's record must still show that **before this date they were in the old department**, and **from this date they are in the new one**. Both, on the same person, on one timeline — not two employee records, not an overwritten field.

A move between our companies is the same person moving, not a new person starting. Their time off, their loans, their documents and their years of service go with them because they are still the same record.

### f) See where somebody has been

From an employee, open the list of their moves. From the Transfers list, filter by department, by company, by date, and see how many people moved and where they went.

## 3. What I want to see on screen

- **A Transfers area in the Employees app**, and a **Transfers** button on the employee's own record showing how many moves that person has had.
- **On a transfer:** the reference number, the state as a bar — *Draft → Waiting for approval → Approved → Applied*, with *Refused* and *Cancelled* as the other endings — the employee, the effective date, and then **the five change rows as before-and-after pairs**, each showing what it is now and what it becomes. Underneath: the reason, and the message thread.
- **The buttons, and when each appears:** *Send for approval* (draft only) · *Approve* (waiting only, HR manager only) · *Refuse* (before approval) · *Apply now* (approved, and only if the effective date has arrived) · *Cancel* (any time before it is applied).
- **In the list:** reference, employee, effective date, from-department, to-department, state.
- **An honest empty state.** A transfer that changes nothing is not a transfer, and the screen should not let me save one.

## 4. What I want to be warned about

- **Applying a transfer cannot be undone from this screen.** It writes a new page into the employee's history. To reverse it you record another transfer moving them back — which is the truthful thing to do anyway, because it is what happened.
- **The effective date must be later than the employee's most recent change.** History is a line, and putting a page in the middle of it is not something this module does. Back-dating a move is an administrator's job, deliberately.
- **A move to another company changes which company owns the employee record from that date on.** Their past payslips, expenses and time off stay with the company that had them at the time, which is correct — but it does mean the old company's reports keep counting the person for the months they were there.
- **The manager and the company are not part of the dated history.** Odoo keeps the department, job position and work location on a timeline; it keeps the manager and the owning company on the person. So "who was her manager in March" is not a question this module can answer, and it does not pretend to.
- **Nothing is sent to the employee.** No letter, no notification. The people involved are told by their managers, as they are now.

## 5. What is intentionally NOT included (keep the first version honest)

- **No transfer of anything but the employee record.** Open tasks, projects, equipment in their custody, approvals waiting on them — none of it is reassigned. Somebody has to do that by hand, and this module does not pretend otherwise.
- **No pay change.** A transfer does not touch salary, wage, contract dates or payroll structure. If the move comes with a raise, that is a separate change to their contract.
- **No two-sided handshake.** One approval, by an HR manager who can see the target company. The original this replaces makes the receiving branch press *Receive*; that is a second inbox to watch and it does not make the move any more real.
- **No bulk transfers.** One person per record. Moving a whole department is fifteen records, and that is on purpose — each one is a decision.
- **No org-chart preview.** No before-and-after tree, no "who reports to whom afterwards" simulation.
- **No approval chain, no delegation, no transfer types.** One state machine, one approver group.
- **No letters or certificates.** Nothing is printed.

## 6. How we'll know it works (acceptance criteria)

The setup for criteria 1–12: an employee whose record shows **one** entry in their history — say department *Support*, job *Consultant*, location *Office 1* — and a second company in the database.

1. I create a transfer for that employee, set the effective date to **the first of next month**, choose a new department, and save. It is **Draft**, with its own reference number, and the department row reads **Support → Professional Services**. ✅
2. **The before-and-after is real.** Every row I have not filled in shows the current value on the left and **nothing** on the right, and the record makes clear that those things do not change. ✅
3. **A transfer that changes nothing cannot be saved.** With no target set at all, saving is refused with a message that says so. ✅
4. **The effective date cannot be earlier than the employee's latest history entry.** Setting it to last month is refused, and the message says which date it must be after. ✅
5. I **Send for approval**: the state is *Waiting for approval*. ✅
6. **An HR officer cannot approve.** Signed in as somebody with the ordinary HR role and not the manager role, the *Approve* button does nothing for me — and calling it directly from outside the screen is refused too. ✅
7. **An HR manager approves** and the state is *Approved*. The *Apply now* button does **not** appear, because the date has not arrived. ✅
8. **Refusing asks for a reason**, records it, and leaves the employee untouched. ✅
9. **The day arrives.** With the effective date set to **today**, the daily run applies the transfer: the state becomes *Applied*. ✅
10. **The history is intact — this is the criterion the module exists for.** Afterwards the employee has **two** entries in their history: the original one, still dated as it was and still saying *Support*, and a new one dated the effective date saying *Professional Services*. **The first entry is unchanged.** Not one entry with a new value in it. ✅
11. **Only what was asked for changed.** In the new entry, the job position and the work location are **the same values as before** — carried across, not emptied. ✅
12. **A future move waits.** For a transfer dated next month, after approval the employee's *current* department is still the old one today, and the new entry is sitting in their history dated ahead. ✅
13. **A move between companies keeps one person.** After applying a transfer to the second company: there is still exactly **one** employee record for that person, it is **active**, it now belongs to the new company, and their time-off records, documents and history are all still attached to it. **No second employee record was created, and nothing was archived.** ✅
14. **Approving a move into a company you cannot see is refused.** As an HR manager whose access covers only the first company, approving a transfer into the second is refused with a message naming the company. ✅
15. **Applied is final.** An applied transfer cannot be edited, cancelled or applied a second time — through the screen or from outside it. ✅
16. **The employee's own record shows their moves.** A counter on the employee opens exactly that person's transfers. ✅
17. **As an ordinary employee** — signed in with `base.group_user` and no HR role — I see **no Transfers menu**, I can read **no** transfer including my own, and opening one **directly at its address** is refused. ✅
18. **Open a transfer and look at it.** The five change rows render as labelled before-and-after pairs, aligned, with the arrow or column heading making the direction obvious; rows with no change are visibly not changing rather than looking like empty required fields; the state bar shows the right stage; and the reference number is legible at the top. **This one is checked by looking at the rendered form on screen, not by reading the values behind it.** ✅
19. **Ukrainian.** With the Ukrainian locale installed and the interface set to Ukrainian, every label, state, button and refusal message on the transfer screen is in Ukrainian. ✅
