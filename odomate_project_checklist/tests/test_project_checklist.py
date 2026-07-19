from odoo import Command, fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProjectChecklist(TransactionCase):
    """Behavioral tests for the project_checklist module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Template = cls.env['project.checklist.template']
        cls.Task = cls.env['project.task']
        cls.project = cls.env['project.project'].create({'name': 'Test Project'})
        cls.template = cls.Template.create({
            'name': 'Onboarding',
            'line_ids': [
                Command.create({'name': 'Step A', 'sequence': 10}),
                Command.create({'name': 'Step B', 'sequence': 20}),
                Command.create({'name': 'Step C', 'sequence': 30}),
            ],
        })
        cls.template_alt = cls.Template.create({
            'name': 'Launch',
            'line_ids': [
                Command.create({'name': 'Alt 1', 'sequence': 10}),
                Command.create({'name': 'Alt 2', 'sequence': 20}),
            ],
        })

    def _new_task(self):
        return self.Task.create({
            'name': 'Task', 'project_id': self.project.id})

    # -- Templates ---------------------------------------------------------

    def test_template_line_count(self):
        self.assertEqual(self.template.line_count, 3)
        self.assertEqual(self.template_alt.line_count, 2)

    # -- Applying a checklist ---------------------------------------------

    def test_apply_on_empty_task_copies_lines(self):
        task = self._new_task()
        task.checklist_template_id = self.template
        self.assertEqual(len(task.checklist_line_ids), 3)
        self.assertEqual(
            set(task.checklist_line_ids.mapped('state')), {'to_do'})
        self.assertEqual(task.applied_template_id, self.template)
        # Independent copy: editing task lines must not touch the template.
        task.checklist_line_ids[0].name = 'Edited'
        self.assertEqual(self.template.line_ids[0].name, 'Step A')

    def test_switch_without_progress_replaces_immediately(self):
        task = self._new_task()
        task.checklist_template_id = self.template
        # All still to_do -> switching applies at once, no wizard.
        task.checklist_template_id = self.template_alt
        self.assertEqual(len(task.checklist_line_ids), 2)
        self.assertEqual(task.applied_template_id, self.template_alt)

    def test_switch_with_progress_waits_for_confirmation(self):
        task = self._new_task()
        task.checklist_template_id = self.template
        task.checklist_line_ids[0].action_start()
        # A started checklist must NOT be silently replaced.
        task.checklist_template_id = self.template_alt
        self.assertEqual(len(task.checklist_line_ids), 3)
        self.assertEqual(task.applied_template_id, self.template)
        self.assertTrue(task.checklist_needs_apply)

    def test_replace_wizard_confirm_replaces(self):
        task = self._new_task()
        task.checklist_template_id = self.template
        task.checklist_line_ids[0].action_done()
        wizard = self.env['project.task.checklist.replace.wizard'].create({
            'task_id': task.id,
            'new_template_id': self.template_alt.id,
        })
        wizard.action_confirm()
        self.assertEqual(len(task.checklist_line_ids), 2)
        self.assertEqual(
            set(task.checklist_line_ids.mapped('state')), {'to_do'})
        self.assertEqual(task.applied_template_id, self.template_alt)

    # -- Progress calculation ---------------------------------------------

    def test_progress_excludes_cancelled(self):
        task = self._new_task()
        task.checklist_template_id = self.template
        lines = task.checklist_line_ids
        lines[0].action_done()
        lines[1].action_cancel()
        # Eligible = 2 (Step A done, Step C to_do); Step B cancelled.
        self.assertAlmostEqual(task.checklist_progress, 50.0)
        lines[2].action_done()
        # Cancelling a step cannot cap progress below 100%.
        self.assertAlmostEqual(task.checklist_progress, 100.0)

    def test_progress_zero_when_all_cancelled(self):
        task = self._new_task()
        task.checklist_template_id = self.template
        task.checklist_line_ids.action_cancel()
        self.assertAlmostEqual(task.checklist_progress, 0.0)
        self.assertFalse(task.date_end)

    # -- Date stamping -----------------------------------------------------

    def test_start_date_stamped_on_first_in_progress(self):
        task = self._new_task()
        task.checklist_template_id = self.template
        self.assertFalse(task.date_start)
        task.checklist_line_ids[0].action_start()
        self.assertEqual(task.date_start, fields.Date.context_today(task))

    def test_start_date_not_overwritten(self):
        task = self._new_task()
        task.checklist_template_id = self.template
        task.date_start = '2020-01-01'
        task.checklist_line_ids[0].action_start()
        self.assertEqual(str(task.date_start), '2020-01-01')

    def test_end_date_stamped_on_completion(self):
        task = self._new_task()
        task.checklist_template_id = self.template
        task.checklist_line_ids.action_done()
        self.assertAlmostEqual(task.checklist_progress, 100.0)
        self.assertEqual(task.date_end, fields.Date.context_today(task))

    def test_end_date_self_heals_when_reopened(self):
        task = self._new_task()
        task.checklist_template_id = self.template
        task.checklist_line_ids.action_done()
        self.assertTrue(task.date_end)
        # Reopen a step -> progress drops -> end date cleared.
        task.checklist_line_ids[0].state = 'in_progress'
        self.assertLess(task.checklist_progress, 100.0)
        self.assertFalse(task.date_end)

    def test_end_date_cleared_on_confirmed_replace(self):
        task = self._new_task()
        task.checklist_template_id = self.template
        task.checklist_line_ids.action_done()
        self.assertTrue(task.date_end)
        wizard = self.env['project.task.checklist.replace.wizard'].create({
            'task_id': task.id,
            'new_template_id': self.template_alt.id,
        })
        wizard.action_confirm()
        self.assertFalse(task.date_end)
