# Publishing workflow (internal)

How a module gets into this repo and onto the Odoo Apps Store. Audience: OdoMate team.
The Notion task tracker is the state machine; this file is the recipe.

## 1. Selection rules

- **Team-selected specs only.** Never a beta user's module or spec — not even anonymized —
  without separate, explicit, written consent.
- Useful, non-confidential business scenario; real-looking, not a toy.
- Vary complexity across the repo so viewers can gauge the tool at multiple levels.

## 2. Security review (before any publish)

Reviewer works through the full checklist in the internal `apps-store-showcase-workflow`
doc. Minimum bar, per module:

- [ ] `ir.model.access.csv` covers every model; no over-broad `group_user` write/unlink
- [ ] Record rules for any multi-user/multi-company data isolation the spec implies
- [ ] No `sudo()` on user-triggered paths without a documented reason
- [ ] HTTP controllers (if any): `auth='user'` unless deliberately public; no open JSON
      endpoints leaking records
- [ ] No raw SQL string interpolation; ORM domains only
- [ ] No `eval` / `safe_eval` on user input
- [ ] No secrets, tokens, URLs to internal infra, or customer data anywhere (code, data
      files, tests, SPEC.md, git history)
- [ ] Demo/data XML doesn't modify core records beyond what the module owns
- [ ] Tests pass on a clean Odoo 19 Community install

## 3. Repo requirements per module

- Standard layout, top-level folder named with the technical name (no `odoo_` prefix)
- `SPEC.md` inside the module folder: the original business specification + a one-line
  note of generation date and OdoMate version/mode
- `static/description/icon.png` + `static/description/index.html` (+ banner image) — this
  becomes the Apps Store listing page
- `README.md` table in the repo root updated with the new module row

## 4. Manifest requirements (Apps Store scans these)

```python
{
    "name": "…",                      # no "Odoo" in the app name (trademark policy)
    "summary": "…",
    "version": "19.0.1.0.0",          # must start with the series: 19.0.x.y.z
    "category": "…",
    "author": "OdoMate",
    "website": "https://www.odomate.pro",
    "support": "support@odomate.pro",
    "license": "LGPL-3",          # generator default; AGPL-3 also store-accepted
    "depends": […],
    "installable": True,
    "images": ["static/description/banner.jpg"],   # the BANNER, never icon.png — the
                                                   # store stretches whatever is here
                                                   # into the big listing slot
}
```

Trademark: the app *name* must not lead with "Odoo" or imply it's an official Odoo
product; "… for Odoo" phrasing in the summary is fine.

**Tracked short link:** once a slug is registered for this module at
`odomate.pro/admin/listing-links`, point `website` at the tracked variant instead —
`"https://odomate.pro/m/<slug>?v=site"` — so the one link the Store leaves clickable
also carries attribution. Register the slug there *first*; the manifest field is a
same-origin redirect either way, so this is a same-day, one-line change per module.

## 5. Apps Store submission (Maryana's dashboard)

The Apps Store does not take uploads — it **scans a registered git repository**:

1. apps.odoo.com → login (registered account) → *Apps* → *Upload your app* / repository
   settings → add this repo's git URL (`https://github.com/OdoMate-Org/example-modules.git`
   — public, so no deploy key needed).
2. The store scans branches named after Odoo series (`19.0`) and lists every top-level
   module directory it finds as an app.
3. Each app is then published/unpublished individually from the dashboard. New pushes to
   `19.0` re-scan automatically (there can be a delay; a manual re-scan button exists in
   the dashboard).
4. Free apps: set no price. The listing page renders `static/description/index.html`.

## 6. Cadence

A stale repo reads worse than no repo: land a fresh example module every **4–6 weeks**
during beta (content calendar owns the reminder).

## 7. Repo hygiene

Commit messages carry no AI co-author/session trailers — plain project history
only. A `commit-msg` hook enforces it; enable once per clone:

```bash
git config core.hooksPath .githooks
```
