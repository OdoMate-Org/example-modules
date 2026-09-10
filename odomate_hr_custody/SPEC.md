# SPEC.md — the business specification this module was generated from

This is the business-level specification the module in this folder was generated
from — code, views, security, demo data, tests, and the user guides in `doc/`.
It is written in the voice of the person who would ask for it: the HR manager who
also ends up owning "who has the company laptop", who uses Odoo every day and has
no knowledge of how Odoo is built inside. No model names, field names or technical
design appear in it; everything in `models/`, `views/` and `security/` was derived
by OdoMate from the plain requirements below.

**Provenance, stated plainly.** This specification was written by the OdoMate team
as an independent description of what a company-property custody feature should do.
It contains no third-party code, text or configuration. The module was generated
from this document alone.

**What was verified before publication.** The module installs on a freshly created
Odoo 19 Community database on the first attempt with no errors (44 modules in
27.37s), its automated tests pass with no failures and no errors (Odoo's runner
reports 33 tests, 0 failed, 0 errors), its Ukrainian translation file is complete
(117 of 117 strings, covering field labels and menu entries as well as view text),
and all twenty acceptance criteria were walked by hand against the running
database. The screens and the printed handover document were also read off the
screen rather than only queried through the data layer.

**One known defect, disclosed rather than hidden.** On a Ukrainian-language
installation two blocks of prose still render in English — the undertaking
paragraph on the handover document, and the guidance note in the refuse-extension
dialog. Both have complete, correct Ukrainian in `i18n/uk.po`; Odoo does not apply
it because each block wraps across more than one source line. Every other string
on those screens, including single-line text in the same files, translates
correctly. An English installation is unaffected. This is queued for the next
generated revision and will not be fixed by hand.

**One correction applied by hand, and why.** The Ukrainian catalogue shipped complete
and correct, and Odoo loaded none of it: every message the module raises from Python
came out in English on a Ukrainian installation. The cause is not the translation.
Odoo's `PoFileReader` requires each code entry to carry the extracted comment
`#. odoo-python`, and it merges a module's own `.pot` over its `.po` before reading,
which strips that comment. The generated catalogue carried the comment on no entry,
and the generated `.pot` overrode it either way. Two edits fix it: the comment is
added to each of the 28 code entries in `i18n/uk.po`, and
`i18n/odomate_hr_custody.pot` is not shipped. With that, 28 of 28 load.
Nothing else in the module was touched, no translation text was changed, and the
same fault is present in every module of this suite — it is reported to the
platform rather than treated as this module's problem.

