from odoo import fields, models


class OdomateHrAnnouncementCategory(models.Model):
    _name = 'odomate.hr.announcement.category'
    _description = 'HR Announcement Category'
    _order = 'name'

    name = fields.Char(string='Category', required=True)
    color = fields.Integer(string='Color')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        help="Leave empty to share this category with every company.",
    )
