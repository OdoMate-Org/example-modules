from markupsafe import Markup

from odoo import fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_date


class OdomateHrDocumentRenew(models.TransientModel):
    _name = 'odomate.hr.document.renew'
    _description = 'Renew Employee Document'

    document_id = fields.Many2one(
        'odomate.hr.document',
        string="Document",
        required=True,
        readonly=True,
        ondelete='cascade',
        default=lambda self: self.env.context.get('active_id')
        if self.env.context.get('active_model') == 'odomate.hr.document'
        else False,
    )
    new_date_issued = fields.Date(
        string="New Issue Date",
        required=True,
        default=fields.Date.context_today,
    )
    new_date_expiry = fields.Date(string="New Expiry Date", required=True)
    new_attachment_ids = fields.Many2many(
        'ir.attachment',
        'odomate_hr_document_renew_attachment_rel',
        'wizard_id',
        'attachment_id',
        string="New Scan(s)",
        required=True,
    )
    reason = fields.Char(string="Reason", required=True)

    def action_confirm(self):
        self.ensure_one()
        document = self.document_id
        if document.state not in ('valid', 'expired'):
            raise UserError(
                self.env._(
                    "Only a valid or expired document can be renewed. "
                    "%(reference)s is still a draft.",
                    reference=document.reference,
                )
            )
        if not self.new_attachment_ids:
            raise ValidationError(
                self.env._("Attach at least one scan of the renewed document.")
            )
        today = fields.Date.context_today(self)
        if self.new_date_expiry <= today:
            raise ValidationError(
                self.env._("The new expiry date must be later than today.")
            )
        if self.new_date_expiry <= self.new_date_issued:
            raise ValidationError(
                self.env._("The new expiry date must be later than the new issue date.")
            )

        old_date_expiry = document.date_expiry
        history = self.env['odomate.hr.document.history'].sudo().create({
            'document_id': document.id,
            'date_issued': document.date_issued,
            'date_expiry': old_date_expiry,
            'renewed_by': self.env.user.id,
            'renewed_date': fields.Datetime.now(),
            'reason': self.reason,
        })
        superseded = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', document._name),
            ('res_id', '=', document.id),
        ])
        if superseded:
            superseded.write({'res_model': history._name, 'res_id': history.id})

        document.write({
            'date_issued': self.new_date_issued,
            'date_expiry': self.new_date_expiry,
            'state': 'valid',
        })
        self.new_attachment_ids.sudo().write({
            'res_model': document._name,
            'res_id': document.id,
        })

        document.message_post(body=Markup("<p>%s</p>") % self.env._(
            "Renewed: expiry moved from %(old_date)s to %(new_date)s. Reason: %(reason)s",
            old_date=format_date(self.env, old_date_expiry) if old_date_expiry
            else self.env._("not set"),
            new_date=format_date(self.env, self.new_date_expiry),
            reason=self.reason,
        ))
        document._close_manager_activities(
            self.env._(
                "Document renewed; the new expiry date is %(new_date)s.",
                new_date=format_date(self.env, self.new_date_expiry),
            )
        )

        return {
            'type': 'ir.actions.act_window',
            'name': self.env._("Employee Document"),
            'res_model': 'odomate.hr.document',
            'res_id': document.id,
            'view_mode': 'form',
            'target': 'current',
        }
