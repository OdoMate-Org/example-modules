# SPEC.md — the business specification this module was generated from

This is the business-level specification the module in this folder was generated
from — code, views, security, demo data, tests, and the user guide in `doc/`.
It is written in the voice of the person who would ask for it: the HR manager who
has to get somebody out of the building properly, who uses Odoo every day and has
no knowledge of how Odoo is built inside. No model names, field names or technical
design appear in it; everything in `models/`, `views/` and `security/` was derived
by OdoMate from the plain requirements below.

**Provenance, stated plainly.** This specification was written by the OdoMate team
as an independent description of what a resignation-and-exit-clearance feature
should do. It contains no third-party code, text or configuration. The module was
generated from this document alone.

**What was verified before publication.** The module installs on a freshly created
Odoo 19 Community database on the first attempt with no errors. Its automated tests
pass on an English install with no failures and no errors — Odoo's own runner
reports 0 failed, 0 errors of 38 tests, which agrees with the 38 test methods in
the file. Its Ukrainian translation loads: 43 of 43 Python messages reach a
`uk_UA` installation, measured with Odoo's own translation loader, along with 36
translated field labels and both menu entries. The screens were read off the screen
rather than only queried through the data layer — pressing *Release* on the demo
resignation refuses it and names the actual outstanding item, its serial number,
its handover reference and the date it was due back.

**One test fails on a Ukrainian install, and that is the translation working.**
`test_release_blocked_by_pending_clearance_line` asserts that the refusal message
contains the English word "clearance". On a `uk_UA` install the message renders in
Ukrainian, so the assertion fails while the behaviour it is checking is correct.
The generator's own risk notes for this version predicted exactly this. It is
recorded here rather than quietly excluded: 38 of 38 pass in English, 37 of 38 in
Ukrainian, and the one failure is an English-only assertion, not a defect in the
module.

**No hand corrections to the generated code.** One defect found after the first
build — a Ukrainian catalogue that was both incomplete and rejected at load time —
was fixed by asking OdoMate for a new version, not by editing the generated code.
Two versions were generated; the second is what ships here, and its change is
confined to `i18n/`.

**What was changed by hand, and it is only publication metadata.** Five keys in
`__manifest__.py`: the store `summary`, the tracked `website` link, the `category`,
the `images` banner reference, and the app `name`, shortened from
"OdoMate HR Resignation & Clearance" to "Employee Resignation & Clearance" so this
listing is named like its six published siblings. No Python, XML, security file,
translation or test was touched.

**Two limitations that are defects rather than scope.** Both are disclosed on the
listing page as well as here. When company property is still outstanding the
clearance checklist shows *Company Property* twice — once as the ordinary pending
line and once as the blocked line naming what is out — and both have to be cleared;
with nothing outstanding the checklist is exactly the items configured. And the
manifest does not declare a dependency it actually has: the notice period is read
from a field added by *Employee Dependants & Identity Documents*, which arrives
anyway because the custody register this module depends on depends on it in turn.
Neither blocks installation or use; both are ours rather than the generator's.

