import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

FAILURE_TEMPLATE_XMLID = 'odomate_hr_leave_email.mail_template_leave_email_failure'


class OdomateHrLeaveEmailLog(models.Model):
    _name = 'odomate.hr.leave.email.log'
    _description = 'Time Off Email Request Log'
    _order = 'received_date desc, id desc'
    _rec_name = 'subject'

    received_date = fields.Datetime(
        string="Received On",
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    email_from = fields.Char(string="From")
    subject = fields.Char(string="Subject")
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Employee",
        ondelete='set null',
        index=True,
        help="Employee the sender address was resolved to. Empty when no "
             "employee could be matched.",
    )
    leave_id = fields.Many2one(
        comodel_name='hr.leave',
        string="Time Off Request",
        ondelete='set null',
        index=True,
        help="Time Off request created from this email.",
    )
    state = fields.Selection(
        selection=[
            ('created', "Created"),
            ('rejected', "Rejected"),
        ],
        string="Result",
        required=True,
        default='rejected',
        index=True,
    )
    failure_reason = fields.Selection(
        selection=[
            ('unknown_sender', "Unknown sender"),
            ('no_date', "No date found"),
            ('reversed_dates', "End date before start date"),
            ('no_leave_type', "Time Off type not configured"),
            ('disabled', "Feature disabled"),
            ('other', "Unexpected error"),
        ],
        string="Reason",
        index=True,
    )
    notes = fields.Text(string="Details")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        index=True,
        help="Company of the resolved employee. Empty when the sender could "
             "not be matched to any employee.",
    )

    @api.depends('subject', 'email_from', 'received_date')
    def _compute_display_name(self):
        for log in self:
            subject = log.subject or self.env._("(no subject)")
            log.display_name = "%s - %s" % (log.email_from or self.env._("unknown"), subject)

    def _odomate_send_failure_reply(self, company):
        self.ensure_one()
        if not self.email_from or not company or not company.leave_email_reply_on_failure:
            return
        template = self.env.ref(FAILURE_TEMPLATE_XMLID, raise_if_not_found=False)
        if not template:
            return
        try:
            template.sudo().send_mail(self.id, force_send=False)
        except Exception:
            _logger.exception(
                "odomate_hr_leave_email: could not queue the refusal answer to %s",
                self.email_from)
