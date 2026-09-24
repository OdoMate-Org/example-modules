from odoo import fields, models


class ProjectChecklistTemplateLine(models.Model):
    _name = 'project.checklist.template.line'
    _description = 'Project Checklist Template Step'
    _order = 'template_id, sequence, id'

    name = fields.Char(required=True)
    note = fields.Text()
    sequence = fields.Integer(default=10)
    template_id = fields.Many2one(
        'project.checklist.template', string='Checklist Template',
        required=True, ondelete='cascade', index=True)