Generated with OdoMate (https://www.odomate.pro) — September 2026, Odoo 19
Community. Published unedited apart from publication metadata (store listing page,
banner and icon) and the one translation correction described above.

---


# Company Property in Custody — Spec (Level 1: Business User)

> **Who wrote this:** the HR manager who also ends up owning "who has the company laptop". They use Odoo every day and have **no** idea how Odoo is built inside. This is how they would ask for it, in plain words.

**What app this touches:** the **Employees** app — a new **Custody** area, plus buttons on each employee's record.

---

## 1. What I want (the problem)

The company owns things that people take away with them: laptops, phones, vehicle keys, access cards, projectors, measuring instruments, the good camera. Somebody takes one, and from that moment we are guessing.

- *"Where is the second projector?"* — three people think somebody else has it.
- *"When is Andriy bringing the instrument back?"* — he said "a couple of weeks", in a conversation, in March.
- Two people are promised the same laptop for the same week, because nothing anywhere says it is already out.
- Somebody leaves the company still holding a phone, and we find out at the exit interview, or not at all.
- And when something does go missing, there is **no piece of paper** with the person's name on it saying they took it, on what date, for what, and undertook to return it. That is the one thing I actually need, and it is the one thing we never have.

I want a register of the things, a request-and-approval trail for taking one, a return step, automatic chasing when a return date passes, and a **printable handover document** the person signs.

---

## 2. What I want to be able to do

### a) Keep a register of the things

Each item: a **name**, a **photo**, a **description** of what it actually is (model, serial number, what came with it), and the **company** it belongs to.

Optionally, an item can be **linked to a product in the catalogue** — for the items we bought as stock and already have a catalogue entry for. When I link one, the name should fill itself in from the catalogue. This is a convenience, not a requirement: most of my register will be items typed in by hand.

### b) Ask to take an item

A request records: **who** is taking it, **which item**, the **date requested**, the **reason** in a sentence — *"client visit, Lviv"*, *"remote work"* — the **date they will bring it back**, and free **notes**.

When an employee raises one for themself, it should default to them, so they are not choosing their own name from a list of two hundred.

### c) Approve it, or refuse it with a reason

- The request is raised as a **draft**, then **sent for approval**.
- An HR officer **approves** it, and the item is now formally in that person's keeping.
- Or **refuses** it — and refusing must ask for a **reason**, in writing, which stays on the record. A refusal with no reason is how a person ends up asking me the same question three times.
- A request can be put **back to draft** if it was sent by mistake.

### d) Not hand out the same thing twice

**Approval must be refused if that item is already in somebody's keeping** — with a message saying so. This is the single most useful rule in the whole module and it must hold everywhere, not only on the screen.

### e) Extend a return date properly

People need things longer than they thought. That should be a request, not an edit.

- The holder asks to **extend**, giving a **new return date**.
- That puts the request back into **waiting for approval**, showing both the current return date and the one being asked for.
- The approver either **approves the extension** — the new date becomes the return date, and the record goes back to approved — or **refuses it**, giving a **reason**; the record goes back to approved with the **original** date unchanged, and the refusal reason is kept.
- A proposed new return date that is not after the request date is refused.

### f) Record the return

One button, **Returned**, which closes the record and stamps the date the item actually came back — so I can tell "brought back on time" from "brought back six weeks late", which the promised date alone can never tell me.

### g) Be chased automatically

A **daily check** that finds every item whose return date is today, tomorrow, or already past and is still out, and emails the holder: what they have, when they took it, why, and when it is due. The email should carry a **link straight to the record**, so extending it is one click and not a hunt through a menu.

### h) Print the handover document

The thing I actually need, and the reason a spreadsheet was never enough. From an approved request, **print a one-page handover document** carrying:

- the **company** heading,
- the **reference number** of the request and the date,
- **who is taking the item** — their name, their job, their department, the **identification reference we hold for them**, and the **emergency contact** we have on file for them,
- **what they are taking** — the item's name and its description,
- **why**, and the **date it must be back**,
- a short **undertaking** — that the holder has received the item in working order, is responsible for it, and will return it by that date,
- **two signature lines**, one for the holder and one for the person handing it over.

The identification reference and the emergency contact come from the employee's own record — the details the **Employee Information** module puts there. That is deliberate: a handover document that does not identify the person receiving the item, and gives no way to reach anybody if something happens, is not worth printing.

### i) See it from the person's side

On an employee's record, two counters: **how many custody records** they have in total, and **how many items they are holding right now**. Each opens the matching list.

### j) Look at the whole picture

A simple **analysis** screen where I can count and group custody records — by item, by person, by state, by month — so I can answer "which items are out most often" and "who has the most overdue returns" without exporting anything.

---

## 3. What I want to see on screen

- **A Custody area in the Employees app** with three screens: **Custody Requests**, **Items** (the register), and **Analysis**.
- **On a request:** the reference number across the top, the state as a bar — *Draft → Waiting for approval → Approved → Returned*, with *Refused* as the end of the other path — the employee, the item, the reason, the requested date, the return date, and the notes. Underneath, the message thread.
- **The buttons on a request, and when each appears:** *Send for approval* (draft only) · *Approve* and *Refuse* (waiting only) · *Set to draft* (draft path only) · *Extend* (approved only) · *Returned* (approved only) · *Print handover document* (approved and returned) · *Send reminder* (approved only).
- **When an extension is pending**, the record shows both dates side by side — the return date it currently has, and the one being asked for — so the approver is comparing, not guessing.
- **When an extension was refused**, the refusal reason stays visible on the record, plainly labelled as the *extension* refusal so nobody confuses it with a refused request.
- **On an item:** its photo, name, description, company, and the optional catalogue link. Items should be browsable as cards with their photos, because that is how people recognise a projector.
- **In the requests list:** reference, employee, item, requested date, return date, state. Overdue rows should be visually obvious without reading the dates.
- **On an employee's record:** two counters — total custody records, and items held right now.
- **The handover document:** one page, printed as a PDF, laid out to be signed on paper.

---

## 4. What I want to be warned about

- **An item can only be out once.** That is the rule the whole module hangs on. It means approving is sometimes refused, and the person approving needs to be told *why* — "already held by someone" — not just blocked.
- **The register is not stock.** This module knows nothing about quantities. If we own five identical laptops, that is five items in the register, not one item with a quantity of five. If somebody sets it up as one item, only one person will ever be able to hold a laptop.
- **Nothing here proves anything financially.** No value, no depreciation, no insurance, no link to what we paid. It is a register of who has what.
- **The chasing email goes to the holder only.** Nothing escalates to their manager or to me. Somebody has to look at the overdue list.
- **The handover document is only as good as the employee record behind it.** If the identification reference or the emergency contact is missing from the person's record, those lines print empty. The document still prints — I would rather have it with a gap than not at all — but a gap is a signal to go and fill the record in.
- **Returning does not check the item's condition.** "Returned" means it came back. It does not mean it came back working.

---

## 5. What is intentionally NOT included (keep the first version honest)

- **No quantities and no stock.** One physical thing, one entry in the register. No reservations, no availability calendar, no booking ahead — an item is either out or it is not.
- **No condition, damage or maintenance.** No condition on handover, no condition on return, no damage report, no repair history, no service schedule.
- **No money.** No purchase value, no depreciation, no insurance, no accounting entry, no link to a supplier invoice.
- **No multi-level approval.** One approval by one HR officer. No chain, no delegation, no substitute approver while somebody is on leave.
- **No blocking on departure.** Somebody with an item still out can still be marked as leaving. Wiring custody into the leaving process belongs to the **resignation** module in a later wave, not here.
- **No escalation.** One reminder email to the holder each day it is overdue. Nobody else is told, ever.
- **No barcodes or scanning.** Handover and return are recorded by a person pressing a button.
- **No signature in the system.** The handover document is signed on paper. Nothing captures a signature on screen or stores a signed copy back.
- **No history of who held an item before.** The custody records themselves are the history; there is no separate timeline on the item.

---

## 6. How we'll know it works (acceptance criteria)

1. I can add an item to the register — name, photo, description — and see it as a card with its photo. ✅
2. I can add a second item by linking it to a product in the catalogue, and its name fills in from the catalogue. ✅
3. I can raise a custody request for an employee with an item, a reason, a requested date and a return date; it is created in **Draft** with its own reference number. ✅
4. I press **Send for approval** and the state becomes *Waiting for approval*. ✅
5. I press **Approve** and the state becomes *Approved*. ✅
6. I raise a **second** request for the **same item** and a different employee, send it for approval, press Approve — and I am **refused**, with a message saying the item is already held. ✅
7. I press **Refuse** on a waiting request, am asked for a reason, type one, and the request becomes *Refused* with my reason visible on it. ✅
8. On the approved request I press **Extend**, propose a new return date, and the record goes back to *Waiting for approval* showing the current return date and the proposed one together. ✅
9. I **approve** that extension: the return date becomes the new date and the state is *Approved* again. ✅
10. On another approved request I propose an extension and **refuse** it with a reason: the state is *Approved* again, the return date is **unchanged**, and the refusal reason is on the record, labelled as the extension refusal. ✅
11. I propose an extension to a date before the request date and I am refused. ✅
12. I press **Returned**; the state becomes *Returned* and today's date is stamped as the date it came back. ✅
13. The item from step 12 can now be approved for a **different** employee — releasing it works. ✅
14. I set an approved request's return date to yesterday, run the daily check, and the holder receives an email naming the item, the reason and the due date, with a link that opens that record. ✅
15. The same run sends **nothing** for a request due next month, and nothing for one already returned. ✅
16. On an employee's record, the two counters show the right numbers, and each opens the matching list. ✅
17. On the **Analysis** screen I can group custody records by item, by person and by state, and the counts match the lists. ✅
18. **The handover document.** From an approved request I press **Print handover document** and get a one-page PDF carrying: the company heading; the reference number and date; the holder's name, job, department, **identification reference** and **emergency contact**; the item's name and description; the reason; the return date; the undertaking text; and two signature lines. ✅
19. I clear the identification reference and the emergency contact on that employee, print again, and the document still prints with those two lines empty — it does not fail. ✅
20. **As an ordinary employee** — signed in with no HR role — I can see **my own** custody requests and raise a new one for myself, I **cannot** see a colleague's, and the **Approve** button is not available to me. ✅
