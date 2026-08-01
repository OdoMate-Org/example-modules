from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

# Indexes replaced by parent-scoped name uniqueness (see _UNIQUE_INDEXES
# below) — dropped in init() so upgraded databases don't keep enforcing the
# old, stricter (company-wide) semantics alongside the new ones.
_STALE_INDEXES = [
    'odomate_product_kind_name_company_uniq',
    'odomate_product_kind_name_global_uniq',
]

# DDL for the conditional-uniqueness indexes. A plain SQL/models.Constraint
# unique on (company_id, code) treats NULL company_id rows as always distinct,
# so two global kinds could share a code. We therefore create two partial
# unique indexes: one for company-scoped rows, one for the global (NULL) rows.
# The same NULL-handling problem applies to parent_id for name uniqueness, so
# name uniqueness needs the cross product of (company scoped/global) x
# (has parent/root-level) — four partial indexes.
_UNIQUE_INDEXES = [
    (
        'odomate_product_kind_code_company_uniq',
        'company_id, code',
        'code IS NOT NULL AND code != \'\' AND company_id IS NOT NULL',
    ),
    (
        'odomate_product_kind_code_global_uniq',
        'code',
        'code IS NOT NULL AND code != \'\' AND company_id IS NULL',
    ),
    (
        'odomate_product_kind_sequence_code_company_uniq',
        'company_id, sequence_code',
        'sequence_code IS NOT NULL AND sequence_code != \'\' AND company_id IS NOT NULL',
    ),
    (
        'odomate_product_kind_sequence_code_global_uniq',
        'sequence_code',
        'sequence_code IS NOT NULL AND sequence_code != \'\' AND company_id IS NULL',
    ),
    (
        'odomate_product_kind_name_parent_company_uniq',
        'company_id, parent_id, name',
        'parent_id IS NOT NULL AND company_id IS NOT NULL',
    ),
    (
        'odomate_product_kind_name_parent_global_uniq',
        'parent_id, name',
        'parent_id IS NOT NULL AND company_id IS NULL',
    ),
    (
        'odomate_product_kind_name_root_company_uniq',
        'company_id, name',
        'parent_id IS NULL AND company_id IS NOT NULL',
    ),
    (
        'odomate_product_kind_name_root_global_uniq',
        'name',
        'parent_id IS NULL AND company_id IS NULL',
    ),
]


