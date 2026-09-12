from odoo import _, fields, models
from odoo.exceptions import UserError


class OdomateHrAnnouncementRefuse(models.TransientModel):
    _name = 'odomate.hr.announcement.refuse'
    _description = 'Refuse HR Announcement'

    announcement_id = fields.Many2one(
        comodel_name='odomate.hr.announcement',
        string='Announcement',
        required=True,
        ondelete='cascade',
    )
    reason = fields.Text(string='Refusal Reason', required=True)

    def action_confirm_refusal(self):
        self.ensure_one()
        announcement = self.announcement_id
        if announcement.state != 'to_approve':
            raise UserError(_(
                "Only an announcement waiting for approval can be refused."))
        announcement.write({
            'state': 'refused',
            'refuse_reason': self.reason,
        })
        announcement.message_post(
            body=_("Announcement refused: %s", self.reason),
        )
        return {'type': 'ir.actions.act_window_close'}
