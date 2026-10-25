from odoo import fields, models

DEFAULT_HOME_SCREEN_PARAM = 'app_dashboard.default_home_screen'


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    app_dashboard_default_home_screen = fields.Boolean(
        string='Apps Dashboard is the default home screen',
        config_parameter=DEFAULT_HOME_SCREEN_PARAM,
        help='Every user lands on the My Apps dashboard right after logging in, '
             'instead of the default menu. Each person can still switch back '
             'from their own Preferences.',
    )

    def set_values(self):
        param = self.env['ir.config_parameter'].sudo()
        was_enabled = param.get_bool(DEFAULT_HOME_SCREEN_PARAM)
        super().set_values()
        if self.app_dashboard_default_home_screen != was_enabled:
            value = 'apps_dashboard' if self.app_dashboard_default_home_screen else 'default_menu'
            self.env['res.users']._app_dashboard_apply_default_home_screen(value)

    def action_app_dashboard_manage_priority_apps(self):
        return self.env['ir.actions.act_window']._for_xml_id('app_dashboard.action_app_dashboard_priority_app')
