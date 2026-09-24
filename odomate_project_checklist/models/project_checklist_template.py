from odoo import api, fields, models


class ProjectChecklistTemplate(models.Model):
    _name = 'project.checklist.template'
    _description = 'Project Checklist Template'
    _order = 'name, id'

    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
    line_ids = fields.One2many(
        'project.checklist.template.line', 'template_id', string='Steps', copy=True)
    line_count = fields.Integer(string='Steps Count', compute='_compute_line_count')

    @api.depends('line_ids')
    def _compute_line_count(self):
        for template in self:
            template.line_count = len(template.line_ids)
