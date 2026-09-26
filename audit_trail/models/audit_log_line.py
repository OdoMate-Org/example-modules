from odoo import fields, models


class AuditLogLine(models.Model):
    _name = 'audit.log.line'
    _description = 'Audit Field Change'
    _order = 'date desc, log_id desc, id'

    log_id = fields.Many2one('audit.log', string='Recorded Event', required=True, index=True, ondelete='cascade')
    field_id = fields.Many2one('ir.model.fields', string='Field', index=True, ondelete='set null')
    field_description = fields.Char(string='Field Label')
    old_value = fields.Text(string='Old Value')
    new_value = fields.Text(string='New Value')

    date = fields.Datetime(related='log_id.date', store=True, index=True, string='Date')
    user_id = fields.Many2one(related='log_id.user_id', store=True, index=True, string='User')
    record_name = fields.Char(related='log_id.record_name', store=True, string='Record')
    res_model = fields.Char(related='log_id.res_model', store=True, index=True, string='Kind of Record')
    res_id = fields.Integer(related='log_id.res_id', store=True, string='Record ID')
    action = fields.Selection(related='log_id.action', store=True, string='Action')
    company_id = fields.Many2one(related='log_id.company_id', store=True, index=True, string='Company')
    session_id = fields.Many2one(related='log_id.session_id', store=True, string='Working Session')
