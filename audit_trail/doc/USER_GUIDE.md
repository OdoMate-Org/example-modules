# Audit Trail — User Guide

Audit Trail records **who did what, to which watched record, when**, with the field values before and after the change. You choose which kinds of records to watch, per company, and switch watching on deliberately. A scheduled clean-up can remove old history once you enable it.

## Table of Contents

1. [Overview](#1-overview)
2. [Installation](#2-installation)
3. [Roles and Access](#3-roles-and-access)
4. [Configuration](#4-configuration)
5. [Daily Use](#5-daily-use)
6. [Field Reference](#6-field-reference)
7. [Scheduled Clean-up](#7-scheduled-clean-up)
8. [Demo Data](#8-demo-data)
9. [Limitations](#9-limitations)

## 1. Overview

| Screen | Menu | Purpose |
|---|---|---|
| Watch Rules (`audit.rule`) | Audit → Configuration → Rules | Which kind of record is watched, in which company, which actions and how much detail |
| Recorded Events (`audit.log`) | Audit → Logs | One row per create / change / delete / export / list open |
| Field Changes (`audit.log.line`) | Audit → Log Lines | One row per changed field, searchable across every watched kind of record |
| Working Sessions (`audit.session`) | Audit → Sessions | Sign-in time, browser and network address of the visit that produced events |

## 2. Installation

1. Open **Apps**, search for **Audit Trail**, click **Activate**.
2. The module depends on `base`, `web`, `base_setup` and `product` (Price Lists). No other app is installed.
3. After installation the **Audit** menu appears for the administrator. System administrators automatically receive the **Audit Administrator** role.

## 3. Roles and Access

| Role | Watch Rules | Recorded Events / Field Changes / Sessions |
|---|---|---|
| **Auditor** (`audit_trail.group_audit_user`) | Read | Read |
| **Audit Administrator** (`audit_trail.group_audit_manager`, includes Auditor) | Read, create, edit, delete | Read and delete (never edit) |

- Every record is limited to the companies the user is allowed to work in.
- The **View Logs** button on Contacts, Bank Accounts and Price Lists is visible only to Auditors and Audit Administrators.
- The **Rules** menu requires Audit Administrator; the **Settings** menu requires the Odoo system administrator role.

## 4. Configuration

### 4.1 Create a watch rule

1. Go to **Audit → Configuration → Rules** and click **New**.
2. Fill **Name** (e.g. "Contacts") and **Kind of Record** (e.g. *Contact*). **Company** defaults to your current company.
3. Choose the **Detail Level**:
   - **Full** — keeps old and new values. Slower: the whole record is re-read before and after every change.
   - **Light** — keeps only the new value of each changed field. Faster, but you lose the old value.
4. On the **Actions to Record** tab, tick what to record: **Record Creation**, **Record Changes**, **Record Deletion**, **Record Exports**, **Record List Opens**.
   - **Record List Opens** is off by default. Every list showing more than one watched record creates an event, which can mean thousands of rows a day. A single record opened on its own is never recorded.
5. **Keep a Copy on Deletion** stores the full contents of each deleted record (extra database space).
6. On the **Exclusions** tab, list **People to Exclude** and **Fields to Exclude**.
7. Click **Confirm**. The rule becomes **Active** and recording starts.

Only one rule per kind of record and company is allowed. A second one is refused with a message naming the existing rule.

### 4.2 Change a rule

While a rule is **Active**, its watch settings are locked (a blue banner says so). Click **Set to Draft**, change the settings, then **Confirm** again. Nothing is recorded while the rule is in Draft. An active rule cannot be deleted; set it to Draft first.

## 5. Daily Use

### 5.1 Recorded Events

**Audit → Logs** lists events with date, record, kind of record, action and user. Use **Group By → User / Kind of Record / Action / Date / Working Session**, or the filters **Creations, Changes, Deletions, Exports, List Opens**.

The event form shows who / when / which record / which action / detail level, and the **Field Changes** table (field, old value, new value). Buttons:

- **Open Record** — opens the watched record (hidden for deletions, exports and list opens). If the record has since been deleted, a warning notification says so instead.
- **View Exported Records** — shown only on export events; opens exactly the records that were exported.
- A **Deleted Record Contents** tab appears on deletion events when a copy was kept.

### 5.2 Worked example

Rule "Contacts", Full detail, active. A user changes the phone of *Deco Addict* from `(603)-996-3829` to `(603)-996-4100`:

| Field | Old Value | New Value |
|---|---|---|
| Phone | (603)-996-3829 | (603)-996-4100 |

With **Light** detail the same change stores **Old Value** empty and **New Value** `(603)-996-4100`. If the user saves without changing anything, no event is written.

### 5.3 Field Changes

**Audit → Log Lines** is a flat list of every changed field across all watched kinds of records. Search by record, field label, old or new value, kind of record or user.

### 5.4 From a watched record

On a Contact, Bank Account or Price List form, click **View Logs** to see that record's history only.

### 5.5 Working Sessions

**Audit → Sessions** shows the user, sign-in time, last activity, browser and network address, and the number of recorded events. Open a session to see its events. A session is created the first time a signed-in person triggers a recorded event, so **Sign-in Time** is the time of that first event, not of the actual login.

## 6. Field Reference

### Watch Rule (`audit.rule`)

| Field | Meaning |
|---|---|
| `name` | Rule name |
| `model_id` | Kind of record watched |
| `company_id` | Company whose users' changes are recorded |
| `state` | Draft / Active |
| `detail_level` | Full / Light |
| `track_create`, `track_write`, `track_unlink`, `track_export`, `track_read` | Actions recorded |
| `keep_deleted_copy` | Store deleted record contents |
| `excluded_user_ids`, `excluded_field_ids` | Never-recorded people and fields |

### Recorded Event (`audit.log`)

`rule_id`, `res_model`, `res_id`, `record_name`, `action`, `user_id`, `date`, `detail_level`, `company_id`, `deleted_data`, `exported_res_ids`, `session_id`, `source_action`, `line_ids`.

### Field Change (`audit.log.line`)

`log_id`, `field_id`, `field_description`, `old_value`, `new_value`, plus read-only copies of `date`, `user_id`, `record_name`, `res_model`, `res_id`, `action`, `company_id`, `session_id` for searching.

## 7. Scheduled Clean-up

1. Go to **Audit → Configuration → Settings** (or **Settings → Audit Trail**).
2. Tick **Remove Old History** and set **Keep history for … months** (default 6).
3. The daily job **Audit Trail: Remove Expired History** deletes up to 1,000 events per run for companies that switched it on, oldest first, and asks the scheduler to run again until it has caught up.

Example: clean-up enabled with 6 months on 26 September 2026 → events dated before 26 March 2026 are removed for that company only. Other companies keep everything.

Audit Administrators can also delete events by hand from **Audit → Logs** (select → Actions → Delete).

## 8. Demo Data

Demo databases contain three **Draft** rules (Contacts, Bank Accounts, Price Lists), three working sessions and ten illustrative events (phone and e-mail changes on contacts, a bank account number change and deletion, price list changes, exports). Nothing is recorded until you confirm a rule.

## 9. Limitations

- Recording applies to changes made through Odoo's ORM (screens, imports, API). Direct SQL changes are not seen.
- The company of an event is the user's **current company** at the time of the change, not the record's own company.
- Only stored fields are compared; binary/image and one-to-many fields are not recorded (their child records can be watched with their own rule).
- **Source Screen** is best-effort, read from the browser address; it may be empty for API calls.
- There is no approval, blocking, alerting or tamper-proof sealing: Audit Administrators can delete history.
- If recording fails for any reason, the user's action still succeeds and the failure is written to the server log.
