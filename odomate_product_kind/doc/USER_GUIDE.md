# Product Kind — Manufacturing Classification — User Guide

## 1. Overview

**Product Kind** (`odomate.product.kind`) is a hierarchical, production-oriented
classification of your products. Unlike the standard product category, a Product
Kind carries manufacturing semantics (route type, manufacturing mode,
engineering / team-planning flags) and — crucially — it **freezes a snapshot**
onto sale order lines and manufacturing orders at the moment they are confirmed
or created.

The result: a product can be reclassified at any time, and the change flows
immediately to the product and its bill of materials (a *live link*), while every
already-confirmed sales and manufacturing document keeps the kind it had when it
was confirmed (a *frozen snapshot*).

## 2. Installation

1. Copy the `odomate_product_kind` folder into your Odoo addons path.
2. This module depends on **Manufacturing** (`mrp`), **Sales** (`sale`) and the
   **Hierarchy view** (`web_hierarchy`) — install those first (Odoo does this
   automatically).
3. Update the apps list and install **Product Kind — Manufacturing
   Classification**.

## 3. Security & Roles

| Group | Technical name | Rights |
|-------|----------------|--------|
| Product Kind / User | `group_odomate_product_kind_user` | Browse the kind tree, see the classification on documents |
| Product Kind / Manager | `group_odomate_product_kind_manager` | Full CRUD on the catalog **and** the exclusive right to change frozen snapshots |

The Manager group implies the User group. A global multi-company record rule lets
a user see **global** (company-less) kinds plus the kinds of **every company they
are allowed into**, at the same time.

- **Works out of the box.** Installing the module automatically grants the
  Administrator the *Product Kind / Manager* group, so the **Product Kinds**
  menu and full access are available immediately — no manual group setup needed.
- **Every internal user can read the catalog.** Besides the two dedicated
  groups above, all internal users (the base *Internal User* group) get
  read-only access to `odomate.product.kind`. This is what lets any user open a
  product, sale order line, BoM or manufacturing order that shows a Product
  Kind without hitting an access-rights error — even if they were never added
  to the Product Kind / User group. Only creating, editing, or deleting kinds
  still requires the dedicated groups.

## 4. The Product Kind catalog

Open **Manufacturing ▸ Configuration ▸ Product Kinds**.

The default view is a **Hierarchy** (draggable folder view). You can also switch to:

- **List** — flat, sortable, with the full path in `complete_name`. Drag rows by
  the sequence handle to reorder — the order is reflected in this list, in
  Kanban, and in the Hierarchy view.
- **Kanban** — grouped by parent (hierarchy) by default, with a product counter
  per card. Switch the Group By to Route Type or Manufacturing Mode any time.
- **Form** — the classification detail plus four smart buttons. The nested
  **Sub Kinds** tab has its own drag handle for reordering children.

### Fields

| Field | Meaning |
|-------|---------|
| `name` | Display name. Unique among the **siblings of the same parent**, within the same company/global scope (see §7) — the same name can be reused under a different parent. |
| `code` | Short business code. Unique within a company, and separately among global kinds (see §7). |
| `sequence_code` | Short code (e.g. `PRD`, `SF`, `CMP`) reserved for **automatic numbering** of ECOs, BoMs and products — distinct from `code`, unique within a company/global scope the same way. |
| `color` | Color-picker used for visual coding of the kind in Kanban and the Hierarchy view. |
| `description` | Free-text description of the kind. |
| `complete_name` | Auto-computed path, e.g. `Finished Goods / Furniture`. |
| `route_type` | Sold / Manufactured / Semi-Finished / Component / Service / Transport / Other. |
| `manufacturing_mode` | Inherit / Make to Order / Make to Stock / Manual / Disabled. |
| `requires_engineering`, `requires_team_planning` | Planning flags. |
| `parent_id` / `child_ids` | Tree structure (`_parent_store`). |
| `company_id` | Leave empty for a **global** kind shared by all companies. |

### Smart buttons

Each button counts records across the **whole subtree** (using `child_of`), so a
root kind shows the totals of all its descendants. Counts include **archived**
kinds, products, BoMs, sale lines and manufacturing orders, so the numbers stay
stable and don't drop just because something in the subtree was archived:

