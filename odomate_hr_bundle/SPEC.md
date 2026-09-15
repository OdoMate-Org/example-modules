# SPEC.md — the business specification this module was generated from

This is the business-level specification the module in this folder was generated
from — the menu file, tests, and the user guides in `doc/`. It is written in the voice
of the person who would ask for it: a business owner or HR lead who found the OdoMate
HR modules one at a time and wanted one install that brings the whole set and makes it
read as one system. No model names, field names or technical design appear in it;
everything in `views/` and `tests/` was derived by OdoMate from the plain requirements
below.

**Provenance, stated plainly.** This specification was written by the OdoMate team. It
contains no third-party code, text or configuration. The module was generated from this
document alone.

**What was verified before publication.** Installed **alone** on a freshly created Odoo
19 Community database with demo data and a Ukrainian interface, it pulls in all eight
member modules with no errors. On a second database that already had three of the eight,
it added only the missing five and left the three untouched. Both **HR Suite** folders
were checked on the rendered screen, in Ukrainian: one in the Employees app with six
entries, one under Configuration with four, and nothing duplicated at the top level. None of
its code, menus or dependencies refers to a payroll module (the specification below
names them only to exclude them), it ships no `.pot`, and it grants no group to any user. OdoMate's own run reports its 10 tests passing.

**One generated version, and no hand correction to the code.** Nothing in this module
was written or corrected by hand. The publication changes are the store listing page,
the banner, the icon, and the manifest metadata that points at them (`website`,
`images`).

**Two things are disclosed rather than fixed.** Uninstalling the bundle does not move
the member menus back to their original places — the bundle never owns those menu
records, and Odoo only reverts what a module owns; each returns on its own module's next
upgrade. Whether the two HR Suite folders then linger as empty entries is **unverified**:
a menu's parent is `ondelete="restrict"` in Odoo's source, but what the uninstall does
when that deletion is blocked could not be confirmed either way. Separately, the
Turnover & Absence Dashboard's own HR Overview screen stays at the top of the Employees
app; what moves into HR Suite is its analysis menu. Both are stated in the user guide
and on the listing page.

