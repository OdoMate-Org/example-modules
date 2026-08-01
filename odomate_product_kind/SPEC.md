# SPEC.md — the business specification this module was generated from

This is the finalized specification produced during the OdoMate refinement
conversation, verbatim (translated from the original Ukrainian). The module
in this folder was generated from it — code, views, security, demo data,
tests, and the user guide in `doc/` — and published after human security
review, unedited apart from publication metadata (store banner reference).

Generated with OdoMate (https://www.odomate.pro) — July 2026, Odoo 19 Community.

---

## Module: odomate_product_kind
Hierarchical production classification "Product Kind" that carries through and freezes as a snapshot across the product → sale → manufacturing chain.

### Models

- **odomate.product.kind**: name (Char, required), code (Char), complete_name (Char, compute='_compute_complete_name', recursive=True, store=True), sequence (Integer), route_type (Selection: sold/manufactured/semi_finished/component/service/transport/other, required), manufacturing_mode (Selection: inherit/mto/mts/manual/disabled, default inherit), requires_engineering (Boolean), requires_team_planning (Boolean), company_id (Many2one res.company, optional — empty = global kind), active (Boolean, default True)
  - Relations: parent_id (Many2one odomate.product.kind, ondelete='cascade'), child_ids (One2many odomate.product.kind, 'parent_id'), parent_path (Char, index) for _parent_store
  - Computed fields: complete_name (path "Parent / Child"); product_count, bom_count, sale_line_count, mrp_production_count (compute, child_of across the whole subtree — for the smart buttons)

- **product.template**: odomate_product_kind_id (Many2one odomate.product.kind, domain ['|', ('company_id','=',False), ('company_id','=',company_id)])
  - Derived readonly display fields (related, non-stored): odomate_route_type, odomate_manufacturing_mode, odomate_requires_engineering, odomate_requires_team_planning

- **mrp.bom**: odomate_product_kind_id (Many2one odomate.product.kind, compute='_compute_odomate_product_kind_id', store=True)
  - Depends: product_id.product_tmpl_id.odomate_product_kind_id, product_tmpl_id.odomate_product_kind_id
  - Live link — no snapshot; used only for filtering and the counter on the kind's card

- **sale.order.line**: odomate_product_kind_id (Many2one odomate.product.kind, related='product_id.product_tmpl_id.odomate_product_kind_id', store=True, readonly) — live link until confirmation
  - odomate_product_kind_snapshot_id (Many2one odomate.product.kind, copy=False) — snapshot, frozen on the order's action_confirm()

- **mrp.production**: odomate_product_kind_snapshot_id (Many2one odomate.product.kind, copy=False) — snapshot, set in create(): from sale_line_id.odomate_product_kind_snapshot_id, falling back to product_id.product_tmpl_id.odomate_product_kind_id at creation time if absent

### Business Rules
- **Gate 1 — SO confirmation**: in sale.order.action_confirm(), for every line that doesn't already have a snapshot — copy the current odomate_product_kind_id into odomate_product_kind_snapshot_id. Once frozen, it is never recomputed again, even if the order is reset to draft and re-confirmed.
- **Gate 2 — MO creation**: in mrp.production.create(), the snapshot is set once, by priority: the originating sale order line's snapshot → the product's current kind. Manual MOs with no linked SO always take the product's kind at creation time.
- **Snapshot immutability**: write() on odomate_product_kind_snapshot_id (sale.order.line, mrp.production) is allowed only for users in the "Product Kind Manager" group; for everyone else, attempting to change an already-frozen value raises a UserError, enforced through the ORM (not just the view — model-level enforcement is mandatory).
- **Group-dependent readonly in the view**: the snapshot field's readonly attribute depends on the group (groups= / attrs with role context), so the form never blocks what the model allows.
- **Archiving a kind**: blocked (ValidationError) if it has active descendants — regardless of role. Additionally blocked for non-managers if active products still use that kind (a manager may archive despite active products).
- **Uniqueness**: name/code unique within company_id — a DB unique constraint (models.Constraint) on (company_id, code); a separate partial unique index for global records (company_id IS NULL), since a plain unique constraint treats every NULL as distinct.
- **Recursion**: @api.constrains('parent_id') + _has_cycle() — forbids cycles in the tree.

### Views & UX
- Primary view — Hierarchy (Odoo 19 `<hierarchy>`, draggable folder view; `web_hierarchy` dependency in the manifest).
- Kanban: grouped by route_type, color-coded, with product counters.
- List/Form: complete_name as rec_name; form has the classification fields plus smart buttons (Products / BoMs / Sale Lines / Manufacturing Orders) navigating across the whole subtree (child_of).
- Search view: group by Parent / Route Type / Manufacturing Mode; filters "Requires Engineering", "Requires Team Planning", "Archived".
- product.template: new "Manufacturing Classification" section with a kind-picker field plus readonly derived attributes.
- sale.order.line: the kind column is optional (optional="hide") in the order-lines list; the snapshot field is technical, visible in the line's detail / a separate tab.
- mrp.production: snapshot field in the "Classification" group, readonly for everyone except the manager (via a groups-dependent modifier).
- mrp.bom: kind field as a readonly column/filter.
- OWL complexity: none — standard views plus the built-in `<hierarchy>`, no custom client action.

### Security
- Groups: group_odomate_product_kind_user (browse the kind tree), group_odomate_product_kind_manager "Product Kind Manager" (implied_ids ⊇ user; full CRUD on the catalog plus the right to change frozen snapshots).
- ir.model.access.csv: rows for odomate.product.kind (user: read; manager: read/write/create/unlink). Other models (product.template, sale.order.line, mrp.production, mrp.bom) inherit their base modules' existing access rights — the new fields need no separate access rows.
- Record rule (global, not group-bound): `['|', ('company_id','=',False), ('company_id','in', company_ids)]` — a multi-company user sees global kinds plus the kinds of every company they're allowed into, at the same time.
- Menu: Manufacturing → Configuration → Product Kinds (Hierarchy view by default).

### Demo Data
- odomate.product.kind: 8–10 records, 2–3 tree levels, covering every route_type: "Finished Goods" (sold, root) → "Furniture", "Electronics" (manufactured); "Components" → "Fasteners" (component); "Services" (service); "Transport" (transport); "Other" (other). Varied manufacturing_mode and engineering/planning flags for variety.
- product.template: 10–15 products distributed across kinds, including several with a filled bill of materials (BoM) for manufactured kinds.
- sale.order: several orders — some in draft (kind is live, no snapshot yet), some confirmed (snapshot frozen).
- mrp.production: one MO created from a confirmed sale order line (snapshot inherited from the SO line's snapshot), one created manually (snapshot from the product's current kind).
- Reclassification scenario: one product whose kind was changed AFTER its SO line was confirmed / its MO was created — demonstrates that historical documents keep the old snapshot, while the product and its BoM (live link) already show the new kind.

### Constraints & Notes
- The BoM field's technical name is normalized to odomate_product_kind_id (a single `odomate_` prefix used consistently across the module).
- The `web_hierarchy` dependency is mandatory in the manifest because of the `<hierarchy>` view usage.
- Model-level protection of the snapshot is mandatory (not just view-readonly) — otherwise a direct API/import write bypasses the restriction.
- The partial unique index for global kinds must be accounted for during module migration/upgrade.
