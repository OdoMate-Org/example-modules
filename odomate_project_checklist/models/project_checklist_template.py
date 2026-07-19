from odoo import api, fields, models


class ProjectChecklistTemplate(models.Model):
    _name = 'project.checklist.template'
    _description = 'Project Checklist Template'
    _order = 'name'

    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)

    line_ids = fields.One2many(
        'project.checklist.template.line',
        'template_id',
        string='Steps',
        copy=True,
    )
    line_count = fields.Integer(
        string='Step Count',
        compute='_compute_line_count',
        store=True,
    )

    @api.depends('line_ids')
    def _compute_line_count(self):
        for template in self:
            template.line_count = len(template.line_ids)


class ProjectChecklistTemplateLine(models.Model):
    _name = 'project.checklist.template.line'
    _description = 'Project Checklist Template Step'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    note = fields.Text()
    sequence = fields.Integer(default=10)

    template_id = fields.Many2one(
        'project.checklist.template',
        string='Checklist Template',
        required=True,
        ondelete='cascade',
        index=True,
    )
