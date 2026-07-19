from odoo import Command, _, api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    checklist_template_id = fields.Many2one(
        'project.checklist.template',
        string='Checklist',
        help="Pick a checklist template to load its steps onto this task.",
    )
    # Internal: which template's steps are currently loaded on the task.
    applied_template_id = fields.Many2one(
        'project.checklist.template',
        string='Applied Checklist',
        copy=False,
        readonly=True,
    )
    checklist_line_ids = fields.One2many(
        'project.task.checklist.line',
        'task_id',
        string='Checklist Steps',
        copy=True,
    )
    checklist_progress = fields.Float(
        string='Checklist Progress',
        compute='_compute_checklist_progress',
        store=True,
        aggregator='avg',
        help="Share of eligible steps marked done. Cancelled steps are "
             "excluded from the calculation.",
    )
    checklist_has_progress = fields.Boolean(
        string='Checklist Started',
        compute='_compute_checklist_has_progress',
    )
    checklist_needs_apply = fields.Boolean(
        string='Checklist Change Pending',
        compute='_compute_checklist_needs_apply',
    )

    date_start = fields.Date(
        string='Start Date',
        copy=False,
        help="Auto-stamped the first time a checklist step starts. "
             "Always editable.",
    )
    date_end = fields.Date(
        string='End Date',
        copy=False,
        help="Auto-stamped when the checklist reaches 100%. Cleared "
             "automatically if progress drops back below 100%. Always "
             "editable.",
    )

    # -- Computes ----------------------------------------------------------

    @api.depends('checklist_line_ids', 'checklist_line_ids.state')
    def _compute_checklist_progress(self):
        for task in self:
            eligible = task.checklist_line_ids.filtered(
                lambda line: line.state != 'cancelled')
            total = len(eligible)
            if not total:
                task.checklist_progress = 0.0
                continue
            done = len(eligible.filtered(lambda line: line.state == 'done'))
            task.checklist_progress = (done / total) * 100.0

    @api.depends('checklist_line_ids.state')
    def _compute_checklist_has_progress(self):
        for task in self:
            task.checklist_has_progress = any(
                line.state != 'to_do' for line in task.checklist_line_ids)

    @api.depends('checklist_template_id', 'applied_template_id')
    def _compute_checklist_needs_apply(self):
        for task in self:
            task.checklist_needs_apply = bool(task.checklist_template_id) and (
                task.checklist_template_id != task.applied_template_id)

    # -- Date stamping helpers ---------------------------------------------

    def _stamp_checklist_start_date(self):
        """Stamp today on date_start the first time a step starts."""
        today = fields.Date.context_today(self)
        for task in self:
            if not task.date_start:
                task.date_start = today

    def _sync_checklist_end_date(self):
        """Stamp date_end when fully complete; clear it (self-heal) when not.

        Progress can only reach 100 when at least one eligible (non-cancelled)
        step exists, so an all-cancelled checklist never stamps an end date.
        """
        today = fields.Date.context_today(self)
        for task in self:
            if task.checklist_progress >= 100.0:
                if not task.date_end:
                    task.date_end = today
            elif task.date_end:
                task.date_end = False

    # -- Applying / replacing a checklist ----------------------------------

    def _apply_checklist_template(self, template):
        """Replace the task's checklist steps with a fresh copy of ``template``.

        All new steps start as ``to_do``. ``date_end`` is cleared because the
        task is incomplete again under the new checklist; ``date_start`` is
        left untouched (it belongs to the task's own timeline).
        """
        self.ensure_one()
        commands = [Command.clear()]
        for tmpl_line in template.line_ids:
            commands.append(Command.create({
                'name': tmpl_line.name,
                'note': tmpl_line.note,
                'sequence': tmpl_line.sequence,
                'template_line_id': tmpl_line.id,
                'state': 'to_do',
            }))
        vals = {
            'checklist_line_ids': commands,
            'applied_template_id': template.id,
            'date_end': False,
        }
        if self.checklist_template_id != template:
            vals['checklist_template_id'] = template.id
        self.with_context(checklist_applying=True).write(vals)

    def action_open_checklist_replace_wizard(self):
        """Open the confirmation dialog before replacing a started checklist.

        Clicking this ``type="object"`` button auto-saves the dirty form, so
        the freshly-picked template is already persisted on
        ``checklist_template_id``. We revert the picker back to the applied
        template right away and hand the intended new template to the wizard.
        That way declining the wizard leaves the task fully consistent (picker
        matches the applied checklist), while confirming re-applies the new
        template through :meth:`_apply_checklist_template`.
        """
        self.ensure_one()
        new_template = self.checklist_template_id
        # Revert the picker without re-triggering the apply logic in write().
        self.with_context(checklist_applying=True).write({
            'checklist_template_id': self.applied_template_id.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Replace Checklist'),
            'res_model': 'project.task.checklist.replace.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_task_id': self.id,
                'default_new_template_id': new_template.id,
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        # The web client saves a brand-new task via create(), so the
        # apply-on-pick logic that lives in write() would never fire for a
        # first-time checklist. Apply the picked template right after create;
        # a new task can never have prior progress, so no confirmation is
        # needed.
        tasks = super().create(vals_list)
        for task in tasks:
            template = task.checklist_template_id
            if template and template != task.applied_template_id:
                task._apply_checklist_template(template)
        return tasks

    def write(self, vals):
        # Guard against re-entrancy while we apply a template internally.
        if self.env.context.get('checklist_applying'):
            return super().write(vals)

        template_change = 'checklist_template_id' in vals
        had_progress = {}
        if template_change:
            had_progress = {
                task.id: task.checklist_has_progress for task in self}

        res = super().write(vals)

        if template_change:
            confirmed = self.env.context.get('checklist_replace_confirmed')
            for task in self:
                template = task.checklist_template_id
                if not template or template == task.applied_template_id:
                    continue
                # Untouched checklist (no lines or all still to_do) applies
                # immediately; a started checklist waits for confirmation.
                if confirmed or not had_progress.get(task.id):
                    task._apply_checklist_template(template)
        return res
