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
