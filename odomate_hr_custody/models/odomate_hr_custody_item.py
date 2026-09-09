from odoo import _, api, fields, models


class OdomateHrCustodyItem(models.Model):
    _name = 'odomate.hr.custody.item'
    _description = 'Custody Item'
    _order = 'name, id'

    name = fields.Char(string="Item Name", required=True, index=True)
    image_1920 = fields.Image(string="Photo", max_width=1920, max_height=1920)
    description = fields.Text(string="Description")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Related Product",
        ondelete='set null',
        help="Optional link to a product record. Selecting a product fills in "
             "the item name once; the two are not kept synchronised afterwards.",
    )
    custody_ids = fields.One2many(
        comodel_name='odomate.hr.custody',
        inverse_name='item_id',
        string="Custody Requests",
    )
    current_custody_id = fields.Many2one(
        comodel_name='odomate.hr.custody',
        string="Current Custody",
        compute='_compute_current_custody',
    )
    current_holder_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Current Holder",
        compute='_compute_current_custody',
    )
    is_available = fields.Boolean(
        string="Available",
        compute='_compute_current_custody',
    )

    @api.depends('custody_ids.state', 'custody_ids.employee_id')
    def _compute_current_custody(self):
        holder_by_item = {}
        stored = self.filtered('id')
        if stored:
            for custody in self.env['odomate.hr.custody'].sudo().search([
                ('item_id', 'in', stored.ids),
                ('state', '=', 'approved'),
            ]):
                holder_by_item.setdefault(custody.item_id.id, custody)
        for item in self:
            current = holder_by_item.get(item.id)
            item.current_custody_id = current.id if current else False
            item.current_holder_id = current.employee_id.id if current else False
            item.is_available = not current

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id and not self.name:
            self.name = self.product_id.display_name

    def action_view_custody_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Custody Requests"),
            'res_model': 'odomate.hr.custody',
            'view_mode': 'list,form',
            'domain': [('item_id', '=', self.id)],
            'context': {'default_item_id': self.id},
        }
