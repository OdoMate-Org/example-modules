# SPEC.md — the business specification this module was generated from

This is the finalized specification produced during the OdoMate refinement
conversation, verbatim. The module in this folder was generated from it —
code, views, security, demo data, tests, and the user guide in `doc/` —
and published after human security review, unedited apart from publication
metadata (store banner reference).

Generated with OdoMate (https://www.odomate.pro) — July 2026, Odoo 19 Community.

---

## Module: project_checklist
Reusable step-by-step checklists that can be attached to Project tasks, with per-task customization, progress tracking, and auto-stamped start/end dates.

### Models

- **project.checklist.template**: name (Char, required), description (Text), active (Boolean, default True)
  - Relations: One2many to `project.checklist.template.line` (line_ids)
  - Computed fields: line_count (Integer, count of line_ids)

- **project.checklist.template.line**: name (Char, required), note (Text, optional), sequence (Integer, default 10)
  - Relations: Many2one to `project.checklist.template` (template_id, required, ondelete=cascade)
  - Draggable ordering via sequence + handle widget

- **project.task.checklist.line**: name (Char, required), note (Text, optional), sequence (Integer, default 10), state (Selection: to_do/in_progress/done/cancelled, default to_do, required)
  - Relations: Many2one to `project.task` (task_id, required, ondelete=cascade); Many2one to `project.checklist.template.line` (template_line_id, optional, ondelete=set null — traceability only, not enforced since lines are freely customizable per task)
  - Timestamps: state_in_progress_date, state_done_date (Datetime, copy=False) — internal bookkeeping to detect "first ever" transitions for the task-level date stamping

- **project.task** (inherited): checklist_template_id (Many2one to `project.checklist.template`, the picker), checklist_line_ids (One2many to `project.task.checklist.line`, task_id), checklist_progress (Float, computed, store=True), date_start (Date), date_end (Date)
  - Computed fields: checklist_progress = done_count / (total_count - cancelled_count) * 100, guarded against division by zero (0 if no eligible lines); depends on checklist_line_ids and each line's state

- **project.task.checklist.replace.wizard** (TransientModel, confirmation only): new_template_id (Many2one, readonly, prefilled), task_id (Many2one, readonly, prefilled), warning_message (Char, computed display text)
  - Used only when replacing a checklist that already has non-to-do progress

### Business Rules
- **Applying a checklist (first time)**: picking checklist_template_id on an empty/untouched task (no lines, or all lines still to_do) immediately copies the template's lines into checklist_line_ids as to_do — no confirmation needed.
- **Switching checklists (with existing progress)**: if any current line is in_progress/done/cancelled, changing checklist_template_id opens the replace wizard; confirming deletes the old lines and copies the new template's lines fresh (all to_do). Declining leaves the task's checklist untouched and reverts the dropdown.
- **Free customization**: once applied, task checklist lines are a fully independent copy — users may add ad-hoc lines, delete lines, edit name/note, and drag-reorder, all without touching the source template.
- **State transitions**: to_do -> in_progress -> done, or -> cancelled from any non-done state. Three action buttons (Start, Done, Cancel) are shown/hidden based on current state (e.g., "Start" hidden once already in_progress/done/cancelled); the state field itself stays visible/editable as a fallback for corrections (e.g., undoing an accidental click).
- **Progress calculation**: cancelled lines are excluded from both numerator and denominator, so cancelling a step can't cap progress below 100%.
- **Start Date auto-stamp**: the first time any checklist line on the task transitions to in_progress, if date_start is empty, set it to today. Stays untouched afterward (including across checklist switches) — it represents the task's own timeline, not the checklist's. Always manually editable.
- **End Date auto-stamp**: when checklist_progress recomputes to exactly 100 (requires at least one eligible line, so an all-cancelled checklist never triggers this), if date_end is empty, set it to today. Always manually editable.
- **End Date self-healing**: if date_end was set and further changes (new line added, a done line reopened, etc.) drop progress back below 100%, date_end is automatically cleared so it can re-stamp honestly on the next real completion.
- **Checklist-switch date handling**: on a confirmed replace, date_end is cleared (task is incomplete again under the new checklist); date_start is left as-is, or — if still empty — remains empty and will stamp naturally on the new checklist's first in_progress step.
- No automatic emails/reminders on step changes (explicitly out of scope for v1).

### Views & UX
- **Task form**: checklist_template_id dropdown near the top of the task; a "Checklist" notebook tab appears once lines exist, containing a progress bar (percentage) followed by an editable list of checklist_line_ids — drag handle, name, note, a color-coded state badge, and three inline action buttons (Start / Done / Cancel), each invisible when not applicable to the current state.
  - Row color-coding: decoration-success (green) for done, decoration-danger (red) for cancelled, decoration-warning/info highlight for in_progress, default for to_do.
  - date_start and date_end shown as plain editable date fields in the task's main info area (alongside existing deadline field).
- **Task list view**: add a checklist_progress column using the built-in progress-bar widget so every task's completion is scannable without opening it.
- **Project Settings**: new "Checklists" menu (list + form) for project.checklist.template — list shows name and line_count; form has name, description, and an editable, drag-reorderable list of template lines (name, note, sequence handle).
- **Replace confirmation**: a small wizard dialog (standard form, no custom scripting) shown only when switching checklists on a task with existing progress; confirms or cancels the replace.
- OWL complexity: none — built-in progressbar widget, list decorations, and a standard confirmation wizard cover every requirement.
- No special mobile/responsive work needed beyond Odoo's default responsive form/list behavior.

### Security
- Groups: uses existing `base.group_user` (all internal users) and existing `project.group_project_manager` (Project Manager) — no new custom groups needed.
- project.checklist.template & project.checklist.template.line: read access for all internal users (so anyone can browse/pick from the library); create/write/unlink restricted to Project Manager.
- project.task.checklist.line: full read/create/write/unlink for all internal users, so anyone can manage the checklist on tasks they can access.
- project.task.checklist.replace.wizard: create/read/write for all internal users (transient, self-cleaning).
- Record rule on project.task.checklist.line mirroring project.task's own visibility (line's task_id.project_id must be in the user's allowed projects), so checklist data access never exceeds a user's existing task access.
- Menu structure: "Checklists" entry added under Project > Configuration (visible only to users with template read access, i.e., all internal users, matching how other configuration lists behave).

### Demo Data
- 3 reusable checklist templates:
  - "New Client Onboarding" — 5 steps (Create Account, Send Welcome Email, Schedule Kick-off Call, Set Up Shared Folder, Confirm First Invoice).
  - "Website Launch Checklist" — 4 steps.
  - "Employee Offboarding" — 4 steps.
- 4-5 demo tasks in existing demo projects, each with a checklist applied and a realistic mixed state: one fully to_do (fresh), one mid-progress with a mix of done/in_progress/to_do (showing the progress bar and colors), one with a cancelled step (showing progress excludes it), and one fully done (with both date_start and date_end auto-populated) to demonstrate the end-to-end flow.

### Constraints & Notes
- Checklist templates are global (no per-company isolation) — not raised as a requirement; can be revisited if multi-company separation is needed later.
- Editing a template after it's already been used on tasks does NOT retroactively change those tasks' checklists — each task holds its own independent copy from the moment it was applied.
- No per-step assignment — the task's existing assignee still owns all steps (explicitly excluded from v1).
- No reports/dashboards beyond the on-task and in-list progress bars (explicitly excluded from v1).
