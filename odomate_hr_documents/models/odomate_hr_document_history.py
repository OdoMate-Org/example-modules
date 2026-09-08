from odoo import api, fields, models


class OdomateHrDocumentHistory(models.Model):
    _name = 'odomate.hr.document.history'
    _description = 'Employee Document Renewal History'
    _order = 'renewed_date desc, id desc'

    document_id = fields.Many2one(
        'odomate.hr.document',
        string="Document",
        required=True,
        ondelete='cascade',
        index=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        related='document_id.employee_id',
        store=True,
        readonly=True,
    )
    date_issued = fields.Date(string="Previous Issue Date", readonly=True)
    date_expiry = fields.Date(string="Previous Expiry Date", readonly=True)
    renewed_by = fields.Many2one('res.users', string="Renewed By", readonly=True)
    renewed_date = fields.Datetime(string="Renewed On", readonly=True)
    reason = fields.Char(string="Reason", required=True, readonly=True)
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        related='document_id.company_id',
        store=True,
        readonly=True,
        index=True,
    )
    attachment_count = fields.Integer(
        string="Superseded Scans",
        compute='_compute_attachment_count',
    )

    def _compute_attachment_count(self):
        grouped = self.env['ir.attachment'].sudo()._read_group(
            [('res_model', '=', self._name), ('res_id', 'in', self.ids)],
            groupby=['res_id'],
            aggregates=['__count'],
        )
        counts = {res_id: count for res_id, count in grouped}
        for history in self:
            history.attachment_count = counts.get(history.id, 0)

    @api.depends('document_id', 'renewed_date')
    def _compute_display_name(self):
        for history in self:
            if history.renewed_date:
                history.display_name = "%s - %s" % (
                    history.document_id.reference or '',
                    fields.Date.to_string(history.renewed_date.date()),
                )
            else:
                history.display_name = history.document_id.reference or ''
