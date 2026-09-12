from datetime import datetime, time

from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class OdomateHrDashboard(models.AbstractModel):
    _name = 'odomate.hr.dashboard'
    _description = 'HR Overview'
    _auto = False

    def _pending_sources(self):
        return [
            ('odomate.hr.loan', _("Loans to approve"),
             [('state', '=', 'submitted')]),
            ('odomate.hr.salary.advance', _("Salary advances to approve"),
             [('state', '=', 'submitted')]),
            ('odomate.hr.resignation', _("Resignations to approve"),
             [('state', 'in', ('confirmed', 'manager_approved'))]),
            ('odomate.hr.transfer', _("Transfers to approve"),
             [('state', '=', 'to_approve')]),
            ('odomate.hr.announcement', _("Announcements to approve"),
             [('state', '=', 'to_approve')]),
        ]

    def _act_window(self, name, res_model, domain, view_mode, context=None):
        views = [[False, mode] for mode in view_mode.split(',')]
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': res_model,
            'views': views,
            'view_mode': view_mode,
            'domain': domain,
            'context': context or {},
            'target': 'current',
        }

    def _movements(self):
        return self.env['odomate.hr.movement'].with_context(active_test=False)

    def _headcount_at(self, day, company_ids):
        movements = self._movements()
        joined = movements.search_count([
            ('direction', '=', 'join'),
            ('date', '<=', day),
            ('company_id', 'in', company_ids),
        ])
        left = movements.search_count([
            ('direction', '=', 'leave'),
            ('date', '<=', day),
            ('company_id', 'in', company_ids),
        ])
        return joined - left

    def _coerce_period(self, date_from, date_to):
        today = fields.Date.context_today(self)
        date_from = fields.Date.to_date(date_from) or today.replace(month=1, day=1)
        date_to = fields.Date.to_date(date_to) or today.replace(month=12, day=31)
        if date_to < date_from:
            date_from, date_to = date_to, date_from
        return date_from, date_to

    @api.model
    def get_overview(self, date_from, date_to):
        if not self.env.user.has_group('hr.group_hr_user'):
            raise AccessError(
                _("The HR Overview is available to HR officers and HR managers only."))

        date_from, date_to = self._coerce_period(date_from, date_to)
        today = fields.Date.context_today(self)
        company_ids = self.env.companies.ids

        day_start = fields.Datetime.to_string(datetime.combine(today, time.min))
        day_end = fields.Datetime.to_string(datetime.combine(today, time.max))
        period_from = fields.Date.to_string(date_from)
        period_to = fields.Date.to_string(date_to)

        headcount_domain = [('company_id', 'in', company_ids)]
        joined_domain = [
            ('direction', '=', 'join'),
            ('date', '>=', period_from),
            ('date', '<=', period_to),
            ('company_id', 'in', company_ids),
        ]
        left_domain = [
            ('direction', '=', 'leave'),
            ('date', '>=', period_from),
            ('date', '<=', period_to),
            ('company_id', 'in', company_ids),
        ]
        off_today_domain = [
            ('state', '=', 'validate'),
            ('date_from', '<=', day_end),
            ('date_to', '>=', day_start),
            ('company_id', 'in', company_ids),
        ]

        movements = self._movements()
        headcount = self.env['hr.employee'].search_count(headcount_domain)
        joined = movements.search_count(joined_domain)
        left = movements.search_count(left_domain)
        off_today = self.env['hr.leave'].search_count(off_today_domain)

        headcount_from = self._headcount_at(period_from, company_ids)
        headcount_to = self._headcount_at(period_to, company_ids)
        average_headcount = (headcount_from + headcount_to) / 2.0
        turnover_rate = round(left / average_headcount * 100, 1) if average_headcount else 0.0

        turnover_definition = _(
            "Turnover = departures in the selected period divided by average headcount "
            "over the period, where average headcount = (headcount on the first day of "
            "the period + headcount on the last day of the period) / 2."
        )
        if average_headcount:
            turnover_detail = _(
                "%(left)s departures / average headcount %(average)s "
                "(%(headcount_from)s on %(date_from)s, %(headcount_to)s on %(date_to)s) "
                "= %(rate)s%%",
                left=left,
                average=average_headcount,
                headcount_from=headcount_from,
                headcount_to=headcount_to,
                date_from=period_from,
                date_to=period_to,
                rate=turnover_rate,
            )
        else:
            turnover_detail = _(
                "%(left)s departures / average headcount 0 "
                "(%(headcount_from)s on %(date_from)s, %(headcount_to)s on %(date_to)s) "
                "- turnover cannot be computed without headcount",
                left=left,
                headcount_from=headcount_from,
                headcount_to=headcount_to,
                date_from=period_from,
                date_to=period_to,
            )

        movement_context = {'active_test': False}
        actions = {
            'headcount': self._act_window(
                _("Headcount"), 'hr.employee', headcount_domain, 'list,kanban,form'),
            'joined': self._act_window(
                _("Joined"), 'odomate.hr.movement', joined_domain,
                'list,graph,pivot', dict(movement_context)),
            'left': self._act_window(
                _("Left"), 'odomate.hr.movement', left_domain,
                'list,graph,pivot', dict(movement_context)),
            'turnover': self._act_window(
                _("Departures behind the turnover rate"), 'odomate.hr.movement',
                left_domain, 'list,graph,pivot', dict(movement_context)),
            'off_today': self._act_window(
                _("Off today"), 'hr.leave', off_today_domain, 'list,form'),
        }

        pending = []
        for model_name, label, domain in self._pending_sources():
            if model_name not in self.env:
                continue
            Model = self.env[model_name]
            if not Model.has_access('read'):
                continue
            count = Model.search_count(domain)
            if not count:
                continue
            pending.append({
                'model': model_name,
                'label': label,
                'count': count,
                'action': self._act_window(label, model_name, domain, 'list,form'),
            })

        return {
            'headcount': headcount,
            'joined': joined,
            'left': left,
            'off_today': off_today,
            'turnover_rate': turnover_rate,
            'turnover_definition': turnover_definition,
            'turnover_detail': turnover_detail,
            'actions': actions,
            'pending': pending,
        }
