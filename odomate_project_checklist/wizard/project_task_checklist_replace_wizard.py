from odoo import api, fields, models


class ProjectTaskChecklistReplaceWizard(models.TransientModel):
    _name = 'project.task.checklist.replace.wizard'
    _description = 'Replace Task Checklist'

    task_id = fields.Many2one(
        'project.task', string='Task', required=True, readonly=True, ondelete='cascade')
    current_template_id = fields.Many2one(
        related='task_id.checklist_template_id', string='Current Checklist')
    new_template_id = fields.Many2one(
        'project.checklist.template', string='New Checklist', required=True,
        ondelete='cascade', domain="[('id', '!=', current_template_id)]")
    warning_message = fields.Char(string='Warning', compute='_compute_warning_message')

    @api.depends('task_id', 'new_template_id')
    def _compute_warning_message(self):
        for wizard in self:
            lines = wizard.task_id.checklist_line_ids
            wizard.warning_message = self.env._(
                "%(count)s current step(s) (%(done)s done, %(started)s in progress, "
                "%(cancelled)s cancelled) will be deleted and replaced by the steps of "
                "\"%(template)s\". The End Date will be cleared.",
                count=len(lines),
                done=len(lines.filtered(lambda l: l.state == 'done')),
                started=len(lines.filtered(lambda l: l.state == 'in_progress')),
                cancelled=len(lines.filtered(lambda l: l.state == 'cancelled')),
                template=wizard.new_template_id.display_name or self.env._('the new checklist'),
            )

    def action_confirm(self):
        self.ensure_one()
        self.task_id.with_context(checklist_replace_confirmed=True).write(
            {'checklist_template_id': self.new_template_id.id})
        return {'type': 'ir.actions.act_window_close'}
