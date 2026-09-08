from odoo import api, fields, models
from odoo.exceptions import ValidationError


class OdomateHrDocumentType(models.Model):
    _name = 'odomate.hr.document.type'
    _description = 'Employee Document Type'
    _order = 'name'

    name = fields.Char(string="Name", required=True, index=True)
    reminder_days = fields.Integer(
        string="Reminder Days",
        default=30,
        help="Number of days used by the chasing pattern to decide when reminders fire.",
    )
    chasing_pattern = fields.Selection(
        [
            ('on_expiry', "On the expiry date only"),
            ('before_expiry', "Once, N days before expiry"),
            ('daily_before', "Every day from N days before expiry until expiry"),
            ('daily_after', "Every day from expiry until N days after expiry"),
        ],
        string="Chasing Pattern",
        required=True,
        default='before_expiry',
    )
    active = fields.Boolean(string="Active", default=True)

    _name_uniq = models.Constraint(
        'UNIQUE(name)',
        "A document type with this name already exists.",
    )

    @api.constrains('chasing_pattern', 'reminder_days')
    def _check_reminder_days(self):
        for document_type in self:
            if document_type.reminder_days < 0:
                raise ValidationError(
                    self.env._(
                        "Reminder Days on %(name)s cannot be negative.",
                        name=document_type.name,
                    )
                )
            if document_type.chasing_pattern != 'on_expiry' and document_type.reminder_days <= 0:
                raise ValidationError(
                    self.env._(
                        "Document type %(name)s uses a chasing pattern that needs a "
                        "reminder delay, so Reminder Days must be greater than zero.",
                        name=document_type.name,
                    )
                )
