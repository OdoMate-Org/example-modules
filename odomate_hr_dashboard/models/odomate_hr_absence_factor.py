from odoo import fields, models
from odoo.tools import SQL, drop_view_if_exists

SCOPE_HELP = (
    "Occurrences, days and the factor cover all approved, finished time off, "
    "narrowed by whatever filter you apply."
)


class OdomateHrAbsenceFactor(models.Model):
    _name = 'odomate.hr.absence.factor'
    _description = 'Absence Concentration by Employee'
    _auto = False
    _order = 'bradford_factor desc'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    occurrence_count = fields.Integer(
        string='Occurrences', readonly=True, help=SCOPE_HELP)
    day_count = fields.Float(string='Days', readonly=True, help=SCOPE_HELP)
    bradford_factor = fields.Integer(
        string='Bradford Factor',
        readonly=True,
        aggregator=None,
        help="Occurrences squared multiplied by days. " + SCOPE_HELP,
    )
    last_absence_date = fields.Date(
        string='Last Absence',
        readonly=True,
        help="End date of this employee's most recent approved, finished time off. "
             "The convenience filters select employees by this date; the figures "
             "themselves always cover all approved, finished time off.",
    )

    def init(self):
        drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(SQL(
            "CREATE OR REPLACE VIEW %s AS (%s)",
            SQL.identifier(self._table),
            self._query(),
        ))

    def _query(self):
        return SQL("""
            WITH qualifying AS (
                SELECT l.employee_id,
                       COUNT(*) AS occurrence_count,
                       COALESCE(SUM(l.number_of_days), 0.0) AS day_count,
                       MAX(l.date_to) AS last_absence_ts
                  FROM hr_leave l
                 WHERE l.employee_id IS NOT NULL
                   AND l.state = 'validate'
                   AND l.date_to <= (now() AT TIME ZONE 'UTC')
              GROUP BY l.employee_id
            )
            SELECT q.employee_id AS id,
                   q.employee_id,
                   v.department_id,
                   COALESCE(v.company_id, e.company_id) AS company_id,
                   q.occurrence_count::integer AS occurrence_count,
                   q.day_count::double precision AS day_count,
                   ROUND(q.occurrence_count * q.occurrence_count * q.day_count)::integer
                       AS bradford_factor,
                   q.last_absence_ts::date AS last_absence_date
              FROM qualifying q
              JOIN hr_employee e ON e.id = q.employee_id
              JOIN hr_version v ON v.id = e.current_version_id
             WHERE COALESCE(v.company_id, e.company_id) IS NOT NULL
        """)
