from odoo import fields, models


class OdomateHrFormTemplate(models.Model):
    _name = 'odomate.hr.form.template'
    _description = 'HR Form / Template'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(string="Name", required=True, index=True)
    note = fields.Text(string="Note")
    active = fields.Boolean(string="Active", default=True)

    _name_uniq = models.Constraint(
        'UNIQUE(name)',
        "A form or template with this name already exists.",
    )
