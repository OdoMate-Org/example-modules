import logging
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

USAGE_WINDOW_DAYS = 30
LAUNCHPAD_ACTION_XMLID = 'odomate_launchpad.action_odomate_launchpad'


class OdomateLaunchpadUsage(models.Model):
    _name = 'odomate.launchpad.usage'
    _description = 'Launchpad App Usage'
    _order = 'used_on desc, id desc'
    _rec_name = 'menu_id'

    user_id = fields.Many2one(
        'res.users', string='User', required=True, ondelete='cascade',
        index=True, default=lambda self: self.env.user,
    )
    menu_id = fields.Many2one(
        'ir.ui.menu', string='App', required=True, ondelete='cascade',
        index=True,
    )
    used_on = fields.Datetime(
        string='Used On', required=True, default=fields.Datetime.now,
        index=True,
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
    def _visible_root_menus(self, menu_ids):
        ids = [mid for mid in (menu_ids or []) if isinstance(mid, int) and mid > 0]
        if not ids:
            return self.env['ir.ui.menu']
        return self.env['ir.ui.menu'].search([
            ('id', 'in', ids),
            ('parent_id', '=', False),
        ])._filter_visible_menus()

    @api.model
    def _usage_counts(self, menus):
        if not menus:
            return {}
        since = fields.Datetime.now() - timedelta(days=USAGE_WINDOW_DAYS)
        groups = self._read_group(
            [
                ('user_id', '=', self.env.uid),
                ('menu_id', 'in', menus.ids),
                ('used_on', '>=', since),
            ],
            ['menu_id'],
            ['__count'],
        )
        return {menu.id: count for menu, count in groups}

    @api.model
    def _is_launchpad_home(self):
        action = self.env.ref(LAUNCHPAD_ACTION_XMLID, raise_if_not_found=False)
        return bool(action) and self.env.user.sudo().action_id.id == action.id

    @api.model
    def get_launchpad_state(self, menu_ids):
        menus = self._visible_root_menus(menu_ids)
        counts = self._usage_counts(menus)
        pins = self.env['odomate.launchpad.pin'].search([
            ('user_id', '=', self.env.uid),
            ('menu_id', 'in', menus.ids),
        ])
        pinned_ids = [pin.menu_id.id for pin in pins]
        pin_rank = {menu_id: rank for rank, menu_id in enumerate(pinned_ids)}

        def sort_key(menu):
            if menu.id in pin_rank:
                return (0, pin_rank[menu.id], 0, '')
            return (1, 0, -counts.get(menu.id, 0), (menu.name or '').casefold())

        return {
            'ordered_ids': [menu.id for menu in sorted(menus, key=sort_key)],
            'pinned_ids': pinned_ids,
            'counts': {str(menu_id): count for menu_id, count in counts.items()},
            'is_home': self._is_launchpad_home(),
        }

    @api.model
    def log_open(self, menu_id):
        menu = self._visible_root_menus([menu_id])
        if not menu:
            return False
        try:
            with self.env.cr.savepoint():
                self.create({'user_id': self.env.uid, 'menu_id': menu.id})
        except Exception:
            _logger.exception("Launchpad: could not log app usage for menu %s", menu.id)
            return False
        return True

    @api.model
    def _load_demo_usage(self):
        user = self.env.ref('base.user_admin', raise_if_not_found=False)
        if not user:
            return
        plan = [
            ('project.menu_main_pm', 8, True),
            ('hr_timesheet.timesheet_menu_root', 6, True),
            ('hr.menu_hr_root', 5, False),
            ('hr_expense.menu_hr_expense_root', 3, False),
            ('hr_recruitment.menu_hr_recruitment_root', 2, False),
        ]
        now = fields.Datetime.now()
        Pin = self.env['odomate.launchpad.pin']
        vals_list = []
        pin_sequence = 1
        for xmlid, opens, pin in plan:
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            if not menu or menu._name != 'ir.ui.menu':
                continue
            vals_list += [
                {
                    'user_id': user.id,
                    'menu_id': menu.id,
                    'used_on': now - timedelta(days=(index * 29) // opens, hours=index),
                }
                for index in range(opens)
            ]
            if pin and not Pin.search_count([('user_id', '=', user.id), ('menu_id', '=', menu.id)]):
                Pin.create({'user_id': user.id, 'menu_id': menu.id, 'sequence': pin_sequence})
                pin_sequence += 1
        discuss = self.env.ref('mail.menu_root_discuss', raise_if_not_found=False)
        if pin_sequence == 1 and discuss and not Pin.search_count(
            [('user_id', '=', user.id), ('menu_id', '=', discuss.id)]
        ):
            Pin.create({'user_id': user.id, 'menu_id': discuss.id, 'sequence': pin_sequence})
        if vals_list:
            self.create(vals_list)

    @api.model
    def set_launchpad_as_home(self):
        self.check_access('create')
        action = self.env.ref(LAUNCHPAD_ACTION_XMLID)
        self.env.user.sudo().write({'action_id': action.id})
        return True

    @api.model
    def reset_launchpad_home(self):
        self.check_access('create')
        if self._is_launchpad_home():
            self.env.user.sudo().write({'action_id': False})
        return True
