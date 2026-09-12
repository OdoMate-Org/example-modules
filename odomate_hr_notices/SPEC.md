# SPEC.md — the business specification this module was generated from

This is the business-level specification the module in this folder was generated
from — code, views, security, demo data, tests, and the user guides in `doc/`.
It is written in the voice of the person who would ask for it: the HR manager who
has to tell two hundred people something and be able to show they were told, who
uses Odoo every day and has no knowledge of how Odoo is built inside. No model
names, field names or technical design appear in it; everything in `models/`,
`views/`, `security/` and `static/src/` was derived by OdoMate from the plain
requirements below.

**Provenance, stated plainly.** This specification was written by the OdoMate team
as an independent description of what an announcements-and-acknowledgements feature
should do. It contains no third-party code, text or configuration. The module was
generated from this document alone.

**What was verified before publication.** The module installs on a freshly created
Odoo 19 Community database on the first attempt with no errors, and its automated
tests pass with no failures and no errors (Odoo's runner reports 0 failed, 0 errors
of 45 tests; `odoo.tests.stats` counts 47, the two numbers disagree by design and
45 is the one that matches the test methods in the file). Its Ukrainian translation
is complete and actually loads: all 12 Python entries and all 6 JavaScript entries
reach a Ukrainian installation, measured with Odoo's own translation loader. The
screens were read off the screen rather than only queried through the data layer —
the register shows two published notices and one expired, the acknowledgement tab
shows 7 of an audience of 21 with both lists of names filled in, and the top-bar
counter opens onto the notice waiting for the reader and the two saved reminders
with their live counts.

**No hand corrections, and no enhancement round.** One version was generated and it
is what ships here. Nothing in it was written or corrected by hand; the only
changes made for publication are the store listing page, the banner, the icon and
the manifest metadata that points at them.