- **Products** — product templates with this kind.
- **BoMs** — bills of materials whose product carries this kind.
- **Sale Lines** — sale order lines classified here (live link).
- **Manufacturing** — manufacturing orders whose **snapshot** falls in this subtree.

## 5. Classifying products

On any product **Template** (**Inventory / Sales ▸ Products ▸ Products**), open
the **Product Kind** tab to find the **Product Kind** field. Selecting a kind
reveals four read-only derived attributes on the same tab — Route Type,
Manufacturing Mode, Requires Engineering, Requires Team Planning — mirrored
from the kind so you can see the production policy without opening the
catalog.

Both the Products list/search and the **Bill of Materials** list/search offer
a **Group By: Product Kind** filter, so you can cluster products or BoMs by
classification without opening the Product Kind catalog itself.

The field is also available from the **Sales** app's **Product Variant** form
(**Sales ▸ Products ▸ Product Variants**), right after the product category.
Product Kind is a **template-level** attribute — every variant of the same
template shares one value. Setting or changing it from a variant updates the
template immediately, and the new value is reflected on every sibling variant
and on the Template form; there is no separate per-variant kind. Editability
follows the same rule everywhere it appears: any user with write access to
the product can set it, with no extra Product Kind group required.

Both the **Product Template list** and the **Product Variant list**
(Sales ▸ Products) also offer Product Kind as an optional column — enable it
from the column picker (⊕ icon) if it isn't shown by default.

The product ↔ kind link and the **bill of materials** link are always **live**:
change the product's kind and both update immediately.

## 6. The snapshot chain (product → sale → manufacturing)

This is the heart of the module.

1. **On a quotation (draft)** — a sale order line shows `Product Kind` as a live,
   read-only reflection of the product's current kind. No snapshot yet.
2. **Gate 1 — confirming the sale order** — `action_confirm()` copies the current
   kind into `Product Kind (Snapshot)` on every line that doesn't already have one.
   Once frozen it is **never** recomputed, even if the order is reset to draft and
   re-confirmed.
3. **Gate 2 — creating a manufacturing order** — the snapshot is set once, by
   priority: originating **sale order line snapshot** → otherwise the **product's
   current kind**. A manual MO with no linked sale order always takes the product's
   kind at creation time.

A *Product Kind Manager* can correct an already-frozen snapshot directly from
the sale order line or the manufacturing order form — the snapshot field is
editable for managers and stays read-only for every other user, on both
documents.

Both the sale order line and the manufacturing order also offer a read-only
**Route Type (Snapshot)** column/field — a quick-reference view of the frozen
kind's route type, so you can see it without opening the Product Kind record.

### Worked example

- "Modular Shelf" is classified **Furniture**.
- Sale order **S00042** is confirmed → its line snapshot freezes to **Furniture**.
- A manufacturing order is created → its snapshot freezes to **Furniture**.
- Later, someone reclassifies "Modular Shelf" to **Semi-Finished**.
- **Result:** the product and its BoM now show **Semi-Finished** (live), while
  S00042's line and the manufacturing order still show **Furniture** (frozen).
  Your production history stays truthful.

## 7. Sales Analysis reporting

Product Kind and Route Type are available as **Group By** and search filter
dimensions on **Sales ▸ Reporting ▸ Sales** (the Sales Analysis pivot / graph
/ list).

- Open the report, click the search bar's dropdown arrow, and look under
  **Group By** for **Product Kind** and **Route Type** — or type either name
  directly into the search bar to filter.
- The value shown follows the same **snapshot-first, live-fallback** rule as
  everywhere else in the module: a line from a **confirmed** order reports
  under the kind that was **frozen at confirmation** (matching what the sale
  order line itself shows), while a **draft/quotation** line — which has no
  snapshot yet — reports under the product's **current** kind.
- A line whose product carries no Product Kind at all groups under "None" for
  both dimensions.

### Worked example

