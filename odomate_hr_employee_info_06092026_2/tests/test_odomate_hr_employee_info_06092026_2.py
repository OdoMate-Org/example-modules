from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOdomateHrEmployeeInfo(TransactionCase):
    """Behaviour expected from odomate_hr_employee_info_06092026_2."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.Dependant = cls.env['odomate.hr.dependant']
        cls.Relationship = cls.env['odomate.hr.relationship']
        cls.Employee = cls.env['hr.employee']
        cls.spouse = cls.env.ref(
            'odomate_hr_employee_info_06092026_2.odomate_hr_relationship_spouse'
        )
        cls.son = cls.env.ref(
            'odomate_hr_employee_info_06092026_2.odomate_hr_relationship_son'
        )

    def _create_employee(self, name):
        return self.Employee.create({'name': name})

    def _create_internal_user(self, login, groups=None):
        group_ids = groups or [self.env.ref('base.group_user').id]
        return self.env['res.users'].create({
            'name': login.replace('_', ' ').title(),
            'login': login,
            'company_id': self.company.id,
            'company_ids': [(6, 0, [self.company.id])],
            'group_ids': [(6, 0, group_ids)],
        })

    # ------------------------------------------------------------------
    # Master data
    # ------------------------------------------------------------------
    def test_relationship_seed_data_is_installed(self):
        names = self.Relationship.search([]).mapped('name')
        for expected in ('Spouse', 'Father', 'Mother', 'Son', 'Daughter'):
            self.assertIn(expected, names)

    def test_relationship_crud_and_name_search(self):
        relationship = self.Relationship.create({'name': 'Guardian'})
        self.assertTrue(relationship.active)
        self.assertEqual(
            self.Relationship.name_search('Guard')[0][0], relationship.id
        )
        relationship.write({'name': 'Legal Guardian'})
        self.assertEqual(relationship.name, 'Legal Guardian')
        relationship.unlink()
        self.assertFalse(relationship.exists())

    # ------------------------------------------------------------------
    # Dependants
    # ------------------------------------------------------------------
    def test_dependant_crud(self):
        employee = self._create_employee("Dependant Owner")
        dependant = self.Dependant.create({
            'employee_id': employee.id,
            'name': "Anna Owner",
            'relationship_id': self.spouse.id,
            'phone': "+1 555 0100",
            'birthdate': date(1990, 4, 2),
        })
        self.assertEqual(dependant.company_id, employee.company_id)
        self.assertIn(dependant, employee.dependant_ids)
        dependant.write({'phone': "+1 555 0199"})
        self.assertEqual(dependant.phone, "+1 555 0199")
        dependant.unlink()
        self.assertFalse(employee.dependant_ids)

    def test_dependants_are_removed_with_their_employee(self):
        employee = self._create_employee("Cascade Owner")
        dependant = self.Dependant.create({
            'employee_id': employee.id,
            'name': "Cascade Child",
            'relationship_id': self.son.id,
        })
        employee.unlink()
        self.assertFalse(dependant.exists())

    def test_flagging_emergency_contact_syncs_employee_and_clears_others(self):
        employee = self._create_employee("Emergency Owner")
        first = self.Dependant.create({
            'employee_id': employee.id,
            'name': "First Contact",
            'relationship_id': self.spouse.id,
            'phone': "+1 555 0001",
            'is_emergency_contact': True,
        })
        self.assertEqual(employee.emergency_contact, "First Contact")
        self.assertEqual(employee.emergency_phone, "+1 555 0001")

        second = self.Dependant.create({
            'employee_id': employee.id,
            'name': "Second Contact",
            'relationship_id': self.son.id,
            'phone': "+1 555 0002",
            'is_emergency_contact': True,
        })
        self.assertFalse(first.is_emergency_contact)
        self.assertTrue(second.is_emergency_contact)
        self.assertEqual(employee.emergency_contact, "Second Contact")
        self.assertEqual(employee.emergency_phone, "+1 555 0002")

    def test_only_one_emergency_contact_survives_a_batch_create(self):
        employee = self._create_employee("Batch Owner")
        self.Dependant.create([
            {
                'employee_id': employee.id,
                'name': "Batch One",
                'relationship_id': self.spouse.id,
                'is_emergency_contact': True,
            },
            {
                'employee_id': employee.id,
                'name': "Batch Two",
                'relationship_id': self.son.id,
                'is_emergency_contact': True,
            },
        ])
        flagged = employee.dependant_ids.filtered('is_emergency_contact')
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged.name, "Batch Two")
        self.assertEqual(employee.emergency_contact, "Batch Two")

    def test_emergency_contact_stays_manually_editable(self):
        employee = self._create_employee("Manual Owner")
        self.Dependant.create({
            'employee_id': employee.id,
            'name': "Auto Filled",
            'relationship_id': self.spouse.id,
            'is_emergency_contact': True,
        })
        employee.write({'emergency_contact': "Neighbour", 'emergency_phone': "+1 555 9999"})
        self.assertEqual(employee.emergency_contact, "Neighbour")
        self.assertEqual(employee.emergency_phone, "+1 555 9999")

    # ------------------------------------------------------------------
    # Spouse auto-add
    # ------------------------------------------------------------------
    def test_spouse_dependant_is_created_once(self):
        employee = self._create_employee("Spouse Owner")
        employee.write({
            'spouse_complete_name': "Maria Spouse",
            'spouse_birthdate': date(1988, 9, 12),
        })
        spouses = employee.dependant_ids.filtered(
            lambda dependant: dependant.relationship_id == self.spouse
        )
        self.assertEqual(len(spouses), 1)
        self.assertEqual(spouses.name, "Maria Spouse")
        self.assertEqual(spouses.birthdate, date(1988, 9, 12))

        employee.write({'spouse_birthdate': date(1988, 9, 13)})
        spouses = employee.dependant_ids.filtered(
            lambda dependant: dependant.relationship_id == self.spouse
        )
        self.assertEqual(len(spouses), 1)

    def test_spouse_dependant_needs_both_values(self):
        employee = self._create_employee("Partial Spouse Owner")
        employee.write({'spouse_complete_name': "Nameless Date"})
        self.assertFalse(employee.dependant_ids)

    # ------------------------------------------------------------------
    # Joining date
    # ------------------------------------------------------------------
    def test_joining_date_is_the_earliest_version_start(self):
        employee = self._create_employee("Joining Owner")
        employee.version_ids.write({'date_version': date(2021, 3, 15)})
        self.assertEqual(employee.joining_date, date(2021, 3, 15))

        self.env['hr.version'].create({
            'employee_id': employee.id,
            'date_version': date(2019, 6, 1),
            'hr_responsible_id': self.env.user.id,
        })
        self.assertEqual(employee.joining_date, date(2019, 6, 1))

    def test_joining_date_is_not_writable(self):
        employee = self._create_employee("Readonly Joining Owner")
        self.assertTrue(self.Employee._fields['joining_date'].readonly)
        self.assertTrue(self.Employee._fields['joining_date'].store)
        self.assertTrue(employee.joining_date)

    def test_joining_date_write_is_ignored(self):
        employee = self._create_employee("Write Attempt Owner")
        computed_value = employee.joining_date
        employee.write({'joining_date': date(2001, 1, 1)})
        self.assertEqual(employee.joining_date, computed_value)
        employee.version_ids.write({'date_version': date(2015, 5, 20)})
        self.assertEqual(employee.joining_date, date(2015, 5, 20))

    def test_joining_date_create_value_is_ignored(self):
        employee = self.Employee.create({
            'name': "Create Attempt Owner",
            'joining_date': date(2001, 1, 1),
        })
        self.assertNotEqual(employee.joining_date, date(2001, 1, 1))

    # ------------------------------------------------------------------
    # Notice period
    # ------------------------------------------------------------------
    def test_notice_period_defaults_from_company(self):
        self.company.hr_default_notice_period_days = 45
        defaults = self.env['hr.version'].default_get(['notice_period'])
        self.assertEqual(defaults.get('notice_period'), 45)

        employee = self._create_employee("Notice Owner")
        self.assertEqual(employee.version_ids[0].notice_period, 45)

    def test_changing_company_default_leaves_existing_versions_alone(self):
        self.company.hr_default_notice_period_days = 20
        employee = self._create_employee("Frozen Notice Owner")
        version = employee.version_ids[0]
        self.assertEqual(version.notice_period, 20)
        self.company.hr_default_notice_period_days = 90
        self.assertEqual(version.notice_period, 20)

    # ------------------------------------------------------------------
    # Login to employee
    # ------------------------------------------------------------------
    def test_new_internal_user_gets_an_employee(self):
        self.company.hr_auto_create_employee = True
        user = self._create_internal_user('odomate_auto_employee')
        self.assertTrue(user.employee_ids)
        self.assertEqual(user.employee_ids[0].name, user.name)

    def test_no_employee_when_the_company_switch_is_off(self):
        self.company.hr_auto_create_employee = False
        user = self._create_internal_user('odomate_no_auto_employee')
        self.assertFalse(user.employee_ids)

    def test_portal_user_gets_no_employee(self):
        self.company.hr_auto_create_employee = True
        user = self._create_internal_user(
            'odomate_portal_user', groups=[self.env.ref('base.group_portal').id]
        )
        self.assertTrue(user.share)
        self.assertFalse(user.employee_ids)

    # ------------------------------------------------------------------
    # Access rules
    # ------------------------------------------------------------------
    def test_employee_cannot_read_a_colleague_dependant(self):
        self.company.hr_auto_create_employee = True
        reader = self._create_internal_user('odomate_dependant_reader')
        own_dependant = self.Dependant.create({
            'employee_id': reader.employee_ids[0].id,
            'name': "Own Child",
            'relationship_id': self.son.id,
        })
        colleague = self._create_employee("Colleague Owner")
        colleague_dependant = self.Dependant.create({
            'employee_id': colleague.id,
            'name': "Colleague Child",
            'relationship_id': self.son.id,
        })
        self.assertEqual(
            own_dependant.with_user(reader).read(['name'])[0]['name'], "Own Child"
        )
        with self.assertRaises(AccessError):
            colleague_dependant.with_user(reader).read(['name'])

    def test_hr_officer_reads_every_dependant(self):
        officer = self._create_internal_user(
            'odomate_hr_officer',
            groups=[
                self.env.ref('base.group_user').id,
                self.env.ref('hr.group_hr_user').id,
            ],
        )
        colleague = self._create_employee("Officer Visible Owner")
        dependant = self.Dependant.create({
            'employee_id': colleague.id,
            'name': "Visible Child",
            'relationship_id': self.son.id,
        })
        self.assertEqual(
            dependant.with_user(officer).read(['name'])[0]['name'], "Visible Child"
        )

    def test_employee_cannot_write_a_dependant(self):
        self.company.hr_auto_create_employee = True
        reader = self._create_internal_user('odomate_dependant_writer')
        own_dependant = self.Dependant.create({
            'employee_id': reader.employee_ids[0].id,
            'name': "Own Child",
            'relationship_id': self.son.id,
        })
        with self.assertRaises(AccessError):
            own_dependant.with_user(reader).write({'name': "Renamed"})

    # ------------------------------------------------------------------
    # Expiry warnings
    # ------------------------------------------------------------------
    def _employee_mails(self, employee, previous_ids):
        return self.env['mail.mail'].search([
            ('id', 'not in', previous_ids),
            ('model', '=', 'hr.employee'),
            ('res_id', '=', employee.id),
        ])

    def test_cron_warns_exactly_on_the_lead_time_day(self):
        today = fields.Date.context_today(self.Employee)
        self.company.hr_identification_expiry_warning_days = 14
        due = self._create_employee("Due Identification")
        due.write({
            'private_email': 'due.identification@example.com',
            'identification_expiry_date': today + timedelta(days=14),
        })
        not_due = self._create_employee("Far Identification")
        not_due.write({
            'private_email': 'far.identification@example.com',
            'identification_expiry_date': today + timedelta(days=365),
        })
        previous_ids = self.env['mail.mail'].search([]).ids
        self.Employee._odomate_cron_identity_expiry_warnings()
        self.assertTrue(self._employee_mails(due, previous_ids))
        self.assertFalse(self._employee_mails(not_due, previous_ids))

    def test_cron_warns_on_the_passport_lead_time(self):
        today = fields.Date.context_today(self.Employee)
        self.company.hr_passport_expiry_warning_days = 180
        due = self._create_employee("Due Passport")
        due.write({
            'private_email': 'due.passport@example.com',
            'passport_expiration_date': today + timedelta(days=180),
        })
        previous_ids = self.env['mail.mail'].search([]).ids
        self.Employee._odomate_cron_identity_expiry_warnings()
        self.assertTrue(self._employee_mails(due, previous_ids))

    def test_send_now_button_ignores_the_lead_time(self):
        employee = self._create_employee("Manual Warning")
        employee.write({
            'private_email': 'manual.warning@example.com',
            'identification_expiry_date': date.today() + timedelta(days=900),
            'passport_expiration_date': date.today() + timedelta(days=900),
        })
        previous_ids = self.env['mail.mail'].search([]).ids
        action = employee.action_send_identification_expiry_warning()
        self.assertEqual(action['tag'], 'display_notification')
        self.assertTrue(self._employee_mails(employee, previous_ids))

        previous_ids = self.env['mail.mail'].search([]).ids
        employee.action_send_passport_expiry_warning()
        self.assertTrue(self._employee_mails(employee, previous_ids))

    def test_warning_without_email_sends_nothing(self):
        employee = self._create_employee("No Email Warning")
        employee.write({'identification_expiry_date': date.today() + timedelta(days=5)})
        previous_ids = self.env['mail.mail'].search([]).ids
        action = employee.action_send_identification_expiry_warning()
        self.assertEqual(action['params']['type'], 'warning')
        self.assertFalse(self._employee_mails(employee, previous_ids))

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------
    def test_settings_round_trip_to_the_company(self):
        settings = self.env['res.config.settings'].create({
            'hr_identification_expiry_warning_days': 21,
            'hr_passport_expiry_warning_days': 120,
            'hr_auto_create_employee': False,
            'hr_default_notice_period_days': 60,
        })
        settings.execute()
        self.assertEqual(self.company.hr_identification_expiry_warning_days, 21)
        self.assertEqual(self.company.hr_passport_expiry_warning_days, 120)
        self.assertFalse(self.company.hr_auto_create_employee)
        self.assertEqual(self.company.hr_default_notice_period_days, 60)

    # ------------------------------------------------------------------
    # Privilege escalation
    # ------------------------------------------------------------------
    def test_module_grants_no_group_to_another_modules_record(self):
        xmlids = self.env['ir.model.data'].search([
            ('module', '=', 'odomate_hr_employee_info_06092026_2'),
            ('model', '=', 'res.users'),
        ])
        self.assertFalse(xmlids)