Generated with OdoMate (https://www.odomate.pro) — September 2026, Odoo 19
Community. Published unedited apart from publication metadata (store listing page,
banner and icon).

---

# Announcements and Reminders — Spec (Level 1: Business User)

> **Who wrote this:** the HR manager who has to tell 200 people something and be able to prove they were told. They use Odoo every day and have **no** idea how Odoo is built inside.

**What app this touches:** the **Employees** app — a new **Notices** area — and the top bar of Odoo, where a counter appears for everybody.

---

## 1. What I want (the problem)

Two problems that look different and are the same problem: something needs to reach somebody at the right moment, and today it does not.

**Telling everybody something.** The office is closed on the 24th. The insurance scheme changed. There is a fire drill on Thursday. Today this is an email to a distribution list that is out of date, and a printout on a wall that nobody in the warehouse walks past. Nobody knows who read it. When it matters — a safety notice, a policy change — "we emailed everyone" is not good enough.

**Remembering to look at something.** Six passports expire next month. Four probation periods end in the next two weeks. Three people have birthdays on Friday. Every one of these is a query somebody has to remember to run, and nobody remembers.

I want announcements that go to a **chosen audience**, that people **see when they are in Odoo** rather than in their inbox, and that record **who acknowledged them**. And I want HR to be able to set up **standing reminders** — "show me anything expiring in the next 30 days" — that appear on their own instead of being remembered.

## 2. What I want to be able to do

### a) Write an announcement and choose who it is for

A title, the text, a category (*Policy*, *Safety*, *Social*, *Benefits* — a list we maintain), a priority, and the dates it is live between. Then the audience, which is one of:

- **everybody**,
- **specific people**,
- **whole departments**, or
- **everybody in a given job position**.

### b) Have it approved before it goes out

An announcement is **drafted**, **sent for approval**, and then **published** by an HR manager — or **refused**, with a reason. What goes on the wall of the company gets a second pair of eyes.

### c) Have people actually see it

When it is published, everybody in its audience sees a **counter in the top bar of Odoo** with a number in it. Opening the counter lists what is waiting for them, newest and most urgent first, and clicking one opens it.

### d) Know who has read it

An announcement carries an **Acknowledge** button. Pressing it records that this person read it, and takes it off their counter. On the announcement, HR sees **how many of the audience have acknowledged it and who has not**.

### e) Have it expire on its own

Past its end date, an announcement stops appearing, stops counting, and shows as **expired**. Nobody has to tidy up.

### f) Set up standing reminders (HR only)

A reminder is a saved question with a date in it: *"employees whose identification expires in the next 30 days"*, *"probation ending this week"*. HR chooses what to look at, which date to look at, and the window — **today**, **a number of days ahead**, or **between two dates** — and gives it a name.

When a reminder has something in it, it appears on **HR's own counter** with the number of matching records, and opening it shows exactly those records.

A reminder shows each person **only what they are allowed to see anyway**. It is a shortcut to a list, not a way around permissions.

### g) Keep the two apart

The counter is one thing in the top bar, but announcements and reminders are listed separately inside it, and an ordinary employee **never sees a reminder** — reminders are an HR tool.

## 3. What I want to see on screen

- **A counter in the top bar of Odoo**, for everybody, carrying a number when there is something and nothing when there is not. Opening it shows a short list: announcements first, with their category and date; then, for HR, the reminders that have something in them, each with its count. Each line opens the thing it names. An empty counter says so plainly rather than showing an empty box.
- **A Notices area in the Employees app:** *Announcements* (what is addressed to me), *All announcements* for HR, and under Configuration the *Categories* and the *Reminders*.
- **On an announcement:** the reference, the state bar — *Draft → Waiting for approval → Published*, with *Refused* and *Expired* as the other ends — the title, category, priority, the live-between dates, the audience, and the text. For HR: how many of the audience have acknowledged, and the list of who has not. For everybody else: the **Acknowledge** button, until they press it.
- **On a reminder:** its name, what it looks at, which date, the window, and a **preview count** so HR can see it is finding something before saving it.
- **The whole thing must still work with the top-bar counter gone.** Everything reachable from the counter is reachable from the Employees app menu, by design — see the warning below.

## 4. What I want to be warned about

- **The top-bar counter is new ground for us.** It is the first thing OdoMate has been asked to build that lives in the browser rather than on the server. **If it cannot be built, the announcements and the reminders still work** — through the menus — and we will say so plainly rather than pretend the counter was never wanted.
- **An announcement is not an email.** People see it when they are in Odoo. Somebody who does not open Odoo for a week sees it in a week. For something that cannot wait, send an email as well.
- **Acknowledged means "pressed the button"**, which is not the same as read and understood. It is a record of the press and nothing more. Do not use it as proof of training.
- **A reminder counts what that person may see.** Two HR officers with different access can see different numbers on the same reminder. That is correct, and it will look like a bug the first time somebody notices it.
- **Reminders look at dates, and nothing else.** No amounts, no states, no "and where the status is open".
- **Expired announcements stay** for the record. They stop appearing; they are not deleted.

## 5. What is intentionally NOT included (keep the first version honest)

- **No employee-facing publishing.** Only HR writes announcements. There is no team noticeboard and no comments from readers.
- **No targeting beyond the four audiences.** No "everybody except", no combinations, no tags, no seniority.
- **No delivery by email or SMS from this module.** Odoo can already email a document; this module does not build a campaign tool.
- **No read receipts beyond the Acknowledge button.** Nothing tracks whether the counter was opened or the text scrolled.
- **No scheduled or recurring announcements.** One announcement, one live window.
- **No reminders on anything but a date field**, and no reminders that write, escalate, or notify anybody. A reminder shows a list. It does not create an activity, send a mail, or assign a task — Odoo's own activities already do that, and a reminder that quietly generated activities for 200 employees would be a much worse module.
- **No per-user reminders.** Reminders are configured by HR for HR. An employee's own to-do list is Odoo's activities, which already exist and already have a counter in the top bar.
- **No rich media.** Text and attachments; no images embedded in the counter, no video.

## 6. How we'll know it works (acceptance criteria)

The setup: three employees — one in *Support*, one in *Sales*, one with no department — plus an HR officer and an HR manager, and one employee who is an ordinary user with no HR role at all.

1. I create an announcement for **everybody**, live from today for a week, and send it for approval: it is *Waiting for approval*, with its own reference. ✅
2. **An HR officer cannot publish it.** Calling publish as somebody with the ordinary HR role and not the manager role is refused — tested by calling it, not by looking for the button. ✅
3. **An HR manager publishes it** and the state is *Published*. ✅
4. **Refusing asks for a reason** and records it, and a refused announcement appears to nobody. ✅
5. **A draft announcement appears to nobody**, including its own audience, including HR. ✅
6. **Everybody sees it.** For all three employees, the list of announcements addressed to them contains this one. ✅
7. **A departmental announcement reaches only that department.** Published to *Support* only: the Support employee has it, the Sales employee does not, and the employee with no department does not. ✅
8. **A job-position announcement** behaves the same way against job positions. ✅
9. **A personal announcement** addressed to two named people reaches exactly those two. ✅
10. **Acknowledging works and is personal.** The Support employee acknowledges: their own count drops by one, the announcement records them, and **the Sales employee's count is unchanged**. ✅
11. **HR sees who has not.** On the announcement, the acknowledged count matches the number of people who pressed it, and the list of who has not acknowledged contains the rest of the audience and nobody outside it. ✅
12. **Dates are respected.** An announcement whose live window starts tomorrow appears to nobody today; one whose window ended yesterday appears to nobody and is marked *Expired* by the daily run. ✅
13. **A reminder finds what it says it finds.** A reminder over an employee date field with a 30-day window returns exactly the employees whose date falls in the next 30 days — verified against the same query run by hand. ✅
14. **A reminder with nothing in it does not appear**, and does not show a zero. ✅
15. **Reminders are HR's.** For the ordinary employee, the reminder is absent from the counter entirely and the Reminders configuration screen is unreachable. ✅
16. **A reminder respects the reader's access.** The same reminder counted by two users with different access gives each of them the number of records **they** may read — the count is never computed with elevated rights. ✅
17. **The counter appears in the top bar with a number in it.** Signed in as an employee with two unacknowledged announcements, the top bar shows the notices counter carrying **2**; opening it lists both, each with its title and category; clicking one opens that announcement; after acknowledging, the counter reads **1**. **This one is checked by looking at the rendered screen, and it is the criterion that answers whether OdoMate can write working JavaScript at all.** ✅
18. **Everything works with the counter gone.** With the module's browser code removed from the build, the server side still installs, and every one of criteria 1 to 16 still passes through the Employees menu. **This is checked deliberately, not assumed.** ✅
19. **As an ordinary employee** — `base.group_user`, no HR role — I can read the announcements addressed to me and acknowledge them, and I can read **nothing else**: not a draft, not one addressed to another department, and not the acknowledgement list of my own. Opening one of those **directly at its address** is refused. ✅
20. **No JavaScript is loaded from the internet.** The module's browser code loads no script, style or font from any external address; everything it uses ships in the module or is already part of Odoo. ✅
21. **Ukrainian.** With the Ukrainian locale installed, every label, state, button, category, refusal message **and the text inside the top-bar counter** are in Ukrainian. ✅
