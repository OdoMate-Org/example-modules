from odoo import api, fields, models


class ProjectTaskChecklistReplaceWizard(models.TransientModel):
    _name = 'project.task.checklist.replace.wizard'
    _description = 'Replace Task Checklist Confirmation'

    task_id = fields.Many2one(
        'project.task',
        string='Task',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    new_template_id = fields.Many2one(
        'project.checklist.template',
        string='New Checklist',
        required=True,
        readonly=True,
    )
    warning_message = fields.Char(
        string='Warning',
        compute='_compute_warning_message',
    )

    @api.depends('task_id', 'new_template_id')
    def _compute_warning_message(self):
        for wizard in self:
            count = len(wizard.task_id.checklist_line_ids)
            wizard.warning_message = (
                "This task already has %(count)s checklist step(s) with "
                "progress. Replacing it with \"%(name)s\" deletes the current "
                "steps and starts fresh. This cannot be undone."
            ) % {
                'count': count,
                'name': wizard.new_template_id.display_name or '',
            }

    def action_confirm(self):
        self.ensure_one()
        self.task_id._apply_checklist_template(self.new_template_id)
        return {'type': 'ir.actions.act_window_close'}
