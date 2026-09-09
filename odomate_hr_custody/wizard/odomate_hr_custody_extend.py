from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_date


class OdomateHrCustodyExtend(models.TransientModel):
    _name = 'odomate.hr.custody.extend'
    _description = 'Extend Custody Return Date'

    request_id = fields.Many2one(
        comodel_name='odomate.hr.custody',
        string="Custody Request",
        required=True,
        ondelete='cascade',
        default=lambda self: self.env.context.get('active_id'),
    )
    current_return_date = fields.Date(
        string="Current Return Date",
        related='request_id.return_date',
        readonly=True,
    )
    request_date = fields.Date(
        string="Request Date",
        related='request_id.request_date',
        readonly=True,
    )
    new_return_date = fields.Date(string="New Return Date", required=True)

    def action_confirm(self):
        self.ensure_one()
        request = self.request_id
        if not request:
            raise UserError(_("There is no custody request to extend."))
        if request.state != 'approved':
            raise UserError(_(
                "Only an item currently in custody can have its return date extended."
            ))
        if self.new_return_date <= request.request_date:
            raise UserError(_(
                "The new return date must be later than the request date (%(date)s).",
                date=format_date(self.env, request.request_date),
            ))
        request.write({
            'extend_new_return_date': self.new_return_date,
            'extension_refusal_reason': False,
            'is_extension': True,
            'state': 'waiting_approval',
        })
        request.message_post(body=_(
            "Extension requested: new return date %(date)s.",
            date=format_date(self.env, self.new_return_date),
        ))
        return {'type': 'ir.actions.act_window_close'}
