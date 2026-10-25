from odoo import api, fields, models


class AppDashboardPriorityApp(models.Model):
    _name = 'app_dashboard.priority.app'
    _description = 'My Apps Dashboard: Priority App'
    _order = 'sequence, id'
    _rec_name = 'menu_id'

    menu_id = fields.Many2one(
        'ir.ui.menu',
        string='App',
        required=True,
        ondelete='cascade',
        domain=lambda self: self._domain_menu_id(),
        help='Root app menu pinned first, for every user, on the My Apps dashboard.',
    )
    sequence = fields.Integer(default=lambda self: self._default_sequence())

    _menu_unique = models.Constraint(
        'UNIQUE(menu_id)',
        'This app is already in the priority list.',
    )

    @api.model
    def _domain_menu_id(self):
        return [('id', 'in', self.env['res.users']._get_dashboard_selectable_root_ids())]

    @api.model
    def _default_sequence(self):
        last = self.search([], order='sequence desc', limit=1)
        return (last.sequence or 0) + 10

    @api.model
    def _app_dashboard_set_demo_priority_apps(self, menu_xmlids):
        sequence = 10
        for xmlid in menu_xmlids:
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            if menu and menu._name == 'ir.ui.menu' and not menu.parent_id:
                if not self.search_count([('menu_id', '=', menu.id)]):
                    self.create({'menu_id': menu.id, 'sequence': sequence})
                sequence += 10
