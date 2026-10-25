from psycopg2 import IntegrityError

from odoo import Command, api, fields, models
from odoo.tools.translate import _

DASHBOARD_ACTION_XMLID = 'app_dashboard.action_apps_dashboard'
DASHBOARD_MENU_XMLID = 'app_dashboard.menu_apps_dashboard_root'
DEFAULT_HOME_SCREEN_PARAM = 'app_dashboard.default_home_screen'
DEFAULT_TILE_SIZE_PARAM = 'app_dashboard.default_tile_size'
TILE_SIZES = ('small', 'medium', 'large')
LAYOUTS = ('grid', 'columns')


class ResUsers(models.Model):
    _inherit = 'res.users'

    favorite_app_menu_ids = fields.Many2many(
        'ir.ui.menu',
        'app_dashboard_favorite_menu_rel',
        'user_id',
        'menu_id',
        string='Favorite Apps',
        domain=[('parent_id', '=', False)],
        copy=False,
        user_writeable=True,
        help='Apps pinned at the top of the My Apps dashboard.',
    )
    home_screen_mode = fields.Selection(
        [
            ('default_menu', 'Default Menu'),
            ('apps_dashboard', 'Apps Dashboard'),
        ],
        string='Home Screen',
        default=lambda self: self._default_home_screen_mode(),
        required=True,
        inverse='_inverse_home_screen_mode',
        user_writeable=True,
        help='Screen opened right after login: the standard Odoo menu, or the My Apps dashboard. '
             'Defaults to whatever an administrator configured in Settings.',
    )
    dashboard_tile_size = fields.Selection(
        [('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')],
        string='Dashboard Tile Size',
        default=lambda self: self._default_dashboard_tile_size(),
        required=True,
        user_writeable=True,
        help='Size of the tiles on your My Apps dashboard. '
             'Defaults to whatever an administrator configured in Settings.',
    )
    dashboard_layout = fields.Selection(
        [('grid', 'Grid'), ('columns', 'Columns')],
        string='Dashboard Layout',
        default='grid',
        required=True,
        user_writeable=True,
        help='Grid groups apps into Favorites and All Apps, sorted automatically. '
             'Columns lets you arrange apps into your own kanban-style columns.',
    )

    @api.model
    def _default_home_screen_mode(self):
        enabled = self.env['ir.config_parameter'].sudo().get_bool(DEFAULT_HOME_SCREEN_PARAM)
        return 'apps_dashboard' if enabled else 'default_menu'

    @api.model
    def _default_dashboard_tile_size(self):
        size = self.env['ir.config_parameter'].sudo().get_str(DEFAULT_TILE_SIZE_PARAM)
        return size if size in TILE_SIZES else 'medium'

    @property
    def SELF_WRITEABLE_FIELDS(self):
        parent = getattr(super(), 'SELF_WRITEABLE_FIELDS', [])
        return list(parent) + [
            'favorite_app_menu_ids', 'home_screen_mode', 'dashboard_tile_size', 'dashboard_layout',
        ]

    def _inverse_home_screen_mode(self):
        dashboard_action = self.env.ref(DASHBOARD_ACTION_XMLID, raise_if_not_found=False)
        for user in self:
            if user.share:
                # portal/public users never get the internal-only dashboard as home action
                if dashboard_action and user.action_id.id == dashboard_action.id:
                    user.sudo().action_id = False
                continue
            if user.home_screen_mode == 'apps_dashboard' and dashboard_action:
                if user.action_id.id != dashboard_action.id:
                    user.sudo().action_id = dashboard_action.id
            elif user.home_screen_mode == 'default_menu' and dashboard_action and user.action_id.id == dashboard_action.id:
                # only undo our own home action: an administrator-assigned one is kept
                user.sudo().action_id = False

    @api.model
    def _get_dashboard_eligible_apps(self):
        Menu = self.env['ir.ui.menu']
        if not Menu.has_access('read'):
            return Menu
        # get_user_roots() returns plain ids on recent releases, a recordset on older ones
        roots = Menu.get_user_roots()
        roots = roots if isinstance(roots, models.BaseModel) else Menu.browse(roots)
        own_menu = self.env.ref(DASHBOARD_MENU_XMLID, raise_if_not_found=False)
        return roots - own_menu if own_menu else roots

    @api.model
    def _get_dashboard_selectable_root_ids(self):
        """Root apps that can appear on a dashboard outside debug mode (used to pin priority apps)."""
        Menu = self.env['ir.ui.menu']
        root_ids = self._get_dashboard_eligible_apps().ids
        try:
            visible_ids = Menu._visible_menu_ids(False)
        except (AttributeError, TypeError):
            return root_ids
        return [menu_id for menu_id in root_ids if menu_id in visible_ids]

    @api.model
    def _app_dashboard_apply_default_home_screen(self, value):
        """Bulk-apply an admin-configured default to every active internal user (Settings action)."""
        for user in self.sudo().search([('active', '=', True), ('share', '=', False)]):
            if user.home_screen_mode != value:
                user.home_screen_mode = value

    @api.model
    def get_app_dashboard_data(self):
        apps = self._get_dashboard_eligible_apps()
        favorites = self.env.user.sudo().favorite_app_menu_ids & apps
        others = apps - favorites

        priority_ids = [
            menu_id for menu_id in self.env['app_dashboard.priority.app'].sudo().search([]).menu_id.ids
            if menu_id in others.ids
        ]
        tiles = self.env['app_dashboard.tile'].sudo().search([
            ('user_id', '=', self.env.uid), ('menu_id', 'in', others.ids),
        ])
        tiles_by_menu = {tile.menu_id.id: tile for tile in tiles}
        manual_order = {
            menu_id: tile.sequence for menu_id, tile in tiles_by_menu.items() if tile.is_manual
        }

        def sort_key(app):
            if app.id in manual_order:
                return (0, manual_order[app.id], 0)
            if app.id in priority_ids:
                return (1, priority_ids.index(app.id), 0)
            open_count = tiles_by_menu[app.id].open_count if app.id in tiles_by_menu else 0
            return (2, -open_count, app.sequence)

        ordered_others = others.sorted(key=sort_key)
        ordered_apps = favorites + ordered_others
        return {
            'apps': [
                {
                    'id': app.id,
                    'name': app.name,
                    'sequence': app.sequence,
                    'is_favorite': app in favorites,
                    'is_priority': app.id in priority_ids and app.id not in manual_order,
                }
                for app in ordered_apps
            ],
            'favorite_ids': favorites.ids,
            'has_manual_order': bool(manual_order),
        }

    @api.model
    def register_app_open(self, menu_id):
        menu_id = int(menu_id)
        if menu_id not in self._get_dashboard_eligible_apps().ids:
            return False
        Tile = self.env['app_dashboard.tile']
        tile = Tile.search([('user_id', '=', self.env.uid), ('menu_id', '=', menu_id)], limit=1)
        try:
            with self.env.cr.savepoint():
                if tile:
                    tile.open_count += 1
                else:
                    Tile.create({'user_id': self.env.uid, 'menu_id': menu_id, 'open_count': 1})
        except IntegrityError:
            tile = Tile.search([('user_id', '=', self.env.uid), ('menu_id', '=', menu_id)], limit=1)
            if tile:
                tile.open_count += 1
        return True

    @api.model
    def reorder_apps(self, ordered_menu_ids):
        eligible_ids = set(self._get_dashboard_eligible_apps().ids)
        Tile = self.env['app_dashboard.tile']
        sequence = 10
        for menu_id in ordered_menu_ids:
            menu_id = int(menu_id)
            if menu_id not in eligible_ids:
                continue
            tile = Tile.search([('user_id', '=', self.env.uid), ('menu_id', '=', menu_id)], limit=1)
            if tile:
                tile.write({'sequence': sequence, 'is_manual': True})
            else:
                Tile.create({
                    'user_id': self.env.uid,
                    'menu_id': menu_id,
                    'sequence': sequence,
                    'is_manual': True,
                })
            sequence += 10
        return True

    @api.model
    def toggle_app_favorite(self, menu_id):
        menu = self.env['ir.ui.menu'].browse(int(menu_id))
        if menu not in self._get_dashboard_eligible_apps():
            return False
        user = self.env.user.sudo()
        if menu in user.favorite_app_menu_ids:
            user.favorite_app_menu_ids = [Command.unlink(menu.id)]
            return False
        user.favorite_app_menu_ids = [Command.link(menu.id)]
        return True

    @api.model
    def _app_dashboard_set_demo_favorites(self, user_xmlid, menu_xmlids):
        user = self.env.ref(user_xmlid, raise_if_not_found=False)
        if not user:
            return
        menus = self.env['ir.ui.menu']
        for xmlid in menu_xmlids:
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            if menu and menu._name == 'ir.ui.menu' and not menu.parent_id:
                menus |= menu
        if menus:
            user.favorite_app_menu_ids = [Command.link(menu.id) for menu in menus]
