import logging

from odoo import SUPERUSER_ID, api, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        for user in users:
            try:
                user._odomate_auto_create_employee()
            except Exception:
                _logger.warning(
                    "Could not create the employee record of user %s.", user.id, exc_info=True
                )
        return users

    def _odomate_auto_create_employee(self):
        """Create the matching ``hr.employee`` for a brand new internal login.

        The company switch is read at login-creation time, so turning it off takes
        effect on the very next login. Existing logins are never backfilled, and no
        employee is ever created from a portal, public or technical account.
        """
        self.ensure_one()
        if self.id == SUPERUSER_ID or self.share or not self.active:
            return self.env['hr.employee']
        company = self.company_id
        if not company or not company.hr_auto_create_employee:
            return self.env['hr.employee']
        Employee = self.env['hr.employee'].sudo()
        if Employee.with_context(active_test=False).search_count([('user_id', '=', self.id)], limit=1):
            return self.env['hr.employee']
        return Employee.with_company(company).create({
            'name': self.name or self.login,
            'user_id': self.id,
        })
