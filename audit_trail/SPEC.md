# SPEC.md — the business specification this module was generated from

This is the business-level specification the module in this folder was generated
from — code, views, security, demo data, tests, and the user guide in `doc/`.
It is written in the voice of the person who would ask for it: a finance /
compliance manager who uses Odoo daily and has no knowledge of how Odoo is built
inside. No model names, field names or technical design appear in it; everything
in `models/`, `views/` and `security/` was derived by OdoMate from the plain
requirements below.

**Provenance, stated plainly.** This specification was written by the OdoMate
team as an independent description of what a record-history feature should do.
It contains no third-party code, text or configuration. The module was generated
from this document alone.

Generated with OdoMate (https://www.odomate.pro) — August 2026, Odoo 19 Community.
Published after human security review, unedited apart from publication metadata
(store listing page, banner and icon).

---

## 1. What I want (the problem)

Our auditor asked me a question I could not answer: *"Who changed this supplier's
bank account, and when?"*

I went looking. The record shows the current bank account and nothing else. There
is a message thread on some records that catches a few changes, but not all of
them, and not on every kind of record. On most records there is simply no history
at all. If someone edits a price list, deletes a customer, or downloads our full
contact list to a spreadsheet, nothing anywhere says it happened.

That is a problem for three reasons:

- **I cannot answer audit questions.** "Prove nobody touched this after approval"
  is currently unanswerable.
- **I cannot investigate incidents.** When a number is wrong, I can see it is
  wrong but not how it got that way.
- **I cannot see data leaving.** Exports to spreadsheets are invisible to me.

I want a **history book** for the records I care about: who did what, to which
record, when, and what the value was before and after.

---

## 2. What I want to be able to do

### a) Choose what gets watched — and nothing more

I do **not** want everything in the system recorded. That would be enormous and
useless. I want to pick, one kind of record at a time, what should be watched —
"watch Suppliers", "watch Bank Accounts", "watch Price Lists".

For each kind of record I pick, I want to tick which actions get recorded:

- when a record is **created**,
- when a record is **changed**,
- when a record is **deleted**,
- when a record is **exported** to a spreadsheet,
- when a record is merely **opened and read** (I expect to leave this one off most
  of the time — see the warning below).

I set these up once, and I can only have **one set of watch settings per kind of
record** — otherwise nobody could tell which one applies.

### b) Turn watching on and off deliberately

A new set of watch settings should **not** start recording the moment I save it.
It should sit in a **Draft** state until I press a **Confirm** button. Only then
does recording begin. There should be a matching button to **Set to Draft**, which
stops the recording.

I want that on/off step to be explicit, because switching it on has a real cost on
the system and I want to know exactly when it started.

While a set of watch settings is switched on, it should be **locked** — I should
not be able to quietly change which actions are recorded halfway through. To change
it, I stop it, edit it, and start it again.

### c) Choose how much detail is kept

For each kind of watched record I want to choose between two levels of detail:

- **Full detail** — for every change, keep the **old value and the new value** of
  every field that moved. This is what I actually want for an audit. It is slower
  and it stores more.
- **Light detail** — only record *that* something was changed and *what it was
  changed to*, without going back to look up what it was before. Much faster, much
  smaller, but the "before" column will be empty. Good for a busy record type where
  I only need an activity trail.

I want to be told, on the screen, which of the two I am choosing and what I give up.

### d) Leave people and fields out

Two exclusions I know I will need:

- **People to leave out.** Our nightly integration user touches thousands of
  records. Recording all of that would bury the human activity I actually want to
  see. I want to name specific people whose actions are not recorded.
- **Fields to leave out.** Some fields on a record are noise (a "last synced" stamp)
  or sensitive in a way I do not want copied into a second place. I want to name
  specific fields that are never recorded, even on a watched record.

### e) Keep a copy of what was deleted

When a record is deleted, "record X was deleted" is not enough — the record is gone,
so I cannot look up what it contained. For the record types where it matters, I want
an option to **also keep the full contents of the record as it stood at the moment of
deletion**. I understand this makes the history bigger.

### f) Read the history

I want three ways in:

1. **From the record itself.** When I am looking at a supplier that is being watched,
   I want a **"View logs"** action right there that shows me only that supplier's
   history. This is the one I will use most.
2. **A full list of everything recorded.** One screen listing every recorded event:
   the date, the record's name, what kind of record it was, which action, and who did
   it. I want to **group** that list by person, by kind of record, by date, and by
   working session, and to **search** it.
3. **A field-by-field list.** A flatter screen where each row is *one field that
   moved* — with the description of the field, the old value and the new value side
   by side — so I can search for "who set a credit limit to zero" across everything
   at once.

When I open a single recorded event, I want to see the header (who, when, which
record, which action) and underneath it the **list of every field that moved, with
its before and after value**.

### g) See the session and the page behind an action

For anything done through the browser, I want to be able to see which **working
session** (this person, signed in at this time) and which **page action** it came
from — and to group a day's activity by session, so I can follow one person's visit
from start to finish. This is what turns twenty scattered events into one story.

### h) Not keep it forever

An audit history that nobody ever clears will grow until it becomes a problem. I want
a **scheduled clean-up** that deletes recorded history older than a chosen age — six
months out of the box.

Two things I insist on:

- It must be **off by default.** Nothing should be silently deleting audit evidence
  on a system I just installed. Switching it on is my decision, with our retention
  policy in front of me.
- I must be able to tell it to **work in batches**, so a first clean-up on a huge
  history does not lock up the system for everyone.

### i) Two levels of access

- **Auditor** — can read the history, cannot change what is watched, cannot delete
  anything.
- **Audit administrator** — everything the auditor can do, plus setting up and
  switching the watch settings on and off. Our system administrators should be audit
  administrators automatically.

---

## 3. What I want to see on screen

- **A new "Audit" area** containing four screens: **Rules** (what is watched),
  **Logs** (every recorded event), **Log Lines** (every field that moved), and the
  **sessions / page actions** screens.
- **On a watch-settings screen:** a name, the kind of record, the detail level as two
  clearly labelled choices, the five action tick-boxes, the people and fields to leave
  out, and a **Confirm / Set to Draft** button with the current state shown across the
  top. Draft rows should look visibly different from live ones in the list.
- **On a recorded event:** who, when, which record, which action, detail level — and
  the before/after table underneath.
- **On a watched record:** a **"View logs"** action that opens that record's history
  alone.
- **On an export event:** a button that opens **exactly the records that were
  exported**, so I can see what left the building.

---

## 4. What I want to be warned about

I want plain warnings written into the screen, not buried in a manual:

- **Recording "read" is dangerous.** Every time anyone opens a list of watched
  records, that is a recorded event for every record in the list. On a busy record
  type this can generate more history than actual business data. I expect this to be
  off, and I expect to be told why before I switch it on.
- **Full detail is slower.** Every change to a watched record means the system reads
  the whole record twice, before and after. On a record type that is written to
  constantly, I will feel it.

---

## 5. What is intentionally NOT included (keep the first version honest)

- **No approval or blocking.** This records what happened; it never stops anyone from
  doing anything.
- **No alerts.** Nothing emails me when a sensitive field changes. I go and look.
- **No "watch only these people."** The only people control is the exclusion list — I
  cannot say "record Anna and nobody else."
- **No tamper-proofing.** An audit administrator can delete recorded history. This is
  a record of activity, not a sealed evidence vault.
- **No reports or dashboards.** Lists, grouping and search only.

---

## 6. How we'll know it works (acceptance criteria)

1. I can set up watching on **Contacts**, leave it in **Draft**, and confirm that
   nothing is recorded yet.
2. I press **Confirm**, change a contact's phone number, and find one recorded event
   showing **the old phone number and the new one**, my name, and the time.
3. I create a contact and find a recorded event listing the values it was created with.
4. I delete a contact and find a recorded event for the deletion — and, with "keep a
   copy on deletion" switched on, the full contents of the contact as it stood.
5. I export ten contacts to a spreadsheet, find a recorded event for the export, and
   press its button to see **exactly those ten records**.
6. I add the integration user to the **people to leave out**, have that user change a
   contact, and confirm **no** event is recorded.
7. I add a field to the **fields to leave out**, change that field, and confirm the
   event does not show it.
8. On the contact itself, **View logs** shows only that contact's history.
9. I can group the full history by person, by kind of record, by date, and by working
   session.
10. I press **Set to Draft** and confirm that changes stop being recorded.
11. Trying to set up a **second** set of watch settings on Contacts is refused with a
    message telling me to edit the existing one.
12. The scheduled clean-up is present and **switched off** after installation; when I
    switch it on and set an age, older history is removed and newer history is kept.
13. A user with **Auditor** access can read the history but cannot change the watch
    settings.
