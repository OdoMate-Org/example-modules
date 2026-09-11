import logging
import re
from datetime import date

from odoo import api, fields, models
from odoo.tools.mail import email_normalize, html2plaintext

_logger = logging.getLogger(__name__)

DATE_RE = re.compile(
    r'(?<![\d/-])(?:(\d{4})-(\d{1,2})-(\d{1,2})|(\d{1,2})/(\d{1,2})/(\d{4}))(?![\d/-])'
)


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        email_from = msg_dict.get('email_from') or ''
        subject = msg_dict.get('subject') or ''
        employee = self._odomate_leave_email_find_employee(email_normalize(email_from) or '')
        company = (employee.company_id or self.env.company).sudo()

        if not company.leave_email_enabled:
            try:
                with self.env.cr.savepoint():
                    return super().message_new(msg_dict, custom_values=custom_values)
            except Exception:
                _logger.exception(
                    "odomate_hr_leave_email: standard Time Off creation failed for %s", email_from)
                return self.browse()

        base_vals = {
            'received_date': fields.Datetime.now(),
            'email_from': email_from,
            'subject': subject,
            'employee_id': employee.id or False,
            'company_id': employee.company_id.id or False,
        }
        try:
            if not employee:
                return self._odomate_leave_email_refuse(
                    base_vals, 'unknown_sender', company,
                    self.env._("No employee is linked to this address."))

            dates = self._odomate_leave_email_extract_dates(msg_dict.get('body'))
            if not dates:
                return self._odomate_leave_email_refuse(
                    base_vals, 'no_date', company,
                    self.env._("No date in the format YYYY-MM-DD or DD/MM/YYYY was found "
                               "in the message."))
            date_from = dates[0]
            date_to = dates[1] if len(dates) > 1 else dates[0]
            if date_to < date_from:
                return self._odomate_leave_email_refuse(
                    base_vals, 'reversed_dates', company,
                    self.env._("The second date (%(date_to)s) comes before the first one "
                               "(%(date_from)s).", date_to=date_to, date_from=date_from))

            leave_type = company.leave_email_type_id
            if not leave_type or not leave_type.exists() or not leave_type.active:
                return self._odomate_leave_email_refuse(
                    base_vals, 'no_leave_type', company,
                    self.env._("No usable Time Off type is configured for %(company)s.",
                               company=company.name))

            values = dict(custom_values or {}, **{
                'employee_id': employee.id,
                'holiday_status_id': leave_type.id,
                'request_date_from': date_from,
                'request_date_to': date_to,
                'name': subject or self.env._("Time Off requested by email"),
            })
            with self.env.cr.savepoint():
                leave = super().message_new(msg_dict, custom_values=values)
            self.env['odomate.hr.leave.email.log'].sudo().create(dict(
                base_vals,
                state='created',
                failure_reason=False,
                leave_id=leave.id,
            ))
            return leave
        except Exception:
            _logger.exception(
                "odomate_hr_leave_email: could not turn the email from %s into a Time Off "
                "request", email_from)
            return self._odomate_leave_email_refuse(
                base_vals, 'other', company,
                self.env._("The request could not be created. The technical details are in "
                           "the server log."))

    @api.model
    def _odomate_leave_email_refuse(self, base_vals, reason, company, notes=False):
        try:
            log = self.env['odomate.hr.leave.email.log'].sudo().create(dict(
                base_vals,
                state='rejected',
                failure_reason=reason,
                notes=notes,
            ))
            log._odomate_send_failure_reply(company)
        except Exception:
            _logger.exception(
                "odomate_hr_leave_email: could not record the refused email (%s)", reason)
        return self.browse()

    @api.model
    def _odomate_leave_email_find_employee(self, email_norm):
        Employee = self.env['hr.employee'].sudo()
        if not email_norm:
            return Employee
        users = self.env['res.users'].sudo().search([
            '|', ('login', '=ilike', email_norm), ('email', '=ilike', email_norm),
        ])
        if users:
            employees = Employee.search([('user_id', 'in', users.ids)])
            if len(employees) > 1:
                employees = employees.filtered(
                    lambda e: e.company_id == e.user_id.company_id) or employees
            if employees:
                return employees[0]
        return Employee.search([
            ('work_email', '=ilike', email_norm), ('user_id', '=', False),
        ], limit=1)

    @api.model
    def _odomate_leave_email_extract_dates(self, body):
        found = []
        for match in DATE_RE.finditer(html2plaintext(body or '')):
            if match.group(1):
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            else:
                day, month, year = int(match.group(4)), int(match.group(5)), int(match.group(6))
            try:
                found.append(date(year, month, day))
            except ValueError:
                continue
            if len(found) == 2:
                break
        return found
