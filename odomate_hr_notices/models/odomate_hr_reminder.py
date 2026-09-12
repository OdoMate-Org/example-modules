from datetime import datetime, time

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

REMINDER_MODEL_WHITELIST = ('hr.employee', 'hr.version', 'hr.applicant', 'hr.leave')


class OdomateHrReminder(models.Model):
    _name = 'odomate.hr.reminder'
    _description = 'HR Date Reminder'
    _order = 'name'

    def _reminder_model_domain(self):
        available = [name for name in REMINDER_MODEL_WHITELIST if name in self.env]
        return [('model', 'in', available)]

    name = fields.Char(string='Reminder', required=True)
    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model',
        ondelete='cascade',
        domain=lambda self: self._reminder_model_domain(),
    )
    field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Date Field',
        ondelete='cascade',
        domain="[('model_id', '=', model_id), ('ttype', 'in', ['date', 'datetime'])]",
    )
    window = fields.Selection(
        selection=[
            ('today', 'Today'),
            ('days_ahead', 'Within the next N days'),
            ('period', 'Between two dates'),
        ],
        string='Time Window',
        default='days_ahead',
        required=True,
    )
    days_ahead = fields.Integer(string='Days Ahead', default=30)
    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    active = fields.Boolean(string='Active', default=True)
    preview_count = fields.Integer(
        string='Matching Records',
        compute='_compute_preview_count',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )

    _check_days_ahead = models.Constraint(
        'CHECK(days_ahead >= 0)',
        "The number of days ahead cannot be negative.",
    )
    _check_period = models.Constraint(
        'CHECK(date_from IS NULL OR date_to IS NULL OR date_from <= date_to)',
        "The period start date must be on or before the period end date.",
    )

    @api.onchange('model_id')
    def _onchange_model_id(self):
        if self.field_id.model_id != self.model_id:
            self.field_id = False

    def _get_match_domain(self):
        """Build the reminder's domain from validated parts only."""
        self.ensure_one()
        if not self.model_id or not self.field_id:
            return None
        if self.field_id.model_id != self.model_id or self.field_id.ttype not in ('date', 'datetime'):
            return None
        if self.model_id.model not in REMINDER_MODEL_WHITELIST:
            return None

        today = fields.Date.context_today(self)
        if self.window == 'today':
            date_from = date_to = today
        elif self.window == 'days_ahead':
            date_from = today
            date_to = today + relativedelta(days=max(self.days_ahead, 0))
        else:
            date_from = self.date_from
            date_to = self.date_to
            if not date_from or not date_to:
                return None

        field_name = self.field_id.name
        if self.field_id.ttype == 'datetime':
            lower = fields.Datetime.to_string(datetime.combine(date_from, time.min))
            upper = fields.Datetime.to_string(datetime.combine(date_to, time.max))
        else:
            lower = fields.Date.to_string(date_from)
            upper = fields.Date.to_string(date_to)
        return [(field_name, '>=', lower), (field_name, '<=', upper)]

    def _get_match_count(self):
        self.ensure_one()
        try:
            domain = self._get_match_domain()
            if domain is None or self.model_id.model not in self.env:
                return 0
            return self.env[self.model_id.model].search_count(domain)
        except (AccessError, ValueError):
            return 0

    @api.depends_context('uid', 'company')
    @api.depends('model_id', 'field_id', 'window', 'days_ahead', 'date_from', 'date_to')
    def _compute_preview_count(self):
        for reminder in self:
            reminder.preview_count = reminder._get_match_count()

    def action_open_matching_records(self):
        self.ensure_one()
        domain = self._get_match_domain()
        if domain is None:
            raise UserError(_(
                "Choose a model, a date field and a complete time window "
                "before opening the matching records."))
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': self.model_id.model,
            'view_mode': 'list,form',
            'domain': domain,
        }