Generated with OdoMate (https://www.odomate.pro) — September 2026, Odoo 19
Community. Published unedited apart from the publication metadata named above.

---



# Resignation and Clearance — Spec (Level 1: Business User)

> **Who wrote this:** the HR manager who has to get somebody out of the building properly. They use Odoo every day and have **no** idea how Odoo is built inside.

**What app this touches:** the **Employees** app — a new **Resignations** area — and the **Custody** register from the *Company Property in Custody* module, which it reads.

---

## 1. What I want (the problem)

Somebody resigns. From that moment there is a list of things that must happen, in an order, involving five different people, and the list lives in my head.

- The notice period is in their contract and nobody looks it up, so the leaving date is agreed in a corridor and then argued about.
- The manager needs to approve it, the handover needs doing, IT needs to close the accounts, the laptop needs to come back — and each of those is a separate conversation I have to start and remember to finish.
- **The laptop is the one that actually costs us money.** Somebody leaves still holding a phone and a laptop and an access card, and we find out weeks later, or never, because the person who would have noticed is the person who left.
- We never find out why people go. We mean to ask, and by the time we get round to it they have gone.
- And afterwards the employee record sits there active, on the org chart, in the payroll list, because nobody switched it off.

I want the resignation written down, approved once by the right people, a **checklist that cannot be finished while the company's property is still out with the person**, an exit interview that is actually sent, and an employee record that gets switched off at the end — properly, on the right date, with the reason recorded.

---

## 2. What I want to be able to do

### a) Record the resignation

A record holds: **who is leaving**, the **date they told us**, the **last day they want**, the **reason** in their own words, and the **kind of leaving** it is — resigned, dismissed, retired — chosen from the list the system already keeps.

### b) Work out the real last day from the notice period

Their contract already says how many days' notice they owe. The system reads it, adds it to the date they told us, and proposes a **last working day**. I can override it — people leave early, people are asked to stay on — but the proposal comes from the contract, not from a corridor.

### c) Approve it, in two steps if we want them

- The resignation is **confirmed**, which is the moment it becomes real.
- Their **line manager** approves — a step a company can switch off if it does not want it. The manager gets a to-do, not an email they will miss.
- Then **HR approves**, which fixes the last working day and opens the clearance.
- Or it is **refused**, with a reason in writing. Or **withdrawn**, because people change their minds, and a withdrawn resignation leaves the person exactly as they were.

### d) Get a clearance checklist, made from a template

We keep a list of the **things that must be cleared** — IT accounts, company property, handover notes, finance, keys and passes — each with who is normally responsible. When HR approves a resignation, the checklist is created from that list, one line per item, each assigned to its responsible person with a to-do.

Each line is **pending**, **cleared**, or **blocked**, and a blocked line carries a **remark** saying what is in the way. I can see, at a glance, how much of the checklist is done.

### e) Have the checklist know about the company property, without anyone remembering to check

**This is the part that matters most and it is the thing no checklist has ever done for us.**

When HR approves the resignation, the system looks at what the person is **still holding** in the custody register — the items handed to them and not yet returned — and:

- puts a line on the checklist for **returning company property**, listing **each item by name**, with the reference of the handover record and the date it was due back;
- marks that line **blocked**, because it is not something anyone can tick;
- and **refuses to let the person be released** while any item is still out, saying which items.

When the items are returned in the custody register, the line can be cleared and the release goes ahead. A person who is holding nothing gets a checklist with nothing blocked, and the whole thing takes four seconds.

On the resignation itself, I want to see **how many items they are still holding**, and be able to open that list.

### f) Send an exit interview that actually gets sent

Choose a questionnaire, press send, and the person gets it — before their last day, while they still care enough to answer. The answers come back into the questionnaire's own results, where they can be read alongside everybody else's, and the resignation shows whether it was answered.

### g) Release the person, once and properly

A single **Release** step, available only when the checklist is complete and nothing is blocked. It:

- records the **release date**,
- writes the **departure date and the reason** onto the employee's own record, where the rest of Odoo looks for them,
- **ends their contract** on that date, so payroll stops producing payslips for somebody who has gone,
- and **archives** the employee record, and the login attached to it.

### h) Have it happen on the day, not before

The release is prepared in advance and happens **on the last working day** — a daily check releases anybody whose day has arrived and whose checklist is finished. Nobody has to be at their desk on the right morning.

### i) Not lose the trail

One active resignation per person at a time. A withdrawn or refused one stays on the record; it is history, not a mistake to be deleted.

---

## 3. What I want to see on screen

- **A Resignations area in the Employees app** with two screens: **Resignations**, and under Configuration the list of **clearance items** we require.
- **On a resignation:** the reference number across the top, the state as a bar — *Draft → Confirmed → Manager approved → Clearance → Released*, with *Refused* and *Withdrawn* as the ends of the other paths — the employee, their department and job, the date they told us, the notice period read from their contract, the proposed last working day and the agreed one, the kind of leaving, and their reason. Underneath, the message thread.
- **The clearance checklist as a table on the resignation itself:** the item, who is responsible, the state — *pending*, *cleared*, *blocked* — the remark, and the date it was cleared. **A blocked line must be visually obvious without reading it.** Above the table, how far through the checklist we are.
- **A counter for what they are still holding**, reading the custody register, opening exactly those records. Zero is a perfectly good answer and should read as zero, not as an empty box.
- **The exit interview in a section of its own:** which questionnaire, whether it has been sent, whether it has been answered, and a way to open the answer.
- **The buttons, and when each appears:** *Confirm* (draft only) · *Manager approve* (confirmed only, and only for the manager or HR) · *Approve* (confirmed or manager-approved) · *Refuse* (before approval) · *Withdraw* (any time before release) · *Send exit interview* (from approval onwards) · *Release* (only once the checklist is complete).
- **In the list:** reference, employee, department, last working day, how far the clearance has got, state.

---

## 4. What I want to be warned about

- **The property check is a snapshot taken when HR approves, plus a live check at release.** The checklist line lists what was out **at approval**; the refusal to release reads the register **at that moment**. Something handed to a leaver *after* their resignation was approved will still block the release, even though it is not on the line — which is the right way round, but it means the line and the message can disagree, and the message is the one to believe.
- **Releasing is not reversible from here.** It archives the employee and their login and ends their contract. Undoing it is an administrator's job in Odoo, not a button on this screen.
- **The notice period comes from the contract, and if the contract does not have one, it is zero.** The proposed last day will then be the day they told us, which is obviously wrong and obviously visible. Fix the contract, not the resignation.
- **Nobody is stopped from resigning.** Outstanding property blocks the *release*, not the resignation. A person can leave the building; the record stays open until the laptop comes back.
- **No money is calculated.** Final settlement, outstanding loans, unused leave and last salary are not computed here, and no payslip is created. What the person is owed and what they owe is worked out by the people who do that.
- **The daily check releases people.** It is a real automatic action with real consequences. A resignation left in a finished state with a past date will be released without anybody pressing anything — which is the point, and is worth knowing.

---

## 5. What is intentionally NOT included (keep the first version honest)

- **No final settlement and no settlement payslip.** No pending salary, no loan or advance recovery, no leave encashment, no net figure. It is the single biggest thing the original does that this does not, and it is deliberate: settlement pulls in payroll, loans and advances all at once, and getting it half right is worse than not doing it.
- **No dismissal workflow.** This is the process for somebody leaving of their own accord. A dismissal can be recorded through it — the kind of leaving is a choice — but there is no disciplinary trail, no warnings, no appeal.
- **No handover-to-a-named-successor process.** There is a place to write handover notes; there is no task list, no transfer of records, no reassignment of anything.
- **No exit-interview reporting.** The answers live in the questionnaire's own results, where they can already be analysed. Nothing here counts reasons for leaving or draws attrition charts — that is the dashboard's job, later in the suite.
- **No notice-period rules beyond the number of days on the contract.** No bands by seniority, no garden leave, no pay in lieu.
- **No blocking of leave, expenses or timesheets** during the notice period.
- **No approval chain beyond the two steps.** One manager, one HR officer.
- **No self-service.** An employee cannot resign from a portal screen. They tell somebody, and HR records it.
- **No document generation.** No reference letter, no release certificate, no printable clearance sheet.

---

## 6. How we'll know it works (acceptance criteria)

The setup for criteria 9–15: an employee who is **still holding two items** in the custody register — a laptop and a projector, both handed over and not yet returned — and one item they have already given back.

1. I record a resignation for that employee: it is created in **Draft** with its own reference number, and the **notice period is filled in from their contract** without my typing it. ✅
2. The **proposed last working day** is the date they told us plus their notice period, counted in days. ✅
3. I override the last working day with a later one and it holds. ✅
4. I **Confirm**: the state is *Confirmed* and their **line manager gets a to-do**. ✅
5. The manager approves and the state is *Manager approved*. ✅
6. With manager approval **switched off** for the company, a new resignation confirmed goes straight to waiting for HR, and no manager to-do is created. ✅
7. I **Refuse** one, am asked for a reason, type one, and it is *Refused* with the reason on it. ✅
8. I **Withdraw** an approved one: the employee is untouched — still active, no departure date, contract unchanged. ✅
9. I try to record a **second** active resignation for the same employee and I am refused. ✅
10. **HR approves.** The **clearance checklist appears**, one line per configured clearance item, each assigned to its responsible person, each with a to-do for that person. ✅
11. **The property line knows what they are holding.** The checklist carries a line for returning company property, marked **blocked**, whose remark names **both** items — the laptop and the projector — **by name**, with **each handover record's reference** and **the date each was due back**. ✅
12. **The counter is right.** The resignation shows they are still holding **2**, and pressing it opens exactly those two custody records — not the one already returned. ✅
13. **Release is refused while property is out.** I clear every other line and press **Release**: I am refused, with a message **naming both items**. ✅
14. I mark the **laptop returned** in the custody register and press Release again: still refused, and the message now names **only the projector**. ✅
15. I mark the **projector returned**: the blocked line can now be cleared, and with every line cleared **Release succeeds**. ✅
16. **The empty case.** For an employee holding **nothing**, HR approval produces a checklist with **no blocked property line**, the counter reads **0**, and Release goes through with no message about custody. ✅
17. **Release does what it says.** Afterwards: the employee's own record carries the **departure date** and the **reason for leaving**; their **contract is ended** on that date; the employee record and their **login are archived**. ✅
18. **The daily check.** A resignation whose checklist is complete and whose last working day is **yesterday** is released by the daily run. One whose day is **next month** is not. One whose day has passed but whose checklist has a pending line is **not** released. ✅
19. **The exit interview.** I pick a questionnaire and press send: the person receives it, the resignation shows it as sent, and after they answer it shows as answered and opens their answer. ✅
20. **Open the resignation and look at it.** The clearance checklist renders as a table with every column headed, each line's state readable, and **the blocked line visibly distinct from the pending ones without having to read the text**; the progress figure above it matches the lines below it; the "still holding" counter renders as a button carrying a number; the state bar shows the right stage; and the exit-interview section renders as a labelled block rather than three loose fields. **This one is checked by looking at the rendered form on screen, not by reading the values behind it.** ✅
21. **As an ordinary employee** — signed in with `base.group_user` and no HR role — I see **no Resignations menu**, I can read **no** resignation including my own, and opening one **directly at its address** is refused. ✅
22. **As the person responsible for a clearance line** — an ordinary `base.group_user` who is not HR — I can see **the lines assigned to me** and mark them cleared or blocked with a remark, and I can see **nothing else**: not another line on the same resignation, not the resignation's reason, not another employee's resignation. ✅
23. **Without the custody module there is nothing to install.** With `odomate_hr_custody` uninstalled, this module cannot be installed at all — Odoo refuses it for an unmet dependency. Criteria 11, 12, 13, 14, 15 and 16 read the custody register's own records directly, and no field in core Odoo carries what they read. ✅
