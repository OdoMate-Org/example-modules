# Employee Dependants & Identity Documents — User Guide

Technical name: `odomate_hr_employee_info_06092026_2` · Odoo 19.0 · License LGPL-3

## Table of contents

1. [What this module does](#1-what-this-module-does)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration)
4. [Dependants](#4-dependants)
5. [Identity documents and expiry warnings](#5-identity-documents-and-expiry-warnings)
6. [Joining date and notice period](#6-joining-date-and-notice-period)
7. [Automatic employee creation from a login](#7-automatic-employee-creation-from-a-login)
8. [Access rights](#8-access-rights)
9. [Demo data](#9-demo-data)
10. [Limitations](#10-limitations)

---

## 1. What this module does

The module adds four things to the standard Employees app:

- **Dependants.** A list of family members per employee (`odomate.hr.dependant`), each linked to a relationship from a small master list (`odomate.hr.relationship`). One dependant per employee can be marked as the emergency contact; ticking that box copies the name and phone onto the employee's **Emergency Contact** / **Emergency Phone** fields.
- **Identity document tracking.** An **Identification Expiry Date** next to the native **Identification No**, scan attachments for both the identification reference and the passport, and a daily job that e-mails the employee a fixed number of days before either document expires.
- **Joining Date.** A stored, read-only date computed as the earliest start date across all of the employee's `hr.version` records.
- **Notice period.** An editable **Notice Period (Days)** on `hr.version`, pre-filled from a company default the first time a version is created.

Two new models are created; `hr.employee`, `hr.version`, `res.users`, `res.company` and `res.config.settings` are extended. No new security group is created — the module reuses **HR Officer** (`hr.group_hr_user`) and **HR Administrator** (`hr.group_hr_manager`).

## 2. Installation

1. Copy the module folder into your Odoo addons path.
2. **Apps → Update Apps List**.
3. Search for *Employee Dependants & Identity Documents* and click **Activate**.
4. Assign **HR Administrator** (`hr.group_hr_manager`) to at least one user. The module does not grant this group to anyone automatically — not even to the database administrator — so someone needs it explicitly to reach **Employees → Configuration → Dependant Relationships** and to edit `notice_period` on existing versions. Do this from **Settings → Users & Companies → Users**.

`hr` and `mail` are installed automatically if they are not present yet.

## 3. Configuration

### 3.1 Company settings

**Settings → Employees → Employee Records** holds four per-company values:

| Setting | Default | Meaning |
| --- | --- | --- |
| Identification Expiry Warning | 14 days | Lead time for the identification warning e-mail |
| Passport Expiry Warning | 180 days | Lead time for the passport warning e-mail |
| Create Employee From New Login | On | Create an employee for every new internal user of this company |
| Default Notice Period | 30 days | Value proposed on newly created employee versions |

All four live on `res.company`, not on system parameters, so the scheduled job and the settings screen always read the same value in a multi-company database.

### 3.2 Relationships

**Employees → Configuration → Dependant Relationships** (HR Administrator only) manages the master list. The module ships **Spouse**, **Father**, **Mother**, **Son** and **Daughter**; add your own (for example **Guardian**) from this screen. Names are unique. Archiving a relationship keeps it on existing dependants but hides it from the dropdown.

### 3.3 Scheduled action

**Settings → Technical → Scheduled Actions → HR: Identity Document Expiry Warnings** runs once a day at 05:00. You can change the hour or deactivate it there.

## 4. Dependants

Open an employee, go to the **Private Information** tab (visible to HR only) and scroll to the **Dependants** section. Add a line with:

| Column | Notes |
| --- | --- |
| Name | Required |
| Relationship | Required, picked from the master list |
| Phone | Optional |
| Date of Birth | Optional |
| Emergency Contact | Toggle — at most one per employee |

### 4.1 Emergency contact

Ticking **Emergency Contact** on a dependant does three things, in this order:

1. Unticks the flag on every other dependant of the same employee.
2. Writes the dependant's **Name** into the employee's **Emergency Contact**.
3. Writes the dependant's **Phone** into the employee's **Emergency Phone**.

This runs inside `create()` and `write()` on `odomate.hr.dependant`, so it applies identically from the form, from an import, and from an RPC call. A partial unique index on `(employee_id) WHERE is_emergency_contact` backs the rule at the database level, so two concurrent writes cannot leave two flagged dependants behind.

**Emergency Contact** and **Emergency Phone** stay ordinary editable fields on the employee. HR can still type a value directly — useful when the emergency contact is a neighbour or a friend rather than a dependant. The dependant flag pushes a value in; it does not lock the field.

### 4.2 Spouse auto-add

When an employee has both **Spouse Complete Name** and **Spouse Birthdate** filled in, the module creates a matching dependant with the **Spouse** relationship. The check is idempotent: it looks for an existing Spouse dependant of that employee with the same name (case-insensitive) before inserting, so re-saving the record does not create duplicates. If the creation fails for any reason it is logged and the employee's own save still succeeds.

Worked example: HR opens *Sofia Bondarenko*, types `Bohdan Bondarenko` and `17/02/1986` into the spouse fields and saves. A **Bohdan Bondarenko / Spouse / 17/02/1986** dependant appears in the Dependants list. Saving again changes nothing.

## 5. Identity documents and expiry warnings

The **Private Information** tab now shows, next to the native fields:

- **Identification No** → **Identification Expiry Date** → **Identification Scans** (multi-file upload) → **Send Identification Expiry Warning** button.
- **Passport No** → **Passport Expiration Date** → **Passport Scans** (multi-file upload) → **Send Passport Expiry Warning** button.

Each button is hidden while its expiry date is empty.

### 5.1 How the daily job decides

For every company, the job computes `today + lead time` and warns only the employees whose expiry date equals that day **exactly**. It is a single-day equality test, not a `<=` range, so nobody is warned twice as the date approaches.

Worked example with the default 14-day identification lead time, run on 06/09/2026:

| Employee | Identification Expiry Date | Warned? |
| --- | --- | --- |
| Olena Kravets | 20/09/2026 (= today + 14) | Yes |
| Taras Moroz | 21/10/2026 (= today + 45) | No |
| Marko Petrenko | 06/09/2027 (= today + 365) | No |

The next day the job compares against 21/09/2026, so Olena is not warned again.

Changing a lead time in Settings affects only the next run's comparison. Nothing is backfilled and no past-due employee is scanned retroactively.

### 5.2 Send now

The two buttons send the same `mail.template` immediately, regardless of the date. Use them when an employee asks for a copy or when HR wants to chase a renewal early. If the employee has neither a work e-mail nor a private e-mail, nothing is sent and the button shows an orange *No e-mail address on file* notification.

### 5.3 Editing the e-mail wording

The messages are ordinary editable templates under **Settings → Technical → Email → Templates**:

- *Employee: Identification Expiry Warning*
- *Employee: Passport Expiry Warning*

Edit the subject or body there; the Ukrainian wording ships in `i18n/uk.po`.

## 6. Joining date and notice period

**Joining Date** appears read-only on the **Work Information** tab, next to the work location. It is stored and recomputed automatically whenever a version is added or its start date changes — it is never typed by hand. This is enforced in the model itself, not just in the form: `create()` and `write()` silently drop any `joining_date` value supplied from outside (a manual write, an import, an RPC call), so the field can never be forced out of sync with the computed value — only `_compute_joining_date` ever sets it.

**Notice Period (Days)** lives on `hr.version`. When a version is created, the field is pre-filled from the company's **Default Notice Period**. It is a one-time default, not a live link: raising the company default from 30 to 60 leaves every existing version at 30. HR Administrators can edit the value per version; for HR Officers the field is read-only in the form.

## 7. Automatic employee creation from a login

When **Create Employee From New Login** is on for a company, creating a new internal user in that company also creates an `hr.employee` with the user's name and `user_id` set. The native **Employee** link on the user form then resolves by itself — the module does not redeclare `res.users.employee_id`.

The rule is evaluated at the moment the login is created, so switching the setting off takes effect on the very next user, with no restart. The automation:

- skips portal and public users (`share = True`), the OdooBot/superuser account, and inactive users;
- skips a user who already has an employee, so it never duplicates the employee that Odoo's own **Create Employee** checkbox produces;
- never backfills existing logins;
- never deletes an employee when a login is removed;
- runs one-way only — creating an employee never creates a login.

If employee creation fails, the failure is logged and the user is still created.

## 8. Access rights

| Model | HR Officer | HR Administrator | Other internal users |
| --- | --- | --- | --- |
| `odomate.hr.dependant` | Read / write / create / delete, all records | Same | Read only, and only their own employee's dependants |
| `odomate.hr.relationship` | Read | Read / write / create / delete | Read |

Two record rules apply to dependants:

- A global multi-company rule restricting records to the user's allowed companies.
- A group pair: `hr.group_hr_user` sees every dependant; `base.group_user` sees only `[('employee_id.user_id', '=', user.id)]`, read-only.

Both rules are needed. Odoo ORs record rules across the groups a user belongs to — HR staff are also members of `base.group_user`, so without the HR-wide rule the restrictive own-records rule would apply to them as well.

The Dependants section sits on the employee's Private Information page, which the `hr` module already restricts to HR — colleagues never see it.

The module does not grant `hr.group_hr_manager` (or any group) to any user as part of installation — not even to the database administrator. Groups belong to the users and groups configuration, not to a feature module, so assigning the HR Administrator role to whoever needs it is a manual step (see §2 Installation).

## 9. Demo data

Installing with demo data creates ten employees (Olena Kravets, Marko Petrenko, Sofia Bondarenko, Andriy Shevchuk, Iryna Melnyk, Dmytro Kovalenko, Nadiya Tkachenko, Yuriy Boyko, Kateryna Lysenko, Taras Moroz) and seventeen dependants spanning all five shipped relationships. Highlights to click through:

- **Olena Kravets** — identification expiring in exactly 14 days (the cron's positive case) and a passport 400 days out (negative case). Three dependants.
- **Marko Petrenko** — passport expiring in exactly 180 days (positive case) against a 365-day identification (negative case).
- **Andriy Shevchuk** — *Halyna Shevchuk* flagged as emergency contact, with the employee's Emergency Contact / Emergency Phone matching.
- **Sofia Bondarenko** — spouse details filled in; her **Bohdan Bondarenko / Spouse** dependant is the one the auto-add rule created during the demo load.
- **Iryna Melnyk** and **Dmytro Kovalenko** — multiple dependants each.

## 10. Limitations

- Only the identification reference and the passport are tracked. Visas, work permits and licences are out of scope — Odoo 19 already carries `visa_no` / `visa_expire` / `permit_no` natively, and richer document management belongs in a dedicated module.
- There is no employee self-service screen. Dependants are maintained by HR; an ordinary employee can read their own dependants through the API but has no menu for them.
- Identification and passport numbers are stored as free text; no format or checksum validation is performed.
- No duplicate-employee detection, no payroll or allowance effects, and no field-level change history on dependants.
- The automation is login → employee only. Creating an employee does not create a login.
- The **Notice Period** restriction for HR Officers is enforced in the form view (the field renders read-only). It is not a server-side write guard, so an HR Officer with API access can still change it.
- Notice Period is not backfilled on versions that already existed when the module was installed; those start empty.
- The five shipped relationship names (Spouse, Father, …) are data records on a plain `Char` field, so they are not translated by `i18n/uk.po`. Rename them in the Configuration screen for a non-English database.