Generated with OdoMate (https://www.odomate.pro) — September 2026, Odoo 19 Community.
Published unedited apart from publication metadata (store listing page, banner and icon).

---


# odomate_hr_bundle — specification

*Written in the voice of the person who would ask for it: a business owner or HR lead who
runs Odoo and does not know how Odoo is built inside. No model names, no field names, no
technical design appears below.*

---

## 1. What I want (the problem)

I went looking for HR add-ons for our Odoo and found yours — but I found them **one at a
time**. A module for employee documents. Another for company property. Another for
resignations. Each one has its own page, its own description, its own install.

Three things went wrong with that.

**I could not tell what existed.** I installed two of them before I discovered there were
eight. There was nothing anywhere that said "these belong together."

**I could not tell what fitted with what.** Each page described its own module honestly
enough, but none of them told me that the resignation module knows about company property,
or that the overview screen draws on the others. I had to install them to find out.

**And once they were installed, the Employees app was a mess.** Eight separate entries
strung down the menu in whatever order they happened to load, and four more scattered
through Configuration. It looked like eight unrelated add-ons from eight different vendors,
which is exactly what it was not.

**I want one thing to install that gives me the whole set, and tells me plainly what I am
getting before I install it.**

---

## 2. What I want to be able to do

### a) Install once, get everything

I install a single item. Everything in the HR set arrives with it — I do not hunt down
eight pages and repeat the process eight times. If I already have some of them installed,
the rest are added and the ones I have are left alone.

### b) Know what I am getting *before* I install

The description must name **every** module in the set and say in one line what each does.
Not a list of technical names — names I would recognise, with the plain reason each exists.
I should be able to read the page and know whether this set solves my problem without
installing anything.

If one of them is not something I want, I need to see that before I commit, not after.

### c) Have the menus make sense afterwards

Once it is installed, the HR screens should look like **one system**, not eight add-ons.

I want the working screens gathered under a single clearly named place in the Employees
app, in a sensible order, and the configuration screens gathered the same way under
Configuration. I do not want to hunt down the menu for the module I just installed.

### d) Keep the permissions I already had

Grouping things under one heading must not let anybody see anything they could not see
before. Whatever each module decided about who may read what, stays exactly as it was. A
person who could not see company-property records yesterday still cannot see them today,
and the new heading does not appear for them at all if there is nothing under it they are
allowed to open.

### e) Uninstall cleanly

If I decide this is not for me, removing it puts the menus back and leaves the individual
modules working on their own.

---

## 3. What I want to see on screen

- **On the Apps page, before installing:** the set's name, and a description that names all
  eight members with a line each.
- **After installing, in the Employees app:** one heading named **HR Suite**, holding the
  working screens — documents, company property, notices, transfers, resignations and the
  HR overview — in that order.
- **Under Employees → Configuration:** a second **HR Suite** heading, holding the four
  setup screens — dependant relationships, announcement categories, clearance items and
  date reminders.
- **Nothing else new.** No new screens of its own, no new buttons, no new records. If I
  went looking for what this thing added, the answer is "the two headings, and the eight
  modules underneath them."

---

## 4. What I want to be warned about

- **It installs eight modules.** That should be stated plainly on the page, not discovered
  at the confirmation dialog. Installing this is a bigger commitment than installing one
  add-on, and I should know that going in.
- **Upgrading one member on its own puts its menu back where it started.** If I upgrade,
  say, the documents module by itself, its entry leaves the HR Suite heading and returns to
  the top level. Re-applying the arrangement means upgrading this set afterwards. I would
  rather be told that than be confused by it.

---

## 5. What is intentionally NOT included

- **No new functionality whatsoever.** This adds no screens, no fields, no records, no
  reports, no automation. Every capability comes from the modules it brings with it. If it
  did anything of its own, it would be a ninth module pretending to be a bundle.
- **No changes to what the members do.** Nothing is renamed, nothing is re-worded, no
  behaviour is altered. Each keeps its own labels in every language.
- **No permission changes of any kind.** It grants nothing to anybody. It does not touch
  user accounts or access groups.
- **No payroll.** There are three further modules in this family — employee loans, loan
  accounting and salary advances — and they are **not** part of this set. They need a
  payroll engine that is not available for this version of Odoo on the Apps Store. They are
  not mentioned in the description, because a buyer cannot obtain them.
- **No choosing which members to install.** It is all eight or none. Anyone wanting a
  subset installs those modules individually, which still works exactly as it does today.

---

## 6. How we'll know it works (acceptance criteria)

1. On a **brand-new database with none of the eight installed**, installing this one item
   alone brings in **all eight**, with no errors.
2. On a database where **three of the eight are already installed**, installing it adds the
   remaining five and leaves the three untouched — no data lost, no settings reset.
3. The Employees app shows **one heading named HR Suite** containing exactly six entries,
   in this order: Documents, Custody, Notices, Transfers, Resignations, HR Overview.
4. **Employees → Configuration** shows a second **HR Suite** heading containing exactly
   four entries: dependant relationships, announcement categories, clearance items, date
   reminders.
5. **Open the Employees app and look at it.** Both headings render with their children
   nested underneath, nothing is duplicated at the top level, no entry appears twice, and
   no heading is empty. *Checked by looking at the screen, not by reading the data behind
   it.*
6. The same check **with Odoo set to Ukrainian**: both headings and every entry under them
   read in Ukrainian, not English.
7. **Signed in as an ordinary employee** with no HR role: they see no more than they saw
   before it was installed. Where they have no access to anything underneath a heading, the
   heading does not appear at all.
8. **Signed in as an HR officer** (not a manager): the entries they could reach before are
   still reachable, in their new place.
9. The description on the module's own page **names all eight members**, each with a line
   saying what it does.
10. Uninstalling it returns the menu entries to where they were, and all eight modules
    continue to work individually.
11. **It contains no reference of any kind to the three payroll modules** — not in what it
    depends on, not anywhere in its files. A search for their names returns nothing.
12. Installing it does **not** change any person's permissions. No user gains a group, and
    no access rule is added, changed or removed.
