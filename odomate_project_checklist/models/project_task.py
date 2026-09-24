from odoo import Command, api, fields, models
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    checklist_template_id = fields.Many2one(
        'project.checklist.template', string='Checklist', copy=True,
        help="Picking a checklist copies its steps into this task. Once a step has been "
             "started, done or cancelled, use Replace Checklist to switch to another one.")
    checklist_line_ids = fields.One2many(
        'project.task.checklist.line', 'task_id', string='Checklist Steps', copy=True)
    checklist_progress = fields.Float(
        string='Checklist Progress', compute='_compute_checklist_progress',
        store=True, aggregator='avg',
        help="Done steps divided by all steps that are not cancelled.")
    checklist_has_progress = fields.Boolean(
        string='Checklist Started', compute='_compute_checklist_progress', store=True)
    checklist_date_start = fields.Date(
        string='Checklist Start Date', copy=False,
        help="Set automatically the first time a checklist step is started, if empty.")
    checklist_date_end = fields.Date(
        string='Checklist End Date', copy=False, compute='_compute_checklist_date_end',
        store=True, readonly=False,
        help="Set automatically when the checklist reaches 100%, cleared again if it "
             "drops below 100%.")

    @api.depends('checklist_line_ids.state')
    def _compute_checklist_progress(self):
        for task in self:
            states = task.checklist_line_ids.mapped('state')
            eligible = len(states) - states.count('cancelled')
            task.checklist_progress = (
                states.count('done') * 100.0 / eligible if eligible else 0.0)
            task.checklist_has_progress = any(state != 'to_do' for state in states)

    @api.depends('checklist_line_ids.state')
    def _compute_checklist_date_end(self):
        today = fields.Date.context_today(self)
        for task in self:
            states = task.checklist_line_ids.mapped('state')
            if not states:
                continue
            eligible = len(states) - states.count('cancelled')
            if eligible and states.count('done') == eligible:
                if not task.checklist_date_end:
                    task.checklist_date_end = today
            else:
                task.checklist_date_end = False

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        for task, vals in zip(tasks, vals_list):
            if task.checklist_template_id and not vals.get('checklist_line_ids'):
                task._apply_checklist_template(task.checklist_template_id)
        return tasks

    def write(self, vals):
        if 'checklist_template_id' not in vals:
            return super().write(vals)
        new_template = self.env['project.checklist.template'].browse(
            vals['checklist_template_id'])
        changed = self.filtered(lambda t: t.checklist_template_id != new_template)
        confirmed = self.env.context.get('checklist_replace_confirmed')
        if new_template and not confirmed:
            blocked = changed.filtered('checklist_has_progress')
            if blocked:
                raise UserError(self.env._(
                    "The checklist of task \"%(task)s\" is already in progress. "
                    "Use the Replace Checklist button to switch to another checklist.",
                    task=blocked[0].display_name,
                ))
        res = super().write(vals)
        if new_template:
            changed._apply_checklist_template(new_template)
        if confirmed:
            changed.checklist_date_end = False
        return res

    def _prepare_checklist_line_vals(self, template):
        self.ensure_one()
        return [
            {
                'task_id': self.id,
                'name': line.name,
                'note': line.note,
                'sequence': line.sequence,
                'template_line_id': line.id,
            }
            for line in template.line_ids.sorted(lambda l: (l.sequence, l.id))
        ]

    def _apply_checklist_template(self, template):
        vals_list = []
        for task in self:
            vals_list += task._prepare_checklist_line_vals(template)
        self.checklist_line_ids.unlink()
        self.env['project.task.checklist.line'].create(vals_list)
        return True

    def action_open_checklist_replace_wizard(self):
        self.ensure_one()
        return {
            'name': self.env._('Replace Checklist'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.checklist.replace.wizard',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {'default_task_id': self.id},
        }
