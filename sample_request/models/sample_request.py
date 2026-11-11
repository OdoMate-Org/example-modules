from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

FOLLOW_UP_DELAY_DAYS = 14
TRANSITION_CONTEXT_KEY = 'sample_request_transition'
WORKFLOW_FIELDS = {'state', 'manager_id', 'rejection_reason', 'follow_up_outcome', 'follow_up_activity_id'}
LOCKED_AFTER_DRAFT_FIELDS = {'partner_id', 'user_id', 'reason_category', 'reason_note', 'line_ids', 'sent_date'}


class SampleRequest(models.Model):
    _name = 'sample.request'
    _description = 'Product Sample Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, readonly=True, copy=False, default='New')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, index=True, tracking=True)
    user_id = fields.Many2one(
        'res.users', string='Sales Rep', required=True, index=True, tracking=True,
        default=lambda self: self.env.user)
    reason_category = fields.Selection(
        [
            ('deal_in_progress', 'Deal in Progress'),
            ('new_prospect', 'New Prospect'),
            ('existing_customer', 'Existing Customer'),
            ('trade_show', 'Trade Show'),
            ('other', 'Other'),
        ], string='Reason', tracking=True)
    reason_note = fields.Text(string='Reason Details')
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('sent', 'Sent'),
            ('followed_up', 'Followed Up'),
            ('cancelled', 'Cancelled'),
        ], string='Status', required=True, default='draft', copy=False, index=True, tracking=True,
        group_expand='_group_expand_states')
    rejection_reason = fields.Text(string='Rejection Reason', copy=False)
    manager_id = fields.Many2one('res.users', string='Decided By', readonly=True, copy=False, tracking=True)
    sent_date = fields.Date(string='Sent Date', copy=False, tracking=True)
    follow_up_outcome = fields.Selection(
        [
            ('ordered', 'Ordered'),
            ('still_thinking', 'Still Thinking'),
            ('not_interested', 'Not Interested'),
        ], string='Follow-up Outcome', copy=False, tracking=True)
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', copy=False, ondelete='set null', tracking=True)
    line_ids = fields.One2many('sample.request.line', 'request_id', string='Products', copy=True)
    line_count = fields.Integer(string='Product Count', compute='_compute_line_count', store=True)
    request_count = fields.Integer(
        string='Count', default=1, readonly=True, aggregator='sum',
        help='Always 1: summed in reporting it counts the requests.')
    converted_count = fields.Integer(
        string='Converted', compute='_compute_conversion', store=True, aggregator='sum',
        help='1 when the request was followed up with the outcome "Ordered", otherwise 0.')
    conversion_rate = fields.Float(
        string='Conversion Rate (%)', compute='_compute_conversion', store=True, aggregator='avg',
        help='100 for a request that led to an order, 0 otherwise. Averaged over sent and followed-up requests it gives the conversion rate.')
    follow_up_activity_id = fields.Many2one('mail.activity', string='Follow-up Activity', readonly=True, copy=False, ondelete='set null')
    is_manager = fields.Boolean(string='Is Sample Manager', compute='_compute_is_manager')

    @api.model
    def _group_expand_states(self, states, domain):
        return [key for key, _label in self._fields['state'].selection]

    @api.depends('line_ids')
    def _compute_line_count(self):
        for request in self:
            request.line_count = len(request.line_ids)

    @api.depends('state', 'follow_up_outcome')
    def _compute_conversion(self):
        for request in self:
            converted = request.state == 'followed_up' and request.follow_up_outcome == 'ordered'
            request.converted_count = 1 if converted else 0
            request.conversion_rate = 100.0 if converted else 0.0

    @api.depends()
    @api.depends_context('uid')
    def _compute_is_manager(self):
        is_manager = self._is_sample_manager()
        for request in self:
            request.is_manager = is_manager

    @api.constrains('state', 'rejection_reason')
    def _check_rejection_reason(self):
        for request in self:
            if request.state == 'rejected' and not (request.rejection_reason or '').strip():
                raise ValidationError(_('A rejected sample request must have a rejection reason.'))

    @api.constrains('sale_order_id', 'follow_up_outcome')
    def _check_sale_order_outcome(self):
        for request in self:
            if request.sale_order_id and request.follow_up_outcome != 'ordered':
                raise ValidationError(_('A sales order can only be linked when the follow-up outcome is "Ordered".'))

    @api.model_create_multi
    def create(self, vals_list):
        if not self._is_sample_manager() and not self.env.su:
            for vals in vals_list:
                forced = [key for key in WORKFLOW_FIELDS & vals.keys() if vals[key] and not (key == 'state' and vals[key] == 'draft')]
                if forced:
                    raise UserError(_('New sample requests always start as drafts.'))
        sequence = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = sequence.next_by_code('sample.request') or 'New'
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su and not self.env.context.get(TRANSITION_CONTEXT_KEY) and not self._is_sample_manager():
            if WORKFLOW_FIELDS & vals.keys():
                raise UserError(_('The status of a sample request can only be changed with its workflow buttons.'))
            if LOCKED_AFTER_DRAFT_FIELDS & vals.keys() and any(request.state != 'draft' for request in self):
                raise UserError(_('A sample request can no longer be edited once it has been submitted. Cancel it while it is pending if it needs to change.'))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_processed(self):
        if any(request.state not in ('draft', 'cancelled') for request in self):
            raise UserError(_('Only draft or cancelled sample requests can be deleted.'))

    def _is_sample_manager(self):
        return self.env.user.has_group('sample_request.group_sample_request_manager')

    def _check_sample_manager(self):
        if not self.env.su and not self._is_sample_manager():
            raise UserError(_('Only Sample Request managers can perform this action.'))

    def _check_owner_or_manager(self):
        if self.env.su or self._is_sample_manager():
            return
        if any(request.user_id != self.env.user for request in self):
            raise UserError(_('Only the requesting sales rep or a manager can perform this action.'))

    def _check_state(self, allowed_states, action_label):
        for request in self:
            if request.state not in allowed_states:
                state_label = dict(self._fields['state']._description_selection(self.env))[request.state]
                raise UserError(_('"%(action)s" is not possible on %(name)s while it is %(state)s.', action=action_label, name=request.name, state=state_label))

    def _transition_write(self, vals):
        return self.with_context(**{TRANSITION_CONTEXT_KEY: True}).write(vals)

    def action_submit(self):
        self._check_owner_or_manager()
        self._check_state(('draft',), _('Submit'))
        for request in self:
            if not request.line_ids:
                raise UserError(_('Add at least one product to %(name)s before submitting it.', name=request.name))
        self._transition_write({'state': 'submitted'})
        self._notify_managers_pending_approval()
        return True

    def _notify_managers_pending_approval(self):
        managers = self.env.ref('sample_request.group_sample_request_manager').sudo().user_ids
        if not managers:
            return
        today = fields.Date.context_today(self)
        for request in self:
            for manager in managers:
                request.activity_schedule(
                    'mail.mail_activity_data_todo',
                    date_deadline=today,
                    summary=request.with_context(lang=manager.lang or self.env.lang).env._('Sample request awaiting approval'),
                    user_id=manager.id,
                )

    def _close_pending_approval_activities(self):
        todo_type = self.env.ref('mail.mail_activity_data_todo')
        for request in self:
            activities = request.activity_ids.filtered(lambda activity: activity.activity_type_id == todo_type)
            if activities:
                activities.action_feedback(feedback=_('Request decided.'))

    def action_approve(self):
        self._check_sample_manager()
        self._check_state(('submitted',), _('Approve'))
        self._close_pending_approval_activities()
        self._transition_write({'state': 'approved', 'manager_id': self.env.user.id})
        return True

    def action_reject(self, reason):
        self._check_sample_manager()
        self._check_state(('submitted',), _('Reject'))
        reason = (reason or '').strip()
        if not reason:
            raise UserError(_('Please give a rejection reason before rejecting the sample request.'))
        self._close_pending_approval_activities()
        self._transition_write({'state': 'rejected', 'rejection_reason': reason, 'manager_id': self.env.user.id})
        return True

    def action_mark_sent(self):
        self._check_sample_manager()
        self._check_state(('approved',), _('Mark as Sent'))
        for request in self:
            sent_date = request.sent_date or fields.Date.context_today(request)
            request._transition_write({'state': 'sent', 'sent_date': sent_date})
            activity = request.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=sent_date + timedelta(days=FOLLOW_UP_DELAY_DAYS),
                summary=request.with_context(lang=request.user_id.lang or self.env.lang).env._('Follow up on sample request'),
                user_id=request.user_id.id,
            )
            request._transition_write({'follow_up_activity_id': activity[:1].id})
        return True

    def action_log_outcome(self, outcome, sale_order=False):
        self._check_owner_or_manager()
        self._check_state(('sent',), _('Log Outcome'))
        if outcome not in dict(self._fields['follow_up_outcome'].selection):
            raise UserError(_('Please choose a valid follow-up outcome.'))
        outcome_label = dict(self._fields['follow_up_outcome']._description_selection(self.env))[outcome]
        for request in self:
            vals = {'state': 'followed_up', 'follow_up_outcome': outcome}
            if outcome == 'ordered' and sale_order:
                vals['sale_order_id'] = sale_order.id
            activity = request.follow_up_activity_id
            request._transition_write(vals)
            if activity.exists():
                activity.action_feedback(feedback=_('Outcome: %(outcome)s', outcome=outcome_label))
        return True

    def action_cancel(self):
        self._check_owner_or_manager()
        self._check_state(('draft', 'submitted'), _('Cancel'))
        self._close_pending_approval_activities()
        self._transition_write({'state': 'cancelled'})
        return True

    def _wizard_action(self, xml_id):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(xml_id)
        action['context'] = {'default_request_id': self.id}
        return action

    def action_open_reject_wizard(self):
        self._check_sample_manager()
        self._check_state(('submitted',), _('Reject'))
        return self._wizard_action('sample_request.sample_request_reject_wizard_action')

    def action_open_outcome_wizard(self):
        self._check_owner_or_manager()
        self._check_state(('sent',), _('Log Outcome'))
        return self._wizard_action('sample_request.sample_request_outcome_wizard_action')
