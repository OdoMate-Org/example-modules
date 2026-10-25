from odoo import fields, models


class AppDashboardTile(models.Model):
    _name = 'app_dashboard.tile'
    _description = 'My Apps Dashboard: Per-User Tile State'
    _order = 'sequence, id'

    user_id = fields.Many2one('res.users', required=True, ondelete='cascade', index=True)
    menu_id = fields.Many2one('ir.ui.menu', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    is_manual = fields.Boolean(
        default=False,
        help='True once the user has dragged this tile into a custom position.',
    )
    open_count = fields.Integer(default=0)

    _user_menu_unique = models.Constraint(
        'UNIQUE(user_id, menu_id)',
        'Each app can only appear once per user.',
    )
