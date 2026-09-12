from odoo import _, api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    notice_count = fields.Integer(
        string='Notices',
        compute='_compute_notice_count',
    )

    def _get_notice_domain(self):
        self.ensure_one()
        Announcement = self.env['odomate.hr.announcement']
        return Announcement._get_notice_domain({
            'employee_ids': self.ids,
            'department_ids': self.department_id.ids,
            'job_ids': self.job_id.ids,
            'company_ids': self.company_id.ids,
        })

    @api.depends_context('uid')
    @api.depends('department_id', 'job_id', 'company_id')
    def _compute_notice_count(self):
        Announcement = self.env['odomate.hr.announcement']
        for employee in self:
            employee.notice_count = Announcement.search_count(employee._get_notice_domain())

    def action_open_notices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Notices"),
            'res_model': 'odomate.hr.announcement',
            'view_mode': 'list,form',
            'domain': self._get_notice_domain(),
        }
