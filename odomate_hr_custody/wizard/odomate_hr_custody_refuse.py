from odoo import _, fields, models
from odoo.exceptions import UserError


class OdomateHrCustodyRefuse(models.TransientModel):
    _name = 'odomate.hr.custody.refuse'
    _description = 'Refuse Custody Request'

    request_id = fields.Many2one(
        comodel_name='odomate.hr.custody',
        string="Custody Request",
        required=True,
        ondelete='cascade',
        default=lambda self: self.env.context.get('active_id'),
    )
    is_extension = fields.Boolean(
        string="Refusing an Extension",
        related='request_id.is_extension',
        readonly=True,
    )
    reason = fields.Text(string="Reason", required=True)

    def action_confirm(self):
        self.ensure_one()
        request = self.request_id
        if not request:
            raise UserError(_("There is no custody request to refuse."))
        request._check_custody_officer_rights()
        if request.state != 'waiting_approval':
            raise UserError(_("Only a request waiting for approval can be refused."))
        if request.is_extension:
            request._check_no_other_holder()
            request.write({
                'extension_refusal_reason': self.reason,
                'extend_new_return_date': False,
                'is_extension': False,
                'state': 'approved',
            })
            request.message_post(body=_(
                "Extension refused: %(reason)s The original return date stands.",
                reason=self.reason,
            ))
        else:
            request.write({
                'refusal_reason': self.reason,
                'state': 'refused',
            })
            request.message_post(body=_("Request refused: %(reason)s", reason=self.reason))
        return {'type': 'ir.actions.act_window_close'}
