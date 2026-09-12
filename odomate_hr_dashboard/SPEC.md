# SPEC.md — the business specification this module was generated from

This is the business-level specification the module in this folder was generated
from — code, views, security, tests, and the user guides in `doc/`. It is written
in the voice of the person who would ask for it: the HR manager who is asked, in a
management meeting, how many people we have, how many left this year and who is off
far more than everybody else. No model names, field names or technical design appear
in it; everything in `models/`, `views/`, `security/` and `static/src/` was derived
by OdoMate from the plain requirements below.

**Provenance, stated plainly.** This specification was written by the OdoMate team as
an independent description of what an HR overview should do. It contains no
third-party code, text or configuration. The module was generated from this document
alone.

**What was verified before publication.** The module installs on a freshly created
Odoo 19 Community database on the first attempt with no errors — with demo data,
without demo data, and with a Ukrainian interface — and its automated tests pass with
no failures and no errors (Odoo's runner reports 0 failed, 0 errors of 22 tests;
`odoo.tests.stats` counts 24, the two numbers disagree by design and 22 is the one
that matches the test methods in the file). Its Ukrainian translation is complete and
actually loads: all 14 Python entries reach a Ukrainian installation, measured with
Odoo's own translation loader rather than by counting lines in the catalogue.

**Two generated versions, and no hand correction to the code.** The first version was
generated from this specification. The second was an enhancement round that fixed one
defect — the Ukrainian translations of server-side strings never loaded, because the
shipped `.pot` overwrote the `.po`'s markers when Odoo merged the two. OdoMate found
and fixed that itself, by deleting the `.pot`; no Python, XML, JavaScript, security
file or test was touched. Nothing in this module was written or corrected by hand.

**One hand edit, disclosed.** The app `name` in `__manifest__.py` was shortened for
publication, from *OdoMate HR Overview Dashboard* to *Employee Turnover & Absence
Dashboard*, so this listing is named like its siblings on the Apps Store rather than
leading with our own brand. The `README.rst` title and the `description` heading were
changed to match. That is a change to a generated field and is named here as one; it
alters no behaviour. The other publication changes are the store listing page, the
banner, the icon and the manifest metadata that points at them.

**One known defect is disclosed rather than fixed.** *Off today* builds its day
boundaries from the reader's own date without converting to UTC, so in a database
spread across far-apart time zones an employee at the very edge of the day can be
counted a few hours early or late. OdoMate's own analysis found it; it is documented
in the user guide's Limitations and on the listing page rather than quietly corrected.

