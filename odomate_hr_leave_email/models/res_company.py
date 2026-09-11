from odoo import api, fields, models

LEAVE_ALIAS_XMLID = 'odomate_hr_leave_email.mail_alias_hr_leave_request'


class ResCompany(models.Model):
    _inherit = 'res.company'

    leave_email_enabled = fields.Boolean(
        string="Time Off Requests by Email",
        default=False,
        help="Turn emails sent to the Time Off address into Time Off requests.",
    )
    leave_email_alias_id = fields.Many2one(
        comodel_name='mail.alias',
        string="Time Off Email Alias",
        compute='_compute_leave_email_alias_id',
        readonly=True,
        help="The single email alias shipped by this module. The address is "
             "the same for every company.",
    )
    leave_email_type_id = fields.Many2one(
        comodel_name='hr.leave.type',
        string="Time Off Type for Email Requests",
        ondelete='set null',
        help="Type given to every Time Off request created from an email. "
             "Requests are refused while this is empty or archived.",
    )
    leave_email_reply_on_failure = fields.Boolean(
        string="Reply on Refusal",
        default=True,
        help="Send an explanatory answer back to the sender when the email "
             "could not be turned into a Time Off request.",
    )

    @api.depends()
    def _compute_leave_email_alias_id(self):
        alias = self.env.ref(LEAVE_ALIAS_XMLID, raise_if_not_found=False)
        for company in self:
            company.leave_email_alias_id = alias
