from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestProjectChecklist(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Template = cls.env['project.checklist.template']
        cls.Line = cls.env['project.task.checklist.line']
        cls.project = cls.env['project.project'].create({'name': 'Checklist Test Project'})
        cls.template = cls.Template.create({
            'name': 'Onboarding',
            'line_ids': [
                (0, 0, {'name': 'Step A', 'sequence': 1, 'note': 'First'}),
                (0, 0, {'name': 'Step B', 'sequence': 2}),
                (0, 0, {'name': 'Step C', 'sequence': 3}),
            ],
        })
        cls.template_2 = cls.Template.create({
            'name': 'Launch',
            'line_ids': [
                (0, 0, {'name': 'Launch 1', 'sequence': 1}),
                (0, 0, {'name': 'Launch 2', 'sequence': 2}),
            ],
        })
        cls.today = fields.Date.context_today(cls.project)

    def _new_task(self, template=None, **extra):
        vals = {'name': 'Task', 'project_id': self.project.id}
        if template:
            vals['checklist_template_id'] = template.id
        vals.update(extra)
        return self.env['project.task'].create(vals)

    # Templates -----------------------------------------------------------

    def test_template_line_count_and_name_search(self):
        self.assertEqual(self.template.line_count, 3)
        self.template.write({'line_ids': [(0, 0, {'name': 'Step D'})]})
        self.assertEqual(self.template.line_count, 4)
        found = self.Template.name_search('Onboard')
        self.assertIn(self.template.id, [rec[0] for rec in found])

    def test_template_archive(self):
        self.template_2.action_archive()
        self.assertFalse(self.template_2.active)
        self.assertNotIn(self.template_2, self.Template.search([]))

    # Applying ------------------------------------------------------------

    def test_apply_on_create_copies_lines(self):
        task = self._new_task(self.template)
        lines = task.checklist_line_ids.sorted('sequence')
        self.assertEqual(lines.mapped('name'), ['Step A', 'Step B', 'Step C'])
        self.assertEqual(set(lines.mapped('state')), {'to_do'})
        self.assertEqual(lines[0].note, 'First')
        self.assertEqual(lines.template_line_id, self.template.line_ids)

    def test_apply_on_write_without_progress_replaces_silently(self):
        task = self._new_task(self.template)
        task.checklist_template_id = self.template_2
        self.assertEqual(
            sorted(task.checklist_line_ids.mapped('name')), ['Launch 1', 'Launch 2'])

    def test_switch_with_progress_is_blocked_outside_wizard(self):
        task = self._new_task(self.template)
        task.checklist_line_ids[0].action_start()
        self.assertTrue(task.checklist_has_progress)
        with self.assertRaises(UserError):
            task.write({'checklist_template_id': self.template_2.id})
        self.assertEqual(task.checklist_template_id, self.template)
        self.assertEqual(len(task.checklist_line_ids), 3)

    def test_template_edit_does_not_touch_task_copy(self):
        task = self._new_task(self.template)
        self.template.line_ids[0].name = 'Renamed'
        self.assertNotIn('Renamed', task.checklist_line_ids.mapped('name'))
        task.checklist_line_ids[0].unlink()
        self.assertEqual(self.template.line_count, 3)

    # Progress ------------------------------------------------------------

    def test_progress_excludes_cancelled(self):
        task = self._new_task(self.template)
        a, b, c = task.checklist_line_ids.sorted('sequence')
        self.assertEqual(task.checklist_progress, 0.0)
        a.action_done()
        self.assertAlmostEqual(task.checklist_progress, 100.0 / 3, places=2)
        b.action_cancel()
        self.assertAlmostEqual(task.checklist_progress, 50.0, places=2)
        c.action_done()
        self.assertEqual(task.checklist_progress, 100.0)

    def test_progress_zero_without_eligible_lines(self):
        task = self._new_task()
        self.assertEqual(task.checklist_progress, 0.0)
        task = self._new_task(self.template)
        task.checklist_line_ids.action_cancel()
        self.assertEqual(task.checklist_progress, 0.0)
        self.assertFalse(task.checklist_date_end)

    # State transitions ---------------------------------------------------

    def test_state_transitions(self):
        task = self._new_task(self.template)
        line = task.checklist_line_ids[0]
        line.action_start()
        self.assertEqual(line.state, 'in_progress')
        self.assertTrue(line.state_in_progress_date)
        line.action_done()
        self.assertEqual(line.state, 'done')
        self.assertTrue(line.state_done_date)
        with self.assertRaises(UserError):
            line.action_cancel()
        with self.assertRaises(UserError):
            line.action_start()
        other = task.checklist_line_ids[1]
        other.action_cancel()
        self.assertEqual(other.state, 'cancelled')
        other.state = 'to_do'
        self.assertEqual(other.state, 'to_do')

    # Dates ---------------------------------------------------------------

    def test_start_date_stamped_once(self):
        task = self._new_task(self.template)
        self.assertFalse(task.checklist_date_start)
        task.checklist_line_ids[0].action_start()
        self.assertEqual(task.checklist_date_start, self.today)
        manual = fields.Date.from_string('2020-01-01')
        task.checklist_date_start = manual
        task.checklist_line_ids[1].action_start()
        self.assertEqual(task.checklist_date_start, manual)

    def test_end_date_stamp_and_self_heal(self):
        task = self._new_task(self.template)
        task.checklist_line_ids.action_done()
        self.assertEqual(task.checklist_progress, 100.0)
        self.assertEqual(task.checklist_date_end, self.today)
        task.checklist_line_ids[0].state = 'in_progress'
        self.assertFalse(task.checklist_date_end)
        task.checklist_line_ids[0].action_done()
        self.assertEqual(task.checklist_date_end, self.today)
        self.Line.create({'task_id': task.id, 'name': 'Ad-hoc'})
        self.assertFalse(task.checklist_date_end)

    def test_end_date_keeps_manual_value_when_complete(self):
        task = self._new_task(self.template)
        manual = fields.Date.from_string('2021-06-30')
        task.checklist_date_end = manual
        task.checklist_line_ids.action_done()
        self.assertEqual(task.checklist_date_end, manual)

    # Replace wizard ------------------------------------------------------

    def test_replace_wizard_confirm(self):
        task = self._new_task(self.template)
        task.checklist_line_ids.action_done()
        start = task.checklist_date_start
        self.assertTrue(task.checklist_date_end)
        action = task.action_open_checklist_replace_wizard()
        self.assertEqual(action['res_model'], 'project.task.checklist.replace.wizard')
        wizard = self.env['project.task.checklist.replace.wizard'].with_context(
            action['context']).create({'new_template_id': self.template_2.id})
        self.assertEqual(wizard.task_id, task)
        self.assertTrue(wizard.warning_message)
        wizard.action_confirm()
        self.assertEqual(task.checklist_template_id, self.template_2)
        self.assertEqual(
            sorted(task.checklist_line_ids.mapped('name')), ['Launch 1', 'Launch 2'])
        self.assertEqual(set(task.checklist_line_ids.mapped('state')), {'to_do'})
        self.assertFalse(task.checklist_date_end)
        self.assertEqual(task.checklist_date_start, start)

    def test_replace_wizard_discard_changes_nothing(self):
        task = self._new_task(self.template)
        task.checklist_line_ids[0].action_start()
        self.env['project.task.checklist.replace.wizard'].create({
            'task_id': task.id, 'new_template_id': self.template_2.id})
        self.assertEqual(task.checklist_template_id, self.template)
        self.assertEqual(len(task.checklist_line_ids), 3)
        self.assertEqual(task.checklist_line_ids[0].state, 'in_progress')

    # Security ------------------------------------------------------------

    def test_line_access_follows_task_visibility(self):
        user = new_test_user(
            self.env, login='checklist_user',
            groups='base.group_user,project.group_project_user')
        private_project = self.env['project.project'].create({
            'name': 'Private', 'privacy_visibility': 'followers'})
        task = self.env['project.task'].create({
            'name': 'Secret', 'project_id': private_project.id,
            'checklist_template_id': self.template.id})
        lines_as_user = self.Line.with_user(user).search([('task_id', '=', task.id)])
        self.assertFalse(lines_as_user)
        with self.assertRaises(AccessError):
            task.checklist_line_ids.with_user(user).read(['name'])
        public_task = self._new_task(self.template)
        self.assertEqual(
            len(self.Line.with_user(user).search([('task_id', '=', public_task.id)])), 3)

    # CRUD / demo -------------------------------------------------------------

    def test_line_crud_and_name_search(self):
        task = self._new_task()
        line = self.Line.create({'task_id': task.id, 'name': 'Ad-hoc step'})
        self.assertTrue(line.exists())
        self.assertEqual(line.state, 'to_do')
        line.write({'name': 'Renamed step', 'note': 'Some note'})
        self.assertEqual(line.name, 'Renamed step')
        self.assertIsInstance(self.Line.name_search('', limit=5), list)
        self.assertIsInstance(
            self.env['project.checklist.template.line'].name_search('', limit=5), list)
        line.unlink()
        self.assertFalse(line.exists())
        self.assertFalse(task.checklist_line_ids)

    def test_template_unlink_keeps_task_lines(self):
        task = self._new_task(self.template_2)
        self.template_2.unlink()
        self.assertEqual(len(task.checklist_line_ids), 2)
        self.assertFalse(task.checklist_line_ids.template_line_id)

    def test_demo_data_loaded(self):
        if not self.env.ref('odomate_project_checklist.demo_task_website_done', raise_if_not_found=False):
            self.skipTest('Demo data not loaded')
        self.assertGreaterEqual(self.Template.search_count([]), 3)
        fresh = self.env.ref('odomate_project_checklist.demo_task_onboarding_fresh')
        self.assertEqual(len(fresh.checklist_line_ids), 5)
        self.assertEqual(fresh.checklist_progress, 0.0)
        done = self.env.ref('odomate_project_checklist.demo_task_website_done')
        self.assertEqual(done.checklist_progress, 100.0)
        self.assertTrue(done.checklist_date_start)
        self.assertTrue(done.checklist_date_end)
        cancelled = self.env.ref('odomate_project_checklist.demo_task_website_cancelled')
        self.assertIn('cancelled', cancelled.checklist_line_ids.mapped('state'))
        self.assertAlmostEqual(cancelled.checklist_progress, 200.0 / 3, places=2)

    def test_template_readonly_for_internal_users(self):
        user = new_test_user(self.env, login='checklist_basic', groups='base.group_user')
        self.assertTrue(self.Template.with_user(user).search([('id', '=', self.template.id)]))
        with self.assertRaises(AccessError):
            self.Template.with_user(user).create({'name': 'Nope'})