Generated with OdoMate (https://www.odomate.pro) — September 2026, Odoo 19 Community.
Published unedited apart from the app name and publication metadata (store listing
page, banner and icon).

---


# HR Overview — Spec (Level 1: Business User)

> **Who wrote this:** the HR manager who is asked, in a management meeting, how many people we have, how many left this year, and who is off this week. They use Odoo every day and have **no** idea how Odoo is built inside.

**What app this touches:** the **Employees** app — a new **HR Overview** area — reading time off, employee records and, where they are installed, the rest of this suite.

---

## 1. What I want (the problem)

Once a month I am asked four questions and I answer three of them badly.

- **"How many people do we have, by department?"** I can get this — it is on the Departments screen — but I get it as of right now, and the question is usually about a month that has finished.
- **"How many joined and how many left this year?"** I count them by hand off a spreadsheet I maintain in parallel, because nothing in Odoo lines up joiners against leavers over time.
- **"What is our turnover?"** Same spreadsheet, and I am never quite sure I have used the same denominator as last quarter.
- **"Who is off far more than everybody else?"** Total days off is easy and it is the wrong measure. The person who takes one three-week holiday is not the problem. The person who takes eleven separate single days is. Nothing I have distinguishes the two.

And separately: **what is waiting for me across all of this** — loans to approve, advances, resignations, transfers, announcements — is five different screens.

I want one place that answers those, and I want the numbers to be the same numbers next month.

## 2. What I want to be able to do

### a) See the shape of the company at a glance

Headcount now, how many joined this month, how many left this month, how many are off today, and the turnover rate for the period — each one a number I can press to see the people behind it. A number I cannot open is a number I cannot trust.

### b) Look at joiners and leavers over time

A list of every arrival and every departure as its own line — the date, the person, the department, and for a departure the reason — so I can group it by month, by department or by reason and get a chart without asking anybody.

### c) Measure absence properly, not just count days

For each employee, over a period: **how many separate absences** they had, **how many days** in total, and the two combined into the standard **Bradford factor** — occurrences × occurrences × days — which is the measure that makes eleven single days look worse than one three-week holiday. Sorted worst first.

### d) See what is waiting for approval across the whole suite

One list of things sitting in an approval state — loans, salary advances, resignations, transfers, announcements — for the modules that are actually installed. If a module is not installed it is simply not there, without an error and without an empty row.

### e) Not have a screen that lies about permissions

An HR manager sees the company. An HR officer sees what an HR officer may see. **An ordinary employee does not get this screen at all.** Headcount, turnover and absence rankings are management information.

## 3. What I want to see on screen

- **An HR Overview in the Employees app**, opening on a row of figures: *Headcount* · *Joined this month* · *Left this month* · *Off today* · *Turnover*. Each is a number with a label, and each opens the records it counts.
- **Under it, the ways into the detail:** *Joiners and leavers*, *Absence by employee*, *Headcount by department*, *Waiting for approval*.
- **Joiners and leavers** as an ordinary Odoo list that can be grouped and charted — by month, by department, by reason — because that is what turns it into the chart somebody asks for in the meeting.
- **Absence by employee** as a list sorted by the Bradford factor, worst first, with occurrences and days beside it, and the same list available as a chart.
- **A period selector** that the figures respect, defaulting to the current year.
- **Honest empty states.** A company with no departures this month shows a zero, not a blank.

## 4. What I want to be warned about

- **This is a smaller dashboard than the one it replaces, and deliberately so.** The original is nearly 6,000 lines, more than half of it browser code, and much of what it draws Odoo 19 now draws by itself. Ours adds the four things Odoo genuinely does not have and uses Odoo's own screens for the rest. Section 5 lists exactly what we are not building.
- **Turnover is a definition, not a fact.** Ours is *departures in the period ÷ average headcount over the period*. Somebody will compare it against a figure calculated a different way and the two will not match. The definition must be visible on the screen, not buried.
- **The Bradford factor rewards nothing and blames nobody.** It is a screening measure. A high score can be one long illness recorded as several absences. It is a starting point for a conversation, not evidence.
- **Only approved, finished time off counts** towards absence. A request still waiting is not an absence yet.
- **The waiting-for-approval list depends on which modules are installed** and will change when one is added.
- **Historical headcount is as good as the employee records are.** If somebody was added to Odoo three years after they joined, with no start date, they will not appear as a joiner. The overview reports what the records say.

## 5. What is intentionally NOT included (keep the first version honest)

The original dashboard draws about twenty panels. We are building four things and reusing Odoo for the rest. What we are **not** doing, and why:

- **No personal panel** — your own attendances, your own timesheets, your own expenses, your own leave balance. Odoo 19 already gives every employee all of that in their own apps.
- **No department kanban of our own.** Odoo 19's **Departments** screen already shows, per department: total employees, absent today, time off to approve, allocations to approve, new applicants, newly hired and expenses to approve. Rebuilding it would be worse and would drift.
- **No time-off analysis of our own.** Odoo 19 ships *Time Off Analysis* — a pivot and a graph over every leave, by employee, type, department and month. Ours adds only what that cannot express: **occurrences** and the **Bradford factor**.
- **No recruitment funnel, no attendance charts, no timesheet charts, no skills panel, no project-task panel.** Each of those has a native analysis screen in its own app.
- **No birthdays, no upcoming events, no announcements panel.** Birthdays are in the calendar; announcements have their own counter in the top bar from module 10.
- **No payroll figures of any kind**, and — this matters — **no granting of payslip or contract access to ordinary users.** The original ships access rules giving every employee read access to `hr.payslip` and `hr.version`, which means everybody in the company can read everybody's salary. We do not ship that, at any size of benefit.
- **No PDF report.** The lists print through Odoo's own export.
- **No configurable dashboard.** No drag-and-drop tiles, no saved layouts, no per-user arrangement.
- **No external chart library.** The original loads Chart.js from a public CDN, which fails on an offline install and puts a third-party script in every customer's back office.

## 6. How we'll know it works (acceptance criteria)

The setup: a demo company with employees across at least three departments, some with a recorded start date this year, at least one recorded as having left, and approved past time off including one employee with **several separate short absences** and one with **a single long one**.

1. **The overview opens** for an HR manager and shows the five figures, each with a label and a number. ✅
2. **Headcount is right.** The number matches a count of active employees for the company, done independently. ✅
3. **Joined this month is right**, and pressing it opens exactly those people. ✅
4. **Left this month is right**, and pressing it opens exactly those people. ✅
5. **Turnover matches its own definition** — departures in the period ÷ average headcount over the period — recomputed by hand from the same data. ✅
6. **Off today is right**, counting only approved time off covering today. ✅
7. **The period selector works.** Setting it to last year changes every figure that depends on the period, and leaves headcount-now alone or clearly labels what it is showing. ✅
8. **Joiners and leavers is a real list.** One line per arrival and per departure, with the date, the person, the department and — for departures — the reason; and it can be grouped by month and by department in the ordinary Odoo way. ✅
9. **The two directions are distinguishable** without reading the date: an arrival and a departure are visibly different in the list. ✅
10. **The Bradford factor is right.** For the employee with 4 separate absences totalling 6 days, the list shows occurrences 4, days 6 and factor **96** (4 × 4 × 6). Computed by hand from the same records. ✅
11. **It sorts the way it must.** The employee with several short absences ranks **above** the employee with one long absence, even though the second has more days. ✅
12. **Only approved, finished time off counts.** A request in *waiting for approval*, and one approved but starting next week, appear in neither the occurrences nor the days. ✅
13. **Waiting for approval shows what is installed.** With the loan, advance, resignation and transfer modules installed, the list contains their pending records, each opening the right record. ✅
14. **And nothing breaks when they are not.** On a database with **none** of the other suite modules installed, the overview opens, the list is simply shorter, and there is no error and no empty placeholder row. ✅
15. **A second company is a second set of numbers.** Switching companies changes the figures, and no figure ever mixes the two. ✅
16. **As an HR officer** — `hr.group_hr_user`, not manager — the overview opens and shows figures consistent with what that role may read, with no access error anywhere on the screen. ✅
17. **As an ordinary employee** — `base.group_user`, no HR role — there is **no HR Overview menu**, the overview cannot be opened by its address, and **neither analysis list can be read**. In particular, that user gains **no** read access to payslips, contracts or employee records they did not already have. ✅
18. **Open the overview and look at it.** The five figures render as a labelled row that does not wrap into an unreadable stack at an ordinary window width; each figure's label is legible above or beside its number; the turnover definition is visible on the screen rather than only in documentation; and the four ways into the detail are visible without scrolling. **This one is checked by looking at the rendered screen, not by reading the numbers behind it.** ✅
19. **Nothing is loaded from the internet.** No script, style or font is fetched from any external address. ✅
20. **Ukrainian.** With the Ukrainian locale installed, every label, figure caption, column heading and menu on the overview is in Ukrainian. ✅
