from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    hr_identification_expiry_warning_days = fields.Integer(
        string="Identification Expiry Lead Time (Days)",
        default=14,
        help="Number of days before the identification expiry date at which the daily job "
             "sends the warning e-mail. The check is an exact date match, so each employee "
             "is warned once.",
    )
    hr_passport_expiry_warning_days = fields.Integer(
        string="Passport Expiry Lead Time (Days)",
        default=180,
        help="Number of days before the passport expiry date at which the daily job sends "
             "the warning e-mail.",
    )
    hr_auto_create_employee = fields.Boolean(
        string="Create Employee From New Login",
        default=True,
        help="Create an employee record automatically for every new internal user of this "
             "company. Evaluated when the login is created; existing logins are never "
             "touched, and removing a login never deletes its employee.",
    )
    hr_default_notice_period_days = fields.Integer(
        string="Default Notice Period (Days)",
        default=30,
        help="Value proposed for the notice period of a newly created employee version. "
             "Changing it later does not modify versions that already exist.",
    )

    _hr_identification_lead_time_positive = models.Constraint(
        'CHECK(hr_identification_expiry_warning_days >= 0)',
        "The identification expiry lead time cannot be negative.",
    )
    _hr_passport_lead_time_positive = models.Constraint(
        'CHECK(hr_passport_expiry_warning_days >= 0)',
        "The passport expiry lead time cannot be negative.",
    )
    _hr_default_notice_period_positive = models.Constraint(
        'CHECK(hr_default_notice_period_days >= 0)',
        "The default notice period cannot be negative.",
    )
