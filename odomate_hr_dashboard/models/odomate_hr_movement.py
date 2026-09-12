from odoo import fields, models
from odoo.tools import SQL, drop_view_if_exists


class OdomateHrMovement(models.Model):
    _name = 'odomate.hr.movement'
    _description = 'HR Arrivals and Departures'
    _auto = False
    _order = 'date desc, id desc'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    direction = fields.Selection(
        [('join', 'Joined'), ('leave', 'Left')],
        string='Direction',
        readonly=True,
    )
    departure_reason_id = fields.Many2one(
        'hr.departure.reason', string='Departure Reason', readonly=True)

    def init(self):
        drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(SQL(
            "CREATE OR REPLACE VIEW %s AS (%s)",
            SQL.identifier(self._table),
            self._query(),
        ))

    def _query(self):
        return SQL("""
            WITH join_version AS (
                SELECT DISTINCT ON (v.employee_id)
                       v.employee_id,
                       v.department_id,
                       v.company_id,
                       v.contract_date_start AS date
                  FROM hr_version v
                 WHERE v.employee_id IS NOT NULL
                   AND v.contract_date_start IS NOT NULL
                 ORDER BY v.employee_id, v.contract_date_start ASC, v.id ASC
            ),
            leave_version AS (
                SELECT DISTINCT ON (v.employee_id)
                       v.employee_id,
                       v.department_id,
                       v.company_id,
                       v.departure_date AS date,
                       v.departure_reason_id
                  FROM hr_version v
                 WHERE v.employee_id IS NOT NULL
                   AND v.departure_date IS NOT NULL
                 ORDER BY v.employee_id, v.departure_date DESC, v.id DESC
            )
            SELECT (j.employee_id * 10 + 1) AS id,
                   j.employee_id,
                   j.department_id,
                   COALESCE(j.company_id, e.company_id) AS company_id,
                   j.date,
                   'join'::varchar AS direction,
                   NULL::integer AS departure_reason_id
              FROM join_version j
              JOIN hr_employee e ON e.id = j.employee_id
             WHERE COALESCE(j.company_id, e.company_id) IS NOT NULL
            UNION ALL
            SELECT (l.employee_id * 10 + 2) AS id,
                   l.employee_id,
                   l.department_id,
                   COALESCE(l.company_id, e.company_id) AS company_id,
                   l.date,
                   'leave'::varchar AS direction,
                   l.departure_reason_id
              FROM leave_version l
              JOIN hr_employee e ON e.id = l.employee_id
             WHERE COALESCE(l.company_id, e.company_id) IS NOT NULL
        """)
