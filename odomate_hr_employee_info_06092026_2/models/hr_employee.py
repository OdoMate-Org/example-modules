import logging

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

IDENTIFICATION_TEMPLATE = 'odomate_hr_employee_info_06092026_2.mail_template_identification_expiry'
PASSPORT_TEMPLATE = 'odomate_hr_employee_info_06092026_2.mail_template_passport_expiry'
SPOUSE_RELATIONSHIP = 'odomate_hr_employee_info_06092026_2.odomate_hr_relationship_spouse'


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    identification_expiry_date = fields.Date(
        string="Identification Expiry Date",
        groups="hr.group_hr_user",
        help="Expiry date of the identification reference recorded above.",
    )
    identification_attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='odomate_hr_employee_identification_attachment_rel',
        column1='employee_id',
        column2='attachment_id',
        string="Identification Scans",
        groups="hr.group_hr_user",
    )
    passport_attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='odomate_hr_employee_passport_attachment_rel',
        column1='employee_id',
        column2='attachment_id',
        string="Passport Scans",
        groups="hr.group_hr_user",
    )
    dependant_ids = fields.One2many(
        comodel_name='odomate.hr.dependant',
        inverse_name='employee_id',
        string="Dependants",
        groups="hr.group_hr_user",
    )
    joining_date = fields.Date(
        string="Joining Date",
        compute='_compute_joining_date',
        store=True,
        readonly=True,
        help="Earliest start date across all versions of this employee's record.",
    )

    @api.depends('version_ids.date_start', 'version_ids.date_version')
    def _compute_joining_date(self):
        for employee in self:
            dates = [
                version.date_start or version.date_version
                for version in employee.version_ids
            ]
            dates = [start for start in dates if start]
            employee.joining_date = min(dates) if dates else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.pop('joining_date', None)
        employees = super().create(vals_list)
        employees._odomate_sync_spouse_dependant()
        return employees

    def write(self, vals):
        vals.pop('joining_date', None)
        res = super().write(vals)
        if {'spouse_complete_name', 'spouse_birthdate'} & set(vals):
            self._odomate_sync_spouse_dependant()
        return res

    def _odomate_sync_spouse_dependant(self):
        """Create the missing Spouse dependant for employees carrying spouse details.

        Idempotent: an employee already holding a Spouse dependant with the same name
        is skipped. Never raises - a bookkeeping side effect must not abort the write
        that triggered it.
        """
        relationship = self.env.ref(SPOUSE_RELATIONSHIP, raise_if_not_found=False)
        if not relationship:
            return
        Dependant = self.env['odomate.hr.dependant'].sudo()
        for employee in self:
            try:
                spouse_name = employee.sudo().spouse_complete_name
                spouse_birthdate = employee.sudo().spouse_birthdate
                if not spouse_name or not spouse_birthdate:
                    continue
                already_there = Dependant.search_count([
                    ('employee_id', '=', employee.id),
                    ('relationship_id', '=', relationship.id),
                    ('name', '=ilike', spouse_name),
                ])
                if already_there:
                    continue
                Dependant.create({
                    'employee_id': employee.id,
                    'name': spouse_name,
                    'relationship_id': relationship.id,
                    'birthdate': spouse_birthdate,
                })
            except Exception:
                _logger.warning(
                    "Could not synchronise the spouse dependant of employee %s.",
                    employee.id, exc_info=True,
                )

    def _odomate_send_expiry_warning(self, template):
        sent = self.env['hr.employee']
        for employee in self:
            recipient = employee.sudo().work_email or employee.sudo().private_email
            if not recipient:
                _logger.info(
                    "Employee %s has no e-mail address, expiry warning skipped.", employee.id
                )
                continue
            template.sudo().send_mail(
                employee.id,
                force_send=False,
                email_layout_xmlid='mail.mail_notification_light',
            )
            sent |= employee
        return sent

    def _odomate_expiry_warning_notification(self, sent):
        if sent:
            message = _("Expiry warning queued for %s.", ", ".join(sent.mapped('name')))
            notification_type = 'success'
        else:
            message = _("No e-mail address on file, nothing was sent.")
            notification_type = 'warning'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': notification_type,
                'message': message,
                'sticky': False,
            },
        }

    def action_send_identification_expiry_warning(self):
        self.ensure_one()
        template = self.env.ref(IDENTIFICATION_TEMPLATE, raise_if_not_found=False)
        if not template:
            raise UserError(_("The identification expiry e-mail template is missing."))
        return self._odomate_expiry_warning_notification(
            self._odomate_send_expiry_warning(template)
        )

    def action_send_passport_expiry_warning(self):
        self.ensure_one()
        template = self.env.ref(PASSPORT_TEMPLATE, raise_if_not_found=False)
        if not template:
            raise UserError(_("The passport expiry e-mail template is missing."))
        return self._odomate_expiry_warning_notification(
            self._odomate_send_expiry_warning(template)
        )

    @api.model
    def _odomate_cron_identity_expiry_warnings(self):
        """Warn once, on the day the configured lead time is reached exactly.

        The comparison is an equality against ``today + lead time`` rather than a
        range, so an employee is warned on a single day and never again while the
        document keeps approaching its expiry date.
        """
        today = fields.Date.context_today(self)
        identification_template = self.env.ref(IDENTIFICATION_TEMPLATE, raise_if_not_found=False)
        passport_template = self.env.ref(PASSPORT_TEMPLATE, raise_if_not_found=False)
        if not identification_template and not passport_template:
            return
        for company in self.env['res.company'].sudo().search([]):
            employees = self.sudo().with_company(company).search([
                ('company_id', '=', company.id),
            ])
            if not employees:
                continue
            if identification_template and company.hr_identification_expiry_warning_days > 0:
                target = today + relativedelta(days=company.hr_identification_expiry_warning_days)
                due = employees.filtered(
                    lambda employee: employee.identification_expiry_date == target
                )
                due._odomate_send_expiry_warning(identification_template)
            if passport_template and company.hr_passport_expiry_warning_days > 0:
                target = today + relativedelta(days=company.hr_passport_expiry_warning_days)
                due = employees.filtered(
                    lambda employee: employee.passport_expiration_date == target
                )
                due._odomate_send_expiry_warning(passport_template)
