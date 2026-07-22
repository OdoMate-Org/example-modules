from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.sql import create_index


class OfficeEquipment(models.Model):
    _name = 'office.equipment'
    _description = 'Office Equipment'
    _order = 'name'

    MAX_CONCURRENT_CHECKOUTS = 3

    name = fields.Char(string='Name', required=True, index=True)
    serial_number = fields.Char(string='Serial Number', copy=False)
    equipment_type = fields.Selection(
        selection=[
            ('laptop', 'Laptop'),
            ('phone', 'Phone'),
            ('monitor', 'Monitor'),
            ('peripheral', 'Peripheral'),
            ('other', 'Other'),
        ],
        string='Equipment Type',
        default='laptop',
        required=True,
    )
    state = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('checked_out', 'Checked Out'),
            ('in_repair', 'In Repair'),
            ('retired', 'Retired'),
        ],
        string='Status',
        default='available',
        required=True,
        copy=False,
        index=True,
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Current Holder',
        help="Employee who currently holds this equipment.",
    )
    checkout_date = fields.Date(string='Check-out Date', copy=False)
    return_date = fields.Date(string='Return Date', copy=False)
    condition_notes = fields.Text(string='Condition Notes')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    @api.constrains('state', 'employee_id')
    def _check_employee_required_when_checked_out(self):
        for equipment in self:
            if equipment.state == 'checked_out' and not equipment.employee_id:
                raise ValidationError(_(
                    "A current holder is required when the equipment "
                    "'%s' is checked out.", equipment.name,
                ))

    def _ensure_serial_available(self, serial, state, exclude_id=None):
        if not serial or state == 'retired':
            return
        domain = [
            ('serial_number', '=', serial),
            ('state', '!=', 'retired'),
        ]
        if exclude_id:
            domain.append(('id', '!=', exclude_id))
        if self.sudo().search_count(domain, limit=1):
            raise ValidationError(_(
                "The serial number '%s' is already used by another "
                "active piece of equipment.", serial,
            ))

    @api.model_create_multi
    def create(self, vals_list):
        seen = set()
        for vals in vals_list:
            serial = vals.get('serial_number')
            state = vals.get('state') or 'available'
            if serial and state != 'retired':
                if serial in seen:
                    raise ValidationError(_(
                        "The serial number '%s' is used more than once in "
                        "the same batch.", serial,
                    ))
                seen.add(serial)
                self._ensure_serial_available(serial, state)
        return super().create(vals_list)

    def write(self, vals):
        if 'serial_number' in vals or 'state' in vals:
            for equipment in self:
                serial = vals.get('serial_number', equipment.serial_number)
                state = vals.get('state', equipment.state)
                self._ensure_serial_available(serial, state, exclude_id=equipment.id)
        return super().write(vals)

    def _auto_init(self):
        res = super()._auto_init()
        # Partial uniqueness: serial_number must be unique among active
        # (non-retired) equipment. A retired item's serial can be reused,
        # and NULL serials never collide.
        create_index(
            self.env.cr,
            'office_equipment_serial_active_uniq',
            self._table,
            ['serial_number'],
            unique=True,
            where="serial_number IS NOT NULL AND state != 'retired'",
        )
        return res

    def action_check_out(self):
        checked_out_counts = {}
        for equipment in self:
            if not equipment.employee_id:
                raise ValidationError(_(
                    "Assign a current holder before checking out '%s'.",
                    equipment.name,
                ))
            employee = equipment.employee_id
            current_count = checked_out_counts.get(employee.id)
            if current_count is None:
                current_count = self.search_count([
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'checked_out'),
                ])
            if current_count >= self.MAX_CONCURRENT_CHECKOUTS:
                raise ValidationError(_(
                    "'%s' already holds %s checked-out item(s), the "
                    "maximum allowed is %s. Return an item before checking "
                    "out '%s'.",
                    employee.name, current_count,
                    self.MAX_CONCURRENT_CHECKOUTS, equipment.name,
                ))
            checked_out_counts[employee.id] = current_count + 1
            equipment.write({
                'state': 'checked_out',
                'checkout_date': fields.Date.context_today(equipment),
                'return_date': False,
            })
        return True

    def action_return(self):
        for equipment in self:
            equipment.write({
                'state': 'available',
                'employee_id': False,
                'return_date': fields.Date.context_today(equipment),
            })
        return True

    def action_send_to_repair(self):
        self.write({
            'state': 'in_repair',
            'employee_id': False,
        })
        return True

    def action_retire(self):
        self.write({
            'state': 'retired',
            'employee_id': False,
        })
        return True