class OdomateProductKind(models.Model):
    _name = 'odomate.product.kind'
    _description = "Product Kind"
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'sequence, complete_name'

    name = fields.Char(required=True, index=True)
    code = fields.Char()
    sequence_code = fields.Char(
        string="Sequence Code",
        help="Short code (e.g. PRD/SF/CMP) reserved for automatic numbering "
             "of ECOs, BoMs and products. Distinct from the business Code "
             "and unique within the company.",
    )
    complete_name = fields.Char(
        compute='_compute_complete_name', recursive=True, store=True,
    )
    sequence = fields.Integer(default=10)
    color = fields.Integer(string="Color")
    description = fields.Text()
    route_type = fields.Selection(
        selection=[
            ('sold', "Sold (Finished Good)"),
            ('manufactured', "Manufactured"),
            ('semi_finished', "Semi-Finished"),
            ('component', "Component"),
            ('service', "Service"),
            ('transport', "Transport"),
            ('other', "Other"),
        ],
        required=True,
        default='other',
    )
    manufacturing_mode = fields.Selection(
        selection=[
            ('inherit', "Inherit"),
            ('mto', "Make to Order"),
            ('mts', "Make to Stock"),
            ('manual', "Manual"),
            ('disabled', "Disabled"),
        ],
        default='inherit',
    )
    requires_engineering = fields.Boolean()
    requires_team_planning = fields.Boolean()
    company_id = fields.Many2one(
        'res.company',
        help="Leave empty to make this kind global (shared across every company).",
    )
    active = fields.Boolean(default=True)

    parent_id = fields.Many2one(
        'odomate.product.kind', string="Parent Kind",
        ondelete='restrict', index=True,
    )
    child_ids = fields.One2many(
        'odomate.product.kind', 'parent_id', string="Sub Kinds",
    )
    parent_path = fields.Char(index=True)

    # Smart-button counters — non-stored, computed over the whole subtree.
    product_count = fields.Integer(compute='_compute_counts')
    bom_count = fields.Integer(compute='_compute_counts')
    sale_line_count = fields.Integer(compute='_compute_counts')
    mrp_production_count = fields.Integer(compute='_compute_counts')

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for kind in self:
            if kind.parent_id:
                kind.complete_name = "%s / %s" % (kind.parent_id.complete_name, kind.name)
            else:
                kind.complete_name = kind.name

    def _compute_counts(self):
        # active_test=False on every model involved: counts must stay stable
        # across archiving (both the kind's own subtree and the counted
        # records), not drop the moment something is archived.
        Kind = self.env['odomate.product.kind'].with_context(active_test=False)
        product_model = self.env['product.template'].with_context(active_test=False)
        bom_model = self.env['mrp.bom'].with_context(active_test=False)
        sale_line_model = self.env['sale.order.line'].with_context(active_test=False)
        production_model = self.env['mrp.production'].with_context(active_test=False)
        for kind in self:
            subtree = Kind.search([('id', 'child_of', kind.id)]) if kind.id else kind
            domain = [('odomate_product_kind_id', 'in', subtree.ids)]
            kind.product_count = product_model.search_count(domain)
            kind.bom_count = bom_model.search_count(domain)
            kind.sale_line_count = sale_line_model.search_count(domain)
            kind.mrp_production_count = production_model.search_count(
                [('odomate_product_kind_snapshot_id', 'in', subtree.ids)]
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        if self._has_cycle():
            raise ValidationError(_("You cannot create a recursive Product Kind hierarchy."))

    @api.constrains('company_id', 'parent_id')
    def _check_company_consistency(self):
        for kind in self:
            parent = kind.parent_id
            if parent and parent.company_id and kind.company_id and parent.company_id != kind.company_id:
                raise ValidationError(_(
                    "The Product Kind '%(child)s' must belong to the same company as its parent '%(parent)s'.",
                    child=kind.name, parent=parent.name,
                ))

    @api.constrains('active')
    def _check_archive(self):
        manager = self.env.user.has_group('odomate_product_kind.group_odomate_product_kind_manager')
        Kind = self.env['odomate.product.kind']
        Product = self.env['product.template']
        for kind in self:
            if kind.active:
                continue
            active_children = Kind.with_context(active_test=False).search_count([
                ('parent_id', '=', kind.id), ('active', '=', True),
            ])
            if active_children:
                raise ValidationError(_(
                    "Cannot archive Product Kind '%(name)s' while it has active sub kinds.",
                    name=kind.complete_name or kind.name,
                ))
            if not manager:
                active_products = Product.search_count([
                    ('odomate_product_kind_id', '=', kind.id), ('active', '=', True),
                ])
                if active_products:
                    raise ValidationError(_(
                        "Cannot archive Product Kind '%(name)s' while active products still use it. "
                        "Please ask a Product Kind Manager.",
                        name=kind.complete_name or kind.name,
                    ))

    # ------------------------------------------------------------------
    # ORM overrides — friendly uniqueness validation
    # ------------------------------------------------------------------
    # The partial unique indexes in init() are the concurrency-safe backstop,
    # but on their own they surface as a raw psycopg2.IntegrityError. These
    # overrides run the same scoping checks in Python first so a duplicate
    # raises a translated ValidationError before the write ever reaches
    # Postgres (a plain @api.constrains would run too late: constrains fire
    # after the ORM has already flushed the row, i.e. after the index would
    # already have raised).
    @api.model_create_multi
    def create(self, vals_list):
        self._check_duplicate_values(vals_list)
        return super().create(vals_list)

    def write(self, vals):
        if {'name', 'code', 'sequence_code', 'parent_id', 'company_id'} & vals.keys():
            merged = [{
                'id': kind.id,
                'name': vals.get('name', kind.name),
                'code': vals.get('code', kind.code),
                'sequence_code': vals.get('sequence_code', kind.sequence_code),
                'parent_id': vals['parent_id'] if 'parent_id' in vals else kind.parent_id.id,
                'company_id': vals['company_id'] if 'company_id' in vals else kind.company_id.id,
            } for kind in self]
            self._check_duplicate_values(merged)
        return super().write(vals)

    def _check_duplicate_values(self, vals_list):
        """Mirror the scoping of the partial unique indexes in Python: code
        and sequence_code unique per (company_id) tier, name unique per
        (company_id, parent_id) tier. Checks both against existing records
        (active_test=False — the indexes have no active-state filter, so an
        archived sibling still counts) and against sibling entries in the
        same vals_list (a create_multi batch isn't visible to itself in the
        DB until flush)."""
        Kind = self.env['odomate.product.kind'].with_context(active_test=False)

        for field_name, label in (('code', _("Code")), ('sequence_code', _("Sequence Code"))):
            seen = set()
            for vals in vals_list:
                value = vals.get(field_name)
                if not value:
                    continue
                company_id = vals.get('company_id') or False
                key = (company_id, value)
                domain = [(field_name, '=', value), ('company_id', '=', company_id)]
                if vals.get('id'):
                    domain.append(('id', '!=', vals['id']))
                if key in seen or Kind.search_count(domain):
                    raise ValidationError(_(
                        "The %(label)s '%(value)s' is already used by another Product Kind "
                        "%(scope)s.",
                        label=label, value=value,
                        scope=_("in this company") if company_id else _("among the global kinds"),
                    ))
                seen.add(key)

        seen_names = set()
        for vals in vals_list:
            name = vals.get('name')
            if not name:
                continue
            parent_id = vals.get('parent_id') or False
            company_id = vals.get('company_id') or False
            key = (company_id, parent_id, name)
            domain = [('name', '=', name), ('parent_id', '=', parent_id), ('company_id', '=', company_id)]
            if vals.get('id'):
                domain.append(('id', '!=', vals['id']))
            if key in seen_names or Kind.search_count(domain):
                if parent_id:
                    raise ValidationError(_(
                        "A Product Kind named '%(name)s' already exists under '%(parent)s'.",
                        name=name, parent=Kind.browse(parent_id).complete_name,
                    ))
                raise ValidationError(_(
                    "A top-level Product Kind named '%(name)s' already exists %(scope)s.",
                    name=name,
                    scope=_("in this company") if company_id else _("among the global kinds"),
                ))
            seen_names.add(key)

    # ------------------------------------------------------------------
    # Low-level
    # ------------------------------------------------------------------
    def unlink(self):
        # A cascading delete would silently wipe an entire sub-tree; require
        # the user to delete (or reparent) leaves first, with a clear message
        # rather than a raw ondelete='restrict' IntegrityError.
        Kind = self.env['odomate.product.kind'].with_context(active_test=False)
        for kind in self:
            child_count = Kind.search_count([('parent_id', '=', kind.id)])
            if child_count:
                raise UserError(_(
                    "Cannot delete Product Kind '%(name)s' because it still has "
                    "%(count)d sub kind(s). Delete or reparent them first.",
                    name=kind.complete_name or kind.name, count=child_count,
                ))
        return super().unlink()

    def init(self):
        # Drop indexes superseded by a wider or narrower uniqueness scope so
        # upgraded databases don't keep enforcing stale semantics.
        for index_name in _STALE_INDEXES:
            self.env.cr.execute('DROP INDEX IF EXISTS "%s"' % index_name)
        # DDL-level partial unique indexes for conditional uniqueness. This is
        # schema definition (not data access) and is the sanctioned Odoo way to
        # express uniqueness that a plain constraint cannot (NULL company rows).
        for index_name, columns, where in _UNIQUE_INDEXES:
            self.env.cr.execute(
                """
                SELECT 1 FROM pg_indexes
                WHERE indexname = %s AND schemaname = current_schema()
                """,
                (index_name,),
            )
            if not self.env.cr.fetchone():
                self.env.cr.execute(
                    "CREATE UNIQUE INDEX \"%s\" ON \"%s\" (%s) WHERE (%s)"
                    % (index_name, self._table, columns, where)
                )

    # ------------------------------------------------------------------
    # Smart-button actions
    # ------------------------------------------------------------------
    def _subtree_ids(self):
        self.ensure_one()
        Kind = self.env['odomate.product.kind'].with_context(active_test=False)
        return Kind.search([('id', 'child_of', self.id)]).ids

    def action_view_products(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Products"),
            'res_model': 'product.template',
            'view_mode': 'kanban,list,form',
            'domain': [('odomate_product_kind_id', 'in', self._subtree_ids())],
            'context': {'default_odomate_product_kind_id': self.id, 'active_test': False},
        }

    def action_view_boms(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Bills of Materials"),
            'res_model': 'mrp.bom',
            'view_mode': 'list,form',
            'domain': [('odomate_product_kind_id', 'in', self._subtree_ids())],
            'context': {'active_test': False},
        }

    def action_view_sale_lines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Sale Order Lines"),
            'res_model': 'sale.order.line',
            'view_mode': 'list,form',
            'domain': [('odomate_product_kind_id', 'in', self._subtree_ids())],
            'context': {'active_test': False},
        }

    def action_view_productions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Manufacturing Orders"),
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': [('odomate_product_kind_snapshot_id', 'in', self._subtree_ids())],
            'context': {'active_test': False},
        }
