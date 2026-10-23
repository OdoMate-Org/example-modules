from psycopg2 import IntegrityError

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OdomateLaunchpadPin(models.Model):
    _name = 'odomate.launchpad.pin'
    _description = 'Launchpad Pinned App'
    _order = 'sequence, id'
    _rec_name = 'menu_id'

    user_id = fields.Many2one(
        'res.users', string='User', required=True, ondelete='cascade',
        index=True, default=lambda self: self.env.user,
    )
    menu_id = fields.Many2one(
        'ir.ui.menu', string='App', required=True, ondelete='cascade',
    )
    sequence = fields.Integer(string='Sequence', default=10)

    _user_menu_uniq = models.Constraint(
        'UNIQUE(user_id, menu_id)',
        'This app is already pinned for this user.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        # Records are strictly personal: outside superuser context they always
        # belong to the current user, so the own-records access rule never
        # rejects a create for carrying another user's id.
        if not self.env.su:
            for vals in vals_list:
                vals['user_id'] = self.env.uid
        return super().create(vals_list)

    @api.model
    def toggle_pin(self, menu_id):
        uid = self.env.uid
        existing = self.search([('user_id', '=', uid), ('menu_id', '=', menu_id)], limit=1)
        if existing:
            existing.unlink()
            return False
        menu = self.env['odomate.launchpad.usage']._visible_root_menus([menu_id])
        if not menu:
            raise UserError(_("This app is not available to you."))
        last = self.search([('user_id', '=', uid)], order='sequence desc, id desc', limit=1)
        try:
            with self.env.cr.savepoint():
                self.create({
                    'user_id': uid,
                    'menu_id': menu.id,
                    'sequence': last.sequence + 1 if last else 10,
                })
        except IntegrityError:
            pass
        return True
