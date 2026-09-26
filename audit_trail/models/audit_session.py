import hashlib
import logging
from datetime import timedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

ACTIVITY_REFRESH = timedelta(minutes=1)


class AuditSession(models.Model):
    _name = 'audit.session'
    _description = 'Audit Working Session'
    _order = 'login_date desc, id desc'

    user_id = fields.Many2one('res.users', string='User', index=True, ondelete='set null')
    login_date = fields.Datetime(string='Sign-in Time', default=fields.Datetime.now)
    last_activity_date = fields.Datetime(string='Last Activity')
    browser = fields.Char(string='Browser')
    ip_address = fields.Char(string='Network Address')
    session_key = fields.Char(string='Session Key', index=True, copy=False, groups='base.group_system')
    company_id = fields.Many2one(
        'res.company', string='Company', related='user_id.company_id', store=True, index=True)
    log_ids = fields.One2many('audit.log', 'session_id', string='Recorded Events')
    log_count = fields.Integer(string='Recorded Events Count', compute='_compute_log_count')

    _session_key_uniq = models.Constraint(
        'UNIQUE(session_key)',
        "A working session with this key already exists.",
    )

    @api.depends('user_id.name', 'login_date')
    def _compute_display_name(self):
        for session in self:
            date = fields.Datetime.to_string(session.login_date) if session.login_date else ''
            session.display_name = f"{session.user_id.name or _('Unknown')} {date}".strip()

    @api.depends('log_ids')
    def _compute_log_count(self):
        counts = dict(self.env['audit.log']._read_group(
            [('session_id', 'in', self.ids)], ['session_id'], ['__count']))
        for session in self:
            session.log_count = counts.get(session, 0)

    def action_view_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Session Events"),
            'res_model': 'audit.log',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('session_id', '=', self.id)],
        }

    @api.model
    def _get_current_session(self):
        """Return (creating if needed) the session of the current HTTP request."""
        try:
            from odoo.http import request
        except ImportError:
            return self.browse()
        http_session = getattr(request, 'session', None) if request else None
        sid = getattr(http_session, 'sid', None) if http_session else None
        if not sid:
            return self.browse()
        key = hashlib.sha256(f"{sid}-{self.env.uid}".encode()).hexdigest()
        Session = self.sudo()
        now = fields.Datetime.now()
        session = Session.search([('session_key', '=', key)], limit=1)
        if session:
            if not session.last_activity_date or now - session.last_activity_date > ACTIVITY_REFRESH:
                session.last_activity_date = now
            return session
        httprequest = request.httprequest
        user_agent = getattr(httprequest.user_agent, 'string', '') or ''
        try:
            with self.env.cr.savepoint():
                return Session.create({
                    'user_id': self.env.uid,
                    'login_date': now,
                    'last_activity_date': now,
                    'browser': user_agent[:255],
                    'ip_address': httprequest.remote_addr,
                    'session_key': key,
                })
        except Exception:
            _logger.debug("Audit session creation raced; reusing the existing one", exc_info=True)
            return Session.search([('session_key', '=', key)], limit=1)
