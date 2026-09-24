from odoo import api, fields, models
from odoo.exceptions import UserError


class ProjectTaskChecklistLine(models.Model):
    _name = 'project.task.checklist.line'
    _description = 'Task Checklist Step'
    _order = 'task_id, sequence, id'

    name = fields.Char(required=True)
    note = fields.Text()
    sequence = fields.Integer(default=10)
    state = fields.Selection(
        [
            ('to_do', 'To Do'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status', default='to_do', required=True)
    task_id = fields.Many2one(
        'project.task', string='Task', required=True, ondelete='cascade', index=True)
    template_line_id = fields.Many2one(
        'project.checklist.template.line', string='Template Step',
        ondelete='set null', index='btree_not_null')
    state_in_progress_date = fields.Datetime(string='Started On', copy=False)
    state_done_date = fields.Datetime(string='Done On', copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._stamp_state_dates()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals:
            self._stamp_state_dates()
        return res

    def _stamp_state_dates(self):
        now = fields.Datetime.now()
        started = self.filtered(lambda l: l.state == 'in_progress')
        started.filtered(lambda l: not l.state_in_progress_date).write(
            {'state_in_progress_date': now})
        self.filtered(lambda l: l.state == 'done' and not l.state_done_date).write(
            {'state_done_date': now})
        worked = self.filtered(lambda l: l.state in ('in_progress', 'done'))
        tasks = worked.task_id.filtered(lambda t: not t.checklist_date_start)
        if tasks:
            tasks.sudo().write({'checklist_date_start': fields.Date.context_today(self)})

    def _set_state(self, new_state, allowed_from):
        invalid = self.filtered(lambda l: l.state not in allowed_from)
        if invalid:
            labels = dict(self._fields['state']._description_selection(self.env))
            raise UserError(self.env._(
                "Step \"%(step)s\" cannot be set to %(target)s from %(current)s.",
                step=invalid[0].name,
                target=labels[new_state],
                current=labels[invalid[0].state],
            ))
        self.write({'state': new_state})
        return True

    def action_start(self):
        return self._set_state('in_progress', ('to_do',))

    def action_done(self):
        return self._set_state('done', ('to_do', 'in_progress'))

    def action_cancel(self):
        return self._set_state('cancelled', ('to_do', 'in_progress'))
