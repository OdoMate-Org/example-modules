# User Guide: Project Task Checklists

> Reusable step-by-step checklists for Odoo Project tasks, with per-step status buttons, a live progress bar, and automatic Start/End dates.

---

## Table of Contents

1. [What does this module do](#1-what-does-this-module-do)
2. [Where to find it in Odoo](#2-where-to-find-it-in-odoo)
3. [First-run setup: create a checklist template](#3-first-run-setup-create-a-checklist-template)
4. [Applying a checklist to a task](#4-applying-a-checklist-to-a-task)
5. [Working through the steps](#5-working-through-the-steps)
6. [How progress is calculated](#6-how-progress-is-calculated)
7. [Start Date and End Date](#7-start-date-and-end-date)
8. [Replacing a checklist that is already in progress](#8-replacing-a-checklist-that-is-already-in-progress)
9. [Task list and search](#9-task-list-and-search)
10. [Access roles](#10-access-roles)
11. [Limitations](#11-limitations)

---

## 1. What does this module do

Many tasks follow the same routine every time: onboarding a client, launching a website, offboarding an employee. This module lets a Project Administrator define that routine once as a **checklist template**. Anyone working on a task then picks the checklist, and its steps are copied into the task. Each step gets a status, the task shows a progress bar, and the task's Start Date and End Date fill in by themselves.

| Capability | Details |
|---|---|
| Reusable templates | **Project → Configuration → Checklists**: a name, a description and an ordered list of steps (each step has a name and an optional note). |
| One-click apply | Picking a template in the task's **Checklist** field copies all its steps into the task. |
| Independent copy per task | Each task's steps can be edited, reordered, added or deleted. Changing the template later **never** changes checklists already applied to tasks. |
| Step statuses | **To Do → In Progress → Done**, or **Cancelled**. **Start**, **Done** and **Cancel** buttons appear on each row. |
| Progress bar | Done steps ÷ (all steps − cancelled steps) × 100. Shown on the task form and as a column in the task list. |
| Automatic dates | **Start Date** is filled in when the first step is started or done. **End Date** is filled in when the checklist reaches 100%, and cleared again if progress drops. |
| Safe replacement | Once work has started, switching to another checklist goes through a confirmation dialog that shows exactly what will be lost. |

---

## 2. Where to find it in Odoo

The module has no top-level menu of its own. It adds to the standard **Project** app:

- **Project → Configuration → Checklists**: create and maintain checklist templates.
- **Project task form**:
  - a **Checklist** field right after **Tags**
  - **Start Date** and **End Date** fields right after **Deadline**
  - a **Checklist** tab in the notebook (shown once the task has at least one step)
- **Project task list view**: a **Checklist Progress** column with a progress bar.
- **Task search**: a **With Checklist** filter, and you can search tasks by **Checklist**.

> 💡 In standard Odoo, the **Project → Configuration** menu is only visible to Project Administrators. Other users can still read the templates and pick them on tasks, but they won't see the Configuration menu.

---

## 3. First-run setup: create a checklist template

**Path:** `Project` → `Configuration` → `Checklists` → `New`

| Field | What to enter | Example |
|---|---|---|
| **Name** (required) | The name users will pick on a task | `New Client Onboarding` |
| **Description** | What the checklist is for (internal note) | `Standard steps to bring a newly signed client on board` |
| **Steps Count** | Read-only. Number of steps in the template | `5` |
| **Steps** tab | One line per step: **Name** (required) and an optional **Note**. Drag the handle (⋮⋮) on the left to reorder. | `Create Account`, `Send Welcome Email`, `Schedule Kick-off Call`, `Set Up Shared Folder`, `Confirm First Invoice` |

The **Checklists** list shows each template's **Name** and **Steps Count**. You can search templates by name, or by **Step** to find every template that contains a given step, for example "Invoice".

To stop offering a template without deleting it, **archive** it (gear/Actions menu → **Archive**). Archived templates no longer appear in the task's **Checklist** dropdown. Tasks that already use them keep their steps. Use the **Archived** filter to find them again.

> 💡 When demo data is loaded, three sample templates are included: *New Client Onboarding* (5 steps), *Website Launch Checklist* (4 steps) and *Employee Offboarding* (4 steps).

---

## 4. Applying a checklist to a task

1. Open any task (**Project → Projects → *your project* → *task***).
2. In the **Checklist** field (next to **Tags**), select a template, e.g. `New Client Onboarding`.
3. Save. All template steps are copied into the task with status **To Do**, and the **Checklist** tab appears.

What you can do with the task's copy:

- **Edit** a step's name or note to fit this task.
- **Reorder** steps with the drag handle.
- **Add** extra steps with *Add a line* at the bottom of the list.
- **Delete** steps that don't apply.

None of this affects the template. It works the other way too: if an administrator later renames, adds or removes steps in the template, tasks that already use it keep their own steps unchanged. Only tasks that apply the template afterwards get the new version.

> 💡 While no step has been started, done or cancelled, you can simply pick a different template in the **Checklist** field. The steps are replaced without any dialog, because nothing has been worked on yet. After work has started, see [section 8](#8-replacing-a-checklist-that-is-already-in-progress).

---

## 5. Working through the steps

Open the **Checklist** tab of the task. At the top is the **Checklist Progress** bar. Below it is the list of steps:

| Column | Meaning |
|---|---|
| ⋮⋮ (handle) | Drag to reorder |
| **Name** | The step |
| **Note** | Optional instructions copied from the template |
| **Status** | Coloured bold text: **To Do**, orange **In Progress**, green **Done**, red **Cancelled**. Click it to pick a status directly (to correct a mistake). |
| Buttons | **Start** (▶), **Done** (✓), **Cancel** (✕). Only the buttons that apply to the current status are shown. |

**Status flow:**

| Current status | Buttons shown | Result |
|---|---|---|
| To Do | **Start**, **Done**, **Cancel** | In Progress / Done / Cancelled |
| In Progress | **Done**, **Cancel** | Done / Cancelled |
| Done | none | change **Status** by hand to reopen |
| Cancelled | none | change **Status** by hand to reopen |

To undo an accidental click (for example a step marked **Done** by mistake), click the **Status** cell and choose the right value, such as **To Do**. Progress and End Date recalculate straight away.

Whole rows are coloured too: **green** for done, **red** for cancelled, **orange** for in progress.

Each step also records when it was first started (**Started On**) and when it was done (**Done On**). These are stored for reference and are not shown in the task form.

---

## 6. How progress is calculated

```
Checklist Progress = Done steps ÷ (All steps − Cancelled steps) × 100
```

Cancelled steps are left out completely, so cancelling a step that doesn't apply doesn't lower the score. If there are no eligible steps (no steps at all, or all steps cancelled), progress is **0%**.

**Worked examples**

| Steps | Done | In Progress | To Do | Cancelled | Calculation | Progress |
|---|---|---|---|---|---|---|
| 5 | 2 | 1 | 2 | 0 | 2 ÷ 5 | **40%** |
| 5 | 2 | 0 | 2 | 1 | 2 ÷ (5 − 1) = 2 ÷ 4 | **50%** |
| 4 | 2 | 0 | 1 | 1 | 2 ÷ (4 − 1) = 2 ÷ 3 | **67%** |
| 3 | 2 | 0 | 0 | 1 | 2 ÷ (3 − 1) = 2 ÷ 2 | **100%** |
| 3 | 0 | 0 | 0 | 3 | no eligible steps | **0%** |

"In Progress" steps count as not done yet. They only count toward progress once they are marked **Done**.

---

## 7. Start Date and End Date

The module adds two **new** date fields to the task, shown as **Start Date** and **End Date** right after **Deadline** (technical names `checklist_date_start` and `checklist_date_end`).

> ℹ️ **Why new fields?** Standard `project.task` already has a technical `date_end` (date and time) that Odoo core manages itself. To avoid interfering with core behaviour, the module does not write to it and keeps its own checklist dates instead.

| Field | Filled in automatically when… | Cleared automatically when… | Editable by hand |
|---|---|---|---|
| **Start Date** | a step becomes **In Progress** or **Done** for the first time **and** the field is empty. It is set to today's date. | never. Once set, it is not changed automatically. | ✅ Always |
| **End Date** | progress reaches **100%** (with at least one step that isn't cancelled) **and** the field is empty. It is set to today's date. | progress drops below 100% (e.g. a new step is added, or a step changes back to not done), **or** the checklist is replaced through the **Replace Checklist** dialog | ✅ Always |

**Example timeline** (template with 4 steps):

| Date | Action | Progress | Start Date | End Date |
|---|---|---|---|---|
| 2 Mar | Checklist applied | 0% | – | – |
| 3 Mar | Step 1 → **Start** | 0% | **3 Mar** | – |
| 5 Mar | Step 1 → **Done**, step 3 → **Cancel** | 1 ÷ 3 = 33% | 3 Mar | – |
| 9 Mar | Steps 2 and 4 → **Done** | 3 ÷ 3 = 100% | 3 Mar | **9 Mar** |
| 10 Mar | A new step "Client sign-off" is added | 3 ÷ 4 = 75% | 3 Mar | *cleared* |
| 12 Mar | "Client sign-off" → **Done** | 100% | 3 Mar | **12 Mar** |

Notes:
- If you typed a Start Date or End Date by hand, automation does not overwrite it with today. Exception: an End Date is still cleared whenever a step changes status while progress is below 100%.
- Replacing the checklist does **not** clear the Start Date, because the work on the task had already begun.

---

## 8. Replacing a checklist that is already in progress

Once **any** step is In Progress, Done or Cancelled, the **Checklist** field becomes read-only and a **Replace Checklist** button (⇄) appears below it. This protects the recorded work from being wiped by an accidental dropdown change.

1. Click **Replace Checklist**. A dialog opens showing the **Task** and its **Current Checklist**.
2. Choose the **New Checklist** (the current one is not offered).
3. Read the warning. It shows exactly what will be lost, e.g. *"5 current step(s) (2 done, 1 in progress, 1 cancelled) will be deleted and replaced by the steps of "Website Launch Checklist". The End Date will be cleared."*
4. Click **Replace Checklist** to confirm. All current steps are deleted, the new template's steps are copied in as **To Do**, and **End Date** is cleared. **Start Date** is kept.
   Or click **Discard** to close the dialog. Nothing is changed.

> ℹ️ **Why a button and not a pop-up on the dropdown?** In Odoo, changing a field on a form (an "onchange") cannot open a confirmation dialog without custom JavaScript, and this module was deliberately built without custom JavaScript. So the dropdown is locked once work has started, and the replacement goes through this explicit dialog. If someone tries to change the checklist another way (e.g. import), Odoo rejects it with: *"The checklist of task … is already in progress. Use the Replace Checklist button to switch to another checklist."*

---

## 9. Task list and search

- **Checklist Progress column**: the task list view (for example **Project → Projects → *project*** in list mode) shows a progress bar per task. The column is optional, so you can hide or show it from the column selector. When the list is grouped, the group row shows the **average** progress.
- **With Checklist** filter (in the task search panel's Filters): shows only tasks that have at least one checklist step.
- **Search by Checklist**: type a template name in the search bar and pick *Search Checklist for: …* to find every task using that template.

---

## 10. Access roles

| Role | Checklist templates (and their steps) | Task checklist steps | Replace Checklist dialog |
|---|---|---|---|
| **Internal user** (`base.group_user`) | ✅ Read only (can pick templates on tasks) | ✅ Read / create / edit / delete, **only on tasks they can see** (see below), within their allowed companies | ✅ Can use it |
| **Project Administrator** (`project.group_project_manager`) | ✅ Read / create / edit / delete | ✅ Read / create / edit / delete on **all** tasks of their allowed companies | ✅ Can use it |

**Which task steps an internal user can see and edit.** Steps follow the task's project visibility. A user can manage steps of a task when **any** of these is true:
- the task's project is visible to all internal employees (or also to portal users),
- the user follows the task's project,
- the user follows the task,
- the user is assigned to the task.

In addition, the task must belong to one of the user's allowed companies (or have no company).

**Templates are global.** They have no company field, so every company in a multi-company database sees the same templates.

To assign roles: `Settings` → `Users & Companies` → `Users` → select the user → **Project** access level (**User** or **Administrator**).

---

## 11. Limitations

| Topic | Limitation |
|---|---|
| Notifications | No emails, chatter messages, activities or reminders are sent when a step changes status. |
| Assignment | Steps have no individual assignee or due date. The task's assignees are responsible for the whole checklist. |
| Reopening steps | There is no button to reopen a **Done** or **Cancelled** step. Change its **Status** cell by hand instead. |
| Reporting | No dedicated reports, dashboards or PDF. You can use the **Checklist Progress** column, the list's group-by average, and the **With Checklist** filter. |
| Step timestamps | **Started On** / **Done On** are recorded per step but are not displayed in the standard views. |
| Multi-company | Templates are not company-specific. All companies share the same template list. |
| Switching templates | Once any step has been started, done or cancelled, you can't switch by re-selecting in the dropdown. Use the **Replace Checklist** button. Replacing deletes the current steps, including their statuses. This cannot be undone. |
| Template updates | Changes to a template are not pushed to tasks that already use it. This is by design. |
| Clearing the Checklist field | Emptying the **Checklist** field (on a task with no progress) does not delete the steps already copied. Delete them from the **Checklist** tab if needed. |
| Menu visibility | **Project → Configuration → Checklists** sits under the standard Configuration menu, which Odoo shows only to Project Administrators. |
