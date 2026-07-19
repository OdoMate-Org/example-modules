from odoo import api, fields, models


class ProjectTaskChecklistLine(models.Model):
    _name = 'project.task.checklist.line'
    _description = 'Task Checklist Step'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    note = fields.Text()
    sequence = fields.Integer(default=10)
    state = fields.Selection(
        selection=[
            ('to_do', 'To Do'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='to_do',
        required=True,
    )

    task_id = fields.Many2one(
        'project.task',
        string='Task',
        required=True,
        ondelete='cascade',
        index=True,
    )
    template_line_id = fields.Many2one(
        'project.checklist.template.line',
        string='Source Template Step',
        ondelete='set null',
        help="The template step this line was copied from. Kept for "
             "traceability only; task steps are freely customizable.",
    )

    # Internal bookkeeping to detect the very first transition of a step,
    # used to drive the task-level start/end date stamping.
    state_in_progress_date = fields.Datetime(
        string='First Started On', copy=False, readonly=True)
    state_done_date = fields.Datetime(
        string='First Completed On', copy=False, readonly=True)

    # -- State transition helpers ------------------------------------------

    def _update_state_timestamps(self):
        """Stamp the first-ever in_progress / done datetimes on each step."""
        now = fields.Datetime.now()
        for line in self:
            if line.state == 'in_progress' and not line.state_in_progress_date:
                line.state_in_progress_date = now
            if line.state == 'done' and not line.state_done_date:
                line.state_done_date = now

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._update_state_timestamps()
        started = lines.filtered(lambda line: line.state == 'in_progress')
        if started:
            started.task_id._stamp_checklist_start_date()
        lines.task_id._sync_checklist_end_date()
        return lines

    def write(self, vals):
        newly_started = self.browse()
        if vals.get('state') == 'in_progress':
            newly_started = self.filtered(
                lambda line: line.state != 'in_progress')
        res = super().write(vals)
        if 'state' in vals:
            self._update_state_timestamps()
            if newly_started:
                newly_started.task_id._stamp_checklist_start_date()
            self.task_id._sync_checklist_end_date()
        return res

    def unlink(self):
        tasks = self.task_id
        res = super().unlink()
        tasks._sync_checklist_end_date()
        return res

    # -- Inline action buttons ---------------------------------------------

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
