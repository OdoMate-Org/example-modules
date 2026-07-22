from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestOfficeEquipment(TransactionCase):
    """Test cases for the office.equipment model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Equipment = cls.env['office.equipment']
        cls.employee = cls.env['hr.employee'].create({'name': 'Test Holder'})

    def test_create_defaults(self):
        equipment = self.Equipment.create({'name': 'Laptop A'})
        self.assertTrue(equipment.id)
        self.assertEqual(equipment.state, 'available')
        self.assertEqual(equipment.equipment_type, 'laptop')
        self.assertEqual(equipment.company_id, self.env.company)

    def test_name_search(self):
        equipment = self.Equipment.create({'name': 'Findable Monitor'})
        results = self.Equipment.name_search('Findable')
        self.assertIn(equipment.id, [res[0] for res in results])

    def test_check_out_flow(self):
        equipment = self.Equipment.create({'name': 'Laptop B'})
        equipment.employee_id = self.employee
        equipment.action_check_out()
        self.assertEqual(equipment.state, 'checked_out')
        self.assertEqual(equipment.checkout_date, fields.Date.context_today(equipment))
        self.assertFalse(equipment.return_date)

    def test_check_out_requires_employee(self):
        equipment = self.Equipment.create({'name': 'Laptop C'})
        with self.assertRaises(ValidationError):
            equipment.action_check_out()

    def test_return_flow(self):
        equipment = self.Equipment.create({
            'name': 'Laptop D',
            'employee_id': self.employee.id,
        })
        equipment.action_check_out()
        equipment.action_return()
        self.assertEqual(equipment.state, 'available')
        self.assertFalse(equipment.employee_id)
        self.assertEqual(equipment.return_date, fields.Date.context_today(equipment))

    def test_send_to_repair_clears_holder_keeps_notes(self):
        equipment = self.Equipment.create({
            'name': 'Phone E',
            'employee_id': self.employee.id,
            'condition_notes': 'Screen flickering',
        })
        equipment.action_check_out()
        equipment.action_send_to_repair()
        self.assertEqual(equipment.state, 'in_repair')
        self.assertFalse(equipment.employee_id)
        self.assertEqual(equipment.condition_notes, 'Screen flickering')

    def test_retire_clears_holder(self):
        equipment = self.Equipment.create({
            'name': 'Monitor F',
            'employee_id': self.employee.id,
        })
        equipment.action_check_out()
        equipment.action_retire()
        self.assertEqual(equipment.state, 'retired')
        self.assertFalse(equipment.employee_id)

    @mute_logger('odoo.sql_db')
    def test_employee_required_when_checked_out(self):
        with self.assertRaises(ValidationError):
            self.Equipment.create({
                'name': 'Laptop G',
                'state': 'checked_out',
            })

    def test_serial_unique_among_active(self):
        self.Equipment.create({'name': 'Laptop H', 'serial_number': 'SN-100'})
        with self.assertRaises(ValidationError):
            self.Equipment.create({'name': 'Laptop I', 'serial_number': 'SN-100'})

    def test_serial_reusable_after_retire(self):
        first = self.Equipment.create({'name': 'Laptop J', 'serial_number': 'SN-200'})
        first.action_retire()
        second = self.Equipment.create({'name': 'Laptop K', 'serial_number': 'SN-200'})
        self.assertTrue(second.id)

    def test_check_out_cap_allows_up_to_three(self):
        employee = self.env['hr.employee'].create({'name': 'Cap Holder A'})
        items = self.Equipment.create([
            {'name': 'Laptop L1', 'employee_id': employee.id},
            {'name': 'Laptop L2', 'employee_id': employee.id},
            {'name': 'Laptop L3', 'employee_id': employee.id},
        ])
        items.action_check_out()
        self.assertEqual(set(items.mapped('state')), {'checked_out'})

    def test_check_out_cap_blocks_fourth_item(self):
        employee = self.env['hr.employee'].create({'name': 'Cap Holder B'})
        self.Equipment.create([
            {'name': 'Laptop M1', 'employee_id': employee.id, 'state': 'checked_out'},
            {'name': 'Laptop M2', 'employee_id': employee.id, 'state': 'checked_out'},
            {'name': 'Laptop M3', 'employee_id': employee.id, 'state': 'checked_out'},
        ])
        fourth = self.Equipment.create({'name': 'Laptop M4', 'employee_id': employee.id})
        with self.assertRaises(ValidationError):
            fourth.action_check_out()
        self.assertEqual(fourth.state, 'available')

    def test_check_out_cap_batch_same_employee_blocks_at_limit(self):
        employee = self.env['hr.employee'].create({'name': 'Cap Holder C'})
        items = self.Equipment.create([
            {'name': 'Laptop N1', 'employee_id': employee.id},
            {'name': 'Laptop N2', 'employee_id': employee.id},
            {'name': 'Laptop N3', 'employee_id': employee.id},
            {'name': 'Laptop N4', 'employee_id': employee.id},
        ])
        with self.assertRaises(ValidationError):
            items.action_check_out()
        # The whole button action is one atomic call: once any item in the
        # batch breaches the cap, none of the batch's writes are persisted,
        # not just the offending item.
        self.assertEqual(set(items.mapped('state')), {'available'})

    def test_check_out_cap_independent_per_employee_in_batch(self):
        employee_a = self.env['hr.employee'].create({'name': 'Cap Holder D'})
        employee_b = self.env['hr.employee'].create({'name': 'Cap Holder E'})
        self.Equipment.create([
            {'name': 'Laptop O1', 'employee_id': employee_a.id, 'state': 'checked_out'},
            {'name': 'Laptop O2', 'employee_id': employee_a.id, 'state': 'checked_out'},
        ])
        item_a3 = self.Equipment.create({'name': 'Laptop O3', 'employee_id': employee_a.id})
        item_b1 = self.Equipment.create({'name': 'Phone O4', 'employee_id': employee_b.id})
        batch = item_a3 + item_b1
        batch.action_check_out()
        self.assertEqual(item_a3.state, 'checked_out')
        self.assertEqual(item_b1.state, 'checked_out')

    def test_check_out_cap_not_enforced_on_direct_write(self):
        employee = self.env['hr.employee'].create({'name': 'Cap Holder F'})
        self.Equipment.create([
            {'name': 'Laptop P1', 'employee_id': employee.id, 'state': 'checked_out'},
            {'name': 'Laptop P2', 'employee_id': employee.id, 'state': 'checked_out'},
            {'name': 'Laptop P3', 'employee_id': employee.id, 'state': 'checked_out'},
        ])
        fourth = self.Equipment.create({'name': 'Laptop P4'})
        fourth.write({'state': 'checked_out', 'employee_id': employee.id})
        self.assertEqual(fourth.state, 'checked_out')