Continuing the "Modular Shelf" example from §6: after S00042 is confirmed and
the product is later reclassified from **Furniture** to **Semi-Finished**,
the Sales Analysis report for that period still shows S00042's line under
**Furniture** — it reports the frozen snapshot, not the product's current
classification. A brand-new quotation for the same (now reclassified) product
reports under **Semi-Finished**, since it has no snapshot yet.

## 8. Business rules & guarantees

- **Snapshot immutability (model level).** Once a snapshot is set, only a *Product
  Kind Manager* can change it. Any other user attempting to change it — even
  through direct API/import, not just the form — gets a `UserError`. The form's
  snapshot field is read-only for everyone except managers, who can edit it
  in place on the sale order line or manufacturing order form (see §6).
- **Archiving.** A kind cannot be archived while it has **active sub kinds**
  (blocked for everyone). Additionally, non-managers cannot archive a kind while
  **active products** still use it; a manager may.
- **Deletion is protected.** Deleting a Product Kind that still has sub kinds is
  blocked with a clear error ("Cannot delete Product Kind '...' because it still
  has N sub kind(s). Delete or reparent them first."). Only a **leaf** kind (no
  children) can be deleted — deleting a parent no longer silently cascades and
  wipes its whole subtree.
- **Uniqueness.** `code` and `sequence_code` are each unique within a company,
  and separately among global (company-less) kinds. `name` is unique among the
  **children of the same parent** (within the same company/global scope) —
  not company-wide — so the same name (e.g. "Metal") can exist under different
  parents, just not twice under the same one. Global kinds get their own
  dedicated partial unique indexes throughout, because SQL otherwise treats
  every `NULL` company/parent as distinct. Creating or renaming a kind into a
  conflict raises a clear, translated error naming the exact duplicate —
  never a raw database error — before the record is ever saved; the database
  indexes remain underneath as a concurrency-safe backstop.
- **No cycles.** The parent relationship is validated against recursion.

## 9. Views reference

| Model | Where the field appears |
|-------|-------------------------|
| `product.template` | Form: "Product Kind" tab with the field + derived attributes. List (Sales ▸ Products ▸ Products): optional column. Search: "Group By: Product Kind" filter. |
| `product.product` | Form (Sales ▸ Products ▸ Product Variants): "Product Kind" near the product category — same template-level value as the Template form, editable by the same users. List: optional column. |
| `sale.order.line` | Optional (`optional="hide"`) Product Kind + snapshot + Route Type (Snapshot) columns — snapshot editable only for a Product Kind Manager |
| `mrp.production` | Snapshot + read-only Route Type (Snapshot) in the classification area — snapshot editable only for a Product Kind Manager, read-only for everyone else |
| `mrp.bom` | Read-only Product Kind column (live). Search: "Group By: Product Kind" filter. |
| `sale.report` (Sales ▸ Reporting ▸ Sales) | Product Kind + Route Type as search fields and "Group By" filters (snapshot-first, live-fallback — see §7). Read-only, like the rest of the report. |

## 10. Limitations

- The manufacturing-order snapshot inherits from a sale order line only when your
  installation links MOs to sale lines (a `sale_line_id` field on
  `mrp.production`). Without that bridge, every MO snapshots the product's current
  kind at creation; the linkage is detected defensively at runtime.
- The `manufacturing_mode` field records intent (Make to Order / Make to Stock /
  …) for reporting and downstream automation; this module does not itself alter
  Odoo's procurement routes.
- Smart-button counters are computed on read (not stored) and reflect the current
  database state each time the form is opened.
- The Sales Analysis "Group By: Product Kind / Route Type" filters are added to
  whichever search view Odoo currently uses for `sale.report` (found
  dynamically, since that view's technical ID isn't stable across Odoo
  versions). This patch is **self-healing**: it is rebuilt from scratch on
  every install *and* every subsequent module upgrade, so it repairs itself
  automatically if it was ever left stale or orphaned (for example by an
  interrupted or older uninstall) — you never need to edit the database by
  hand. If Sales ▸ Reporting ever throws a view error referencing an
  `odomate_*` field, upgrading this module (Apps ▸ Product Kind — Manufacturing
  Classification ▸ Upgrade) resolves it. Uninstalling the module also cleanly
  removes this patch, so it never leaves a leftover reference behind for the
  next install.
