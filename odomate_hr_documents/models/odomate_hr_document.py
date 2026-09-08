import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_date

_logger = logging.getLogger(__name__)

REMINDER_ACTIVITY_XMLID = 'mail.mail_activity_data_todo'
REMINDER_TEMPLATE_XMLID = 'odomate_hr_documents.mail_template_document_reminder'
NUMERIC_SEARCH_OPERATORS = ('=', '!=', '<', '<=', '>', '>=')


class OdomateHrDocument(models.Model):
    _name = 'odomate.hr.document'
    _description = 'Employee Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference'
    _order = 'date_expiry asc, id desc'

    reference = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: self.env._("New"),
        index=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    document_type_id = fields.Many2one(
        'odomate.hr.document.type',
        string="Document Type",
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
    )
    description = fields.Text(string="Description")
    date_issued = fields.Date(string="Issue Date", tracking=True)
    date_expiry = fields.Date(string="Expiry Date", index=True, tracking=True)
    state = fields.Selection(
        [
            ('draft', "Draft"),
            ('valid', "Valid"),
            ('expired', "Expired"),
        ],
        string="Status",
        default='draft',
        required=True,
        copy=False,
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        related='employee_id.company_id',
        store=True,
        readonly=True,
        index=True,
    )
    days_remaining_label = fields.Char(
        string="Days Remaining",
        compute='_compute_days_remaining_label',
        search='_search_days_remaining_label',
    )
    last_reminder_sent_date = fields.Date(
        string="Last Reminder Sent",
        copy=False,
        groups='base.group_no_one',
    )
    history_ids = fields.One2many(
        'odomate.hr.document.history',
        'document_id',
        string="Renewal History",
    )
    history_count = fields.Integer(
        string="Renewals",
        compute='_compute_history_count',
    )

    @api.depends('history_ids')
    def _compute_history_count(self):
        for document in self:
            document.history_count = len(document.history_ids)

    @api.depends('date_expiry', 'state')
    def _compute_days_remaining_label(self):
        today = fields.Date.context_today(self)
        for document in self:
            if not document.date_expiry:
                document.days_remaining_label = False
                continue
            delta = (document.date_expiry - today).days
            if delta < 0:
                document.days_remaining_label = self.env._(
                    "Expired %(days)s days", days=-delta
                )
            elif delta == 0:
                document.days_remaining_label = self.env._("Today")
            elif delta == 1:
                document.days_remaining_label = self.env._("Tomorrow")
            else:
                document.days_remaining_label = str(delta)

    def _search_days_remaining_label(self, operator, value):
        if operator not in NUMERIC_SEARCH_OPERATORS:
            return NotImplemented
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return NotImplemented
        target = fields.Date.context_today(self) + relativedelta(days=int(value))
        return [('date_expiry', operator, target)]

    def init(self):
        self.env.cr.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS odomate_hr_document_valid_uniq
                ON odomate_hr_document (employee_id, document_type_id)
             WHERE state = 'valid'
            """
        )

    def _raise_duplicate_valid(self, employee_id, document_type_id):
        employee = self.env['hr.employee'].sudo().browse(employee_id)
        document_type = self.env['odomate.hr.document.type'].sudo().browse(
            document_type_id)
        raise ValidationError(
            self.env._(
                "%(employee)s already holds a valid %(document_type)s. "
                "Renew the existing document instead of adding a second one.",
                employee=employee.name,
                document_type=document_type.name,
            )
        )

    def _check_no_valid_sibling(self, employee_id, document_type_id, exclude_ids=()):
        if not employee_id or not document_type_id:
            return
        domain = [
            ('employee_id', '=', employee_id),
            ('document_type_id', '=', document_type_id),
            ('state', '=', 'valid'),
        ]
        if exclude_ids:
            domain.append(('id', 'not in', list(exclude_ids)))
        if self.env['odomate.hr.document'].sudo().search_count(domain, limit=1):
            self._raise_duplicate_valid(employee_id, document_type_id)

    @api.constrains('employee_id', 'document_type_id', 'state')
    def _check_single_valid_document(self):
        for document in self:
            if document.state != 'valid':
                continue
            document._check_no_valid_sibling(
                document.employee_id.id,
                document.document_type_id.id,
                exclude_ids=document.ids,
            )

    @api.model_create_multi
    def create(self, vals_list):
        pending = set()
        for vals in vals_list:
            if not vals.get('reference') or vals['reference'] == self.env._("New"):
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'odomate.hr.document'
                ) or self.env._("New")
            if vals.get('state') != 'valid':
                continue
            pair = (vals.get('employee_id'), vals.get('document_type_id'))
            if not all(pair):
                continue
            if pair in pending:
                self._raise_duplicate_valid(*pair)
            pending.add(pair)
            self._check_no_valid_sibling(*pair)
        return super().create(vals_list)

    def write(self, vals):
        if {'state', 'employee_id', 'document_type_id'} & vals.keys():
            pending = set()
            for document in self:
                if (vals.get('state') or document.state) != 'valid':
                    continue
                pair = (
                    vals.get('employee_id', document.employee_id.id),
                    vals.get('document_type_id', document.document_type_id.id),
                )
                if not all(pair):
                    continue
                if pair in pending:
                    self._raise_duplicate_valid(*pair)
                pending.add(pair)
                document._check_no_valid_sibling(*pair, exclude_ids=self.ids)
        return super().write(vals)

    def action_mark_valid(self):
        today = fields.Date.context_today(self)
        for document in self:
            if document.state == 'valid':
                continue
            if document.date_expiry and document.date_expiry < today:
                raise ValidationError(
                    self.env._(
                        "%(reference)s expired on %(date)s and cannot be marked valid. "
                        "Use Renew to record a new issue and expiry date.",
                        reference=document.reference,
                        date=format_date(self.env, document.date_expiry),
                    )
                )
            document.state = 'valid'
        return True

    def action_set_to_draft(self):
        for document in self:
            if document.state == 'draft':
                continue
            document.state = 'draft'
            document._close_manager_activities(
                self.env._(
                    "Document set back to draft: the expiry date this to-do chased "
                    "no longer applies."
                )
            )
        return True

    def action_open_renew_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._("Renew Document"),
            'res_model': 'odomate.hr.document.renew',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_document_id': self.id},
        }

    def action_view_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._("Renewal History"),
            'res_model': 'odomate.hr.document.history',
            'view_mode': 'list,form',
            'domain': [('document_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_send_reminder_now(self):
        for document in self:
            if document.state == 'draft':
                raise UserError(
                    self.env._(
                        "%(reference)s is still a draft, so it is not chased. "
                        "Mark it valid first.",
                        reference=document.reference,
                    )
                )
        self._send_reminders(fields.Date.context_today(self), force=True)
        return True

    def _is_reminder_due(self, today):
        self.ensure_one()
        if self.state not in ('valid', 'expired') or not self.date_expiry:
            return False
        document_type = self.document_type_id
        if not document_type:
            return False
        reminder_days = max(document_type.reminder_days or 0, 0)
        delta = (self.date_expiry - today).days
        pattern = document_type.chasing_pattern
        if pattern == 'on_expiry':
            return delta == 0
        if pattern == 'before_expiry':
            return delta == reminder_days
        if pattern == 'daily_before':
            return 0 <= delta <= reminder_days
        if pattern == 'daily_after':
            return -reminder_days <= delta <= 0
        return False

    @api.model
    def _cron_process_documents(self):
        today = fields.Date.context_today(self)
        documents = self.sudo().search([
            ('state', 'in', ('valid', 'expired')),
            ('date_expiry', '!=', False),
        ])
        to_expire = documents.filtered(
            lambda document: document.state == 'valid' and document.date_expiry < today
        )
        if to_expire:
            to_expire.write({'state': 'expired'})
            # Persist the expiry before the fallible notification phase so a
            # reminder failure can never roll the state transition back.
            self.env.cr.flush()
        due = documents.filtered(lambda document: document._is_reminder_due(today))
        due._send_reminders(today)
        return True

    def _send_reminders(self, today, force=False):
        template = self.env.ref(REMINDER_TEMPLATE_XMLID, raise_if_not_found=False)
        for document in self:
            document_sudo = document.sudo()
            if not force and document_sudo.last_reminder_sent_date == today:
                continue
            # Isolate each document in its own savepoint: a rendering or
            # activity failure on one document must not abort the whole run
            # (and, in the cron, must not roll back the expiry writes above).
            try:
                with self.env.cr.savepoint():
                    if template and document_sudo._get_reminder_recipient_email():
                        template.sudo().send_mail(document.id, force_send=False)
                    document_sudo._sync_manager_activity()
                    document_sudo.last_reminder_sent_date = today
            except Exception:
                _logger.exception(
                    "Failed to send expiry reminder for document %s",
                    document_sudo.reference or document.id,
                )
        return True

    def _get_reminder_recipient_email(self):
        self.ensure_one()
        employee = self.employee_id
        return employee.work_email or employee.private_email or ''

    def _sync_manager_activity(self):
        self.ensure_one()
        manager_user = self.employee_id.parent_id.user_id
        if not manager_user:
            return False
        activity_type = self.env.ref(REMINDER_ACTIVITY_XMLID, raise_if_not_found=False)
        summary = self.env._(
            "Renew %(document_type)s for %(employee)s (%(reference)s)",
            document_type=self.document_type_id.name,
            employee=self.employee_id.name,
            reference=self.reference,
        )
        existing = self.activity_ids.filtered(
            lambda activity: activity.user_id == manager_user
            and (not activity_type or activity.activity_type_id == activity_type)
        )
        if existing:
            existing.write({
                'date_deadline': self.date_expiry,
                'summary': summary,
            })
        else:
            self.activity_schedule(
                REMINDER_ACTIVITY_XMLID,
                date_deadline=self.date_expiry,
                summary=summary,
                user_id=manager_user.id,
            )
        return True

    def _close_manager_activities(self, feedback):
        for document in self:
            document.sudo().activity_feedback(
                [REMINDER_ACTIVITY_XMLID], feedback=feedback
            )

    @api.model
    def _generate_demo_documents(self):
        if self.search_count([], limit=1):
            return False
        employees = self.env['hr.employee'].sudo().search([], order='id')
        if not employees:
            return False

        def holder(index):
            return employees[index % len(employees)]

        today = fields.Date.context_today(self)
        module = 'odomate_hr_documents.'
        work_permit = self.env.ref(module + 'demo_document_type_work_permit')
        first_aid = self.env.ref(module + 'demo_document_type_first_aid')
        driving_licence = self.env.ref(module + 'demo_document_type_driving_licence')
        forklift = self.env.ref(module + 'demo_document_type_forklift')
        residence_permit = self.env.ref(module + 'demo_document_type_residence_permit')
        professional_licence = self.env.ref(module + 'demo_document_type_professional_licence')

        documents = self.sudo().create([
            {
                'employee_id': holder(0).id,
                'document_type_id': work_permit.id,
                'description': "Category B work permit issued by the regional labour office.",
                'date_issued': today - relativedelta(years=2),
                'date_expiry': today + relativedelta(days=work_permit.reminder_days),
                'state': 'valid',
            },
            {
                'employee_id': holder(1).id,
                'document_type_id': first_aid.id,
                'description': "Two-day workplace first-aid course, valid three years.",
                'date_issued': today - relativedelta(years=3),
                'date_expiry': today - relativedelta(days=20),
                'state': 'valid',
            },
            {
                'employee_id': holder(2).id,
                'document_type_id': driving_licence.id,
                'description': "Categories B and BE. Renewed once already.",
                'date_issued': today - relativedelta(days=40),
                'date_expiry': today + relativedelta(years=8),
                'state': 'valid',
            },
            {
                'employee_id': holder(3).id,
                'document_type_id': forklift.id,
                'description': "Awaiting the signed copy from the training provider.",
                'date_issued': today - relativedelta(years=1),
                'date_expiry': today + relativedelta(days=10),
                'state': 'draft',
            },
            {
                'employee_id': holder(4).id,
                'document_type_id': residence_permit.id,
                'description': "Temporary residence permit, renewable at the town hall.",
                'date_issued': today - relativedelta(years=1),
                'date_expiry': today,
                'state': 'valid',
            },
            {
                'employee_id': holder(5).id,
                'document_type_id': professional_licence.id,
                'description': "Chartered practice licence; the renewal fee is due yearly.",
                'date_issued': today - relativedelta(years=4),
                'date_expiry': today - relativedelta(days=90),
                'state': 'expired',
            },
        ])

        renewed = documents[2]
        history = self.env['odomate.hr.document.history'].sudo().create({
            'document_id': renewed.id,
            'date_issued': today - relativedelta(years=10),
            'date_expiry': today - relativedelta(days=40),
            'renewed_by': self.env.user.id,
            'renewed_date': fields.Datetime.now() - relativedelta(days=40),
            'reason': "Ten-year licence replaced at the driving licence agency.",
        })
        self.env['ir.attachment'].sudo().create([
            {
                'name': 'driving_licence_previous.txt',
                'mimetype': 'text/plain',
                'raw': b'Superseded driving licence scan (demo placeholder).',
                'res_model': history._name,
                'res_id': history.id,
            },
            {
                'name': 'driving_licence_current.txt',
                'mimetype': 'text/plain',
                'raw': b'Current driving licence scan (demo placeholder).',
                'res_model': renewed._name,
                'res_id': renewed.id,
            },
        ])

        for xmlid, filename, body in (
            ('demo_form_template_expense_claim', 'expense_claim_form.txt',
             b'Expense claim form (demo placeholder).'),
            ('demo_form_template_address_change', 'change_of_address.txt',
             b'Change of address notification (demo placeholder).'),
            ('demo_form_template_equipment_loan', 'equipment_loan_agreement.txt',
             b'Equipment loan agreement (demo placeholder).'),
        ):
            template = self.env.ref(module + xmlid, raise_if_not_found=False)
            if template:
                self.env['ir.attachment'].sudo().create({
                    'name': filename,
                    'mimetype': 'text/plain',
                    'raw': body,
                    'res_model': template._name,
                    'res_id': template.id,
                })
        return True
