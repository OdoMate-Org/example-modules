# OdoMate HR Suite — User Guide

Technical name: `odomate_hr_bundle` · Version `19.0.1.0.0` · License LGPL-3

## Table of contents

1. [What this module does](#1-what-this-module-does)
2. [What gets installed](#2-what-gets-installed)
3. [Installation](#3-installation)
4. [The menu layout you get](#4-the-menu-layout-you-get)
5. [Permissions](#5-permissions)
6. [Keeping the layout after upgrading one member module](#6-keeping-the-layout-after-upgrading-one-member-module)
7. [Uninstalling](#7-uninstalling)
8. [Limitations](#8-limitations)

## 1. What this module does

`odomate_hr_bundle` is a meta-module. It contains no models, no fields, no
wizards, no computed values, no automation and no permission records of its
own. It does exactly two things:

1. It **installs the eight OdoMate HR modules** as a single unit, so you tick
   one box in Apps instead of eight.
2. It **groups their menus** into an **HR Suite** folder in the Employees app
   and a second **HR Suite** folder under **Employees → Configuration**, so the
   top level of the Employees app does not grow eight new entries.

Every screen, record, button and permission you see afterwards comes from the
member modules. This module adds none of its own.

## 2. What gets installed

| Module | Title on the Store | What it does |
|---|---|---|
| `odomate_hr_employee_info_06092026_2` | Employee Dependants & Identity Documents | Family members, dependants and identity document details on the employee record |
| `odomate_hr_documents` | Employee Document Expiry Tracking | Documents that expire, with advance warning and a renewal history |
| `odomate_hr_custody` | Employee Custody Management | Company property held by employees, with request, approval and return |
| `odomate_hr_transfer` | Employee Transfer | Moves between departments, locations or companies, keeping the history |
| `odomate_hr_leave_email` | Time Off Requests by Email | Turns an incoming email into a time-off request |
| `odomate_hr_notices` | HR Notices, Announcements & Acknowledgements | Company announcements and personal reminders, with a count in the top bar |
| `odomate_hr_dashboard` | Employee Turnover & Absence Dashboard | Headcount, turnover, absence concentration and pending approvals in one screen |
| `odomate_hr_resignation` | Employee Resignation & Clearance | Resignation requests, a clearance checklist and an exit interview |

`hr` (Employees) is also declared as a dependency, because the two HR Suite
folders are attached to the Employees app menu.

`odomate_hr_leave_email` contributes no menu of its own — it is configured
through an incoming mail alias and the Time Off settings, not through a
dedicated screen. That is why eight modules produce ten re-parented menu
entries rather than eleven.

## 3. Installation

1. Copy `odomate_hr_bundle` into your addons path, together with the eight
   member modules if they are not already there.
2. **Apps → Update Apps List.**
3. Search for **OdoMate HR Suite**, then click **Install**.

Odoo resolves the dependency list and installs any member module that is
missing. On a database where some members are already installed, only the
missing ones are added — **already-installed members and all of their data are
left untouched.** This is standard Odoo dependency behaviour, not something
this module implements.

No configuration step follows the install. There is nothing to set up.

## 4. The menu layout you get

**Employees → HR Suite** (sequence 35, so it sits after the app's own
top-level entries):

| Order | Entry | Comes from |
|---|---|---|
| 1 | Documents | `odomate_hr_documents` |
| 2 | Custody | `odomate_hr_custody` |
| 3 | Notices | `odomate_hr_notices` |
| 4 | Transfers | `odomate_hr_transfer` |
| 5 | Resignations | `odomate_hr_resignation` |
| 6 | HR Overview | `odomate_hr_dashboard` |

**Employees → Configuration → HR Suite** (sequence 90, so it sits at the
bottom of the Configuration menu):

| Order | Entry | Comes from |
|---|---|---|
| 1 | Dependant relationships | `odomate_hr_employee_info_06092026_2` |
| 2 | Announcement categories | `odomate_hr_notices` |
| 3 | Clearance items | `odomate_hr_resignation` |
| 4 | Date reminders | `odomate_hr_notices` |

Each of these ten entries is rewritten with **`parent_id` and `sequence`
only**. Its name, its action, its group restrictions, its active flag and its
icon are never touched. That is why every entry keeps its own screen, its own
records, its own permissions and its own translated label after the move.

## 5. Permissions

This module ships no `ir.model.access` rows, no record rules and no security
groups, and it grants nothing to any user or existing group. **Installing it
changes no user's permissions.**

The two HR Suite folders carry no action and no group of their own. Odoo hides
a folder automatically when every entry beneath it is hidden from the current
user, so visibility is entirely inherited from the member modules:

- A user with no OdoMate HR permissions at all does not see the HR Suite
  folder.
- A user who may only see Custody sees an HR Suite folder containing exactly
  one entry.
- A user who holds every member module's group sees all six entries.

## 6. Keeping the layout after upgrading one member module

This is the one operational detail worth knowing.

The menu file is deliberately **not** marked `noupdate`, so the HR Suite
arrangement re-applies every time `odomate_hr_bundle` is upgraded.

However, if you later upgrade **a single member module on its own**, that
member's own XML reloads and puts **its own** menu back at its native
top-level position. Only that member is affected; the other nine entries stay
where they are.

**To restore the grouping:** upgrade `odomate_hr_bundle` afterwards
(**Apps → OdoMate HR Suite → Upgrade**). Nothing else is needed, and the
upgrade is safe to repeat.

## 7. Uninstalling

Nothing is destroyed when you uninstall this module.

The `parent_id` field on a menu is declared `ondelete="restrict"` in Odoo's
own source, which means uninstalling the bundle **can never delete a member
module's menu as a side effect.** The eight member modules and all of their
data remain installed and keep working individually.

What uninstalling does **not** do is move the ten entries back to their
original positions. The `parent_id` values the bundle wrote landed on records
owned by the *member* modules, so the bundle has nothing of its own to revert.
Each member menu returns to its native position the next time **that member's
own module** is upgraded or reinstalled.

One detail is **unverified and we are flagging it rather than guessing**:
whether the two HR Suite folder records that this module owns are themselves
removed on uninstall, or whether the `restrict` constraint leaves them behind
as empty folders because a still-installed member's menu still points at one.
We could not confirm the per-record behaviour of Odoo's uninstall routine from
the source available to us, so we state it neither way. If empty HR Suite
folders do remain after an uninstall, they are harmless and can be deleted
manually in developer mode under **Settings → Technical → User Interface →
Menu Items**.

## 8. Limitations

- **Menu placement only.** This module adds no feature of its own. If a member
  module lacks a capability, installing the bundle does not add it.
- **Re-upgrade needed after a single-member upgrade.** See section 6. This is
  inherent to how Odoo reloads a module's own XML and cannot be avoided from a
  separate module.
- **Uninstall does not restore the original menu positions.** See section 7.
- **The fate of the two folders on uninstall is unverified.** See section 7.
- **Fixed layout.** The order and grouping are defined in
  `views/odomate_hr_suite_menus.xml`. Changing them means editing that file and
  upgrading the module; there is no settings screen for it.
- **No demo data.** A data-only meta-module ships none.

---

OdoMate · <https://www.odomate.pro> · <support@odomate.pro>
