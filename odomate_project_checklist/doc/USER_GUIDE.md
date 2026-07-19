# Project Task Checklists — User Guide

Reusable, step-by-step checklists for Odoo **Project** tasks, with per-task
customization, live progress tracking, and automatically stamped start/end
dates.

## Table of Contents

1. [Overview](#1-overview)
2. [Installation](#2-installation)
3. [Building Checklist Templates](#3-building-checklist-templates)
4. [Applying a Checklist to a Task](#4-applying-a-checklist-to-a-task)
5. [Working Through the Steps](#5-working-through-the-steps)
6. [Progress and Automatic Dates](#6-progress-and-automatic-dates)
7. [Switching or Replacing a Checklist](#7-switching-or-replacing-a-checklist)
8. [Security & Access](#8-security--access)
9. [Field Reference](#9-field-reference)
10. [Limitations](#10-limitations)

## 1. Overview

This module lets you define checklist **templates** (a named list of steps)
once, then attach them to any project task. When a template is applied, its
steps are copied onto the task as an **independent copy** — you can add,
delete, rename, re-order, and mark steps without ever affecting the source
template.

Each task shows a progress bar next to its **End Date**, and two dates fill
themselves in as work happens: the **Start Date** stamps when the first step
begins, and the **End Date** stamps when everything eligible is done.

## 2. Installation

1. Copy the `project_checklist` folder into your Odoo addons path.
2. Enable **Developer Mode**, then update the Apps list.
3. Search for **Project Task Checklists** and click **Install**.

The module depends on **Project** (`project`); Odoo installs it automatically
if needed.

## 3. Building Checklist Templates

Go to **Project → Configuration → Checklists**.

- The list shows each template's **Name** and its **Step Count**.
- Open or create a template. Give it a name (e.g. *New Client Onboarding*)
  and an optional description.
- In the **Steps** tab, add rows. Each step has a **Name**, an optional
  **Note**, and a drag handle (⠿) to re-order them. Order is stored in the
  `sequence` field.

> Only **Project Managers** can create or edit templates. Every internal user
> can read them, so anyone can pick a template when working on a task.

Three ready-to-use templates ship as demo data: *New Client Onboarding*
(5 steps), *Website Launch Checklist* (4 steps), and *Employee Offboarding*
(4 steps).

## 4. Applying a Checklist to a Task

Open any task (**Project → Tasks**). Near the deadline you'll find the
**Checklist** picker, followed by **Start Date**, **End Date**, and a
**progress bar**.

- Pick a template on a task with **no checklist yet** (or one where every step
  is still *To Do*): the steps copy in immediately as *To Do*. No confirmation
  is needed. This works both on a saved task and while filling out a
  **brand-new** task — the steps are copied in as soon as you save.
- A new **Checklist** tab appears as soon as steps exist, and the progress bar
  next to **End Date** appears with it.
- The progress bar lives in the task's main info area, not inside the
  **Checklist** tab — it stays visible no matter which tab (Description,
  Sub-tasks, Checklist, …) is currently open.

## 5. Working Through the Steps

In the **Checklist** tab, each step row shows the drag handle, name, note, a
**Status** field, and three inline buttons. (The progress bar itself is not in
this tab — see [Progress and Automatic Dates](#6-progress-and-automatic-dates).)

| Button | Appears when | Sets status to |
|--------|--------------|----------------|
| **Start** | status is *To Do* | *In Progress* |
| **Done** | status is *To Do* or *In Progress* | *Done* |
| **Cancel** | status is *To Do* or *In Progress* | *Cancelled* |

Rows are color-coded: **green** for *Done*, **red** for *Cancelled*, **orange**
for *In Progress*, default for *To Do*.

The **Status** field itself stays editable, so you can correct an accidental
click (for example, set a *Done* step back to *In Progress*).

You can also freely add ad-hoc steps, delete steps, or rename them — the task's
checklist is entirely its own copy.

## 6. Progress and Automatic Dates

**Progress** = done steps ÷ eligible steps × 100, where *eligible* excludes
**Cancelled** steps. So cancelling a step can never hold progress below 100%.

Worked example — a 4-step checklist:

| Step | Status |
|------|--------|
| Review Content | Done |
| Test on Mobile | Done |
| Configure Analytics | Cancelled |
| Point DNS | Done |

Eligible steps = 3 (the cancelled one is excluded). Done = 3.
Progress = 3 ÷ 3 × 100 = **100%**.

**Start Date** — the first time any step moves to *In Progress*, today's date
is written to **Start Date** if it was empty. It is never overwritten
afterward (it belongs to the task's own timeline) and is always manually
editable.

**End Date** — when progress reaches exactly 100%, today's date is written to
**End Date** if it was empty. If a later change drops progress back below 100%
(you add a step, or reopen a done one), the End Date is **cleared
automatically** so it can re-stamp honestly on the next real completion. An
all-cancelled checklist has no eligible steps, so it never stamps an End Date.

On the task form, the progress bar sits next to **End Date** in the main info
area (not inside the Checklist tab), so it stays visible while you switch
between tabs. The task **list view** also includes a **Checklist Progress**
column (progress-bar widget) so completion is scannable without opening each
task.

## 7. Switching or Replacing a Checklist

If a task's checklist already has progress (any step not *To Do*) and you pick
a different template, the change is **not** applied silently. A **Replace
Checklist** button appears next to the picker. Clicking it opens a confirmation
dialog summarizing how many steps will be deleted and which template will
replace them.

- **Replace** — deletes the current steps and copies the new template fresh
  (all *To Do*). The **End Date** is cleared (the task is incomplete again);
  the **Start Date** is left as-is.
- **Cancel** — leaves the task's checklist untouched and reverts the
  **Checklist** picker back to the currently applied template, so the picker
  and the steps always stay in sync.

## 8. Security & Access

| Model | Internal User | Project Manager |
|-------|---------------|-----------------|
| `project.checklist.template` | Read | Full |
| `project.checklist.template.line` | Read | Full |
| `project.task.checklist.line` | Full | Full |
| `project.task.checklist.replace.wizard` | Full (transient) | Full |

A record rule on `project.task.checklist.line` mirrors task visibility: a step
is never visible to a user who cannot see its task. Managers see all task
checklist steps, matching their task access.

## 9. Field Reference

**project.task.checklist.line**

| Field | Type | Notes |
|-------|------|-------|
| `name` | Char | Required |
| `note` | Text | Optional |
| `sequence` | Integer | Drag-handle ordering |
| `state` | Selection | to_do / in_progress / done / cancelled |
| `task_id` | Many2one | The task (ondelete cascade) |
| `template_line_id` | Many2one | Source template step (traceability only) |

**project.task** (added fields)

| Field | Type | Notes |
|-------|------|-------|
| `checklist_template_id` | Many2one | The picker |
| `checklist_line_ids` | One2many | The task's own steps |
| `checklist_progress` | Float (stored) | 0–100, cancelled steps excluded |
| `date_start` | Date | Auto-stamped on first *In Progress* |
| `date_end` | Date | Auto-stamped at 100%, self-clearing |

## 10. Limitations

- **No per-step assignment.** The task's existing assignee owns all steps.
- **No notifications.** Step changes send no emails or reminders (out of scope
  for v1).
- **Templates are global.** There is no per-company isolation of templates.
- **Editing a template is not retroactive.** Tasks keep the independent copy
  they received when the checklist was applied.
- **No dashboards/reports** beyond the on-task and in-list progress bars.
