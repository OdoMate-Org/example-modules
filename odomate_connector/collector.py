"""Read-only collectors gathering raw structural facts from an Odoo env.

Everything here READS (ORM + one pg_class query) and returns plain dicts.
Redaction, classification and assembly live in snapshot_lib (pure stdlib) so
they stay unit-testable outside Odoo. Do not filter/redact here beyond the
config-param allowlist pre-fetch — snapshot_lib is the authority.

Why every read is ``sudo()``
----------------------------

The snapshot must describe the database as it *is*, not as the acting user is
permitted to see it: a record rule hiding some models would produce a snapshot
that quietly misrepresents the environment, which is worse than no snapshot.

This is safe because of what is read and who can trigger it:

* Only **structural metadata** is read — the registry (``ir.model``,
  ``ir.model.fields``, ``ir.ui.view``, ``ir.module.module``, ``res.groups``),
  an allowlisted slice of ``ir.config_parameter``, and row-count estimates from
  PostgreSQL statistics. No business table is ever queried, so elevated reads
  cannot expose records to anyone.
* The only entry point is the export wizard, which is restricted to
  ``base.group_system`` twice over: by ``ir.model.access.csv`` and by an
  explicit ``has_group`` check in ``action_generate``. A user holding that group
  already administers the database and can read all of this directly.
* Nothing is written, and nothing leaves the process — the caller receives a
  file to inspect.
"""

import os
from collections import defaultdict

from odoo import release
from odoo.modules.module import get_module_path

from .snapshot_lib import CONFIG_PARAM_ALLOWLIST

# xmlid "modules" that mean "created in the database", not "shipped by a module"
NON_MODULE_XMLID_MODULES = ("__export__", "__cloc_exclude__", "studio_customization")


def _core_addons_dir():
    """Directory holding the Odoo distribution's own addons.

    Located via ``base``, which is by definition part of the distribution, so
    this stays correct however Odoo was installed (package, source, container).
    """
    import odoo.addons.base

    return os.path.realpath(os.path.dirname(os.path.dirname(odoo.addons.base.__file__)))


def _module_location(name, core_dir):
    """Where a module lives: ``("core"|"external", addons_root_name)``.

    ``core``/``external`` alone cannot tell an in-house module from a vendor's —
    both sit outside the distribution. The *addons root* can: a site that keeps
    its own code in ``/opt/client/addons`` beside ``/opt/oca/addons`` becomes
    separable by grouping on this value, and a deployment that flattens
    everything into one directory honestly reports one group rather than
    implying a distinction it cannot make.

    Only the directory's **name** is exported, never the full path — the path
    can carry a company or user name, and this is meant to group modules, not
    to describe someone's filesystem.

    Both values are None when the path cannot be resolved, which is the case for
    a module imported straight into the database.
    """
    try:
        path = get_module_path(name, display_warning=False)
    except Exception:  # noqa: BLE001 - provenance must never break the export
        return None, None
    if not path:
        return None, None
    path = os.path.realpath(path)
    location = "core" if path.startswith(core_dir + os.sep) else "external"
    return location, os.path.basename(os.path.dirname(path)) or None


def collect(env):
    """Return the raw dict consumed by snapshot_lib.build_snapshot()."""
    models = _models(env)
    return {
        "instance": _instance(env),
        "modules": _modules(env),
        "models": models,
        "views": _views(env),
        "settings": _settings(env),
        "config_params": _config_params(env),
        "groups": _groups(env),
        "automations": _automations(env),
        "record_counts": _record_counts(env, models),
    }


def _instance(env):
    icp = env["ir.config_parameter"].sudo()
    return {
        "odoo_version": f"{release.version_info[0]}.{release.version_info[1]}",
        "db_uuid": icp.get_param("database.uuid") or "",
        "languages": [code for code, _name in env["res.lang"].get_installed()],
        "multi_company": env["res.company"].sudo().search_count([]) > 1,
    }


def _modules(env):
    """Installed modules with enough provenance to fetch their source again.

    All of these come from the module's own manifest — public metadata, no
    business data. They exist so a replica environment can be rebuilt:

    * ``website`` is the source of truth for OCA, whose convention is that it
      holds the exact repository (``https://github.com/OCA/purchase-workflow``),
      making resolution a clone rather than a guess.
    * ``license`` decides what may legally be installed into a sandbox.
    * ``url`` and ``published_version`` are set by Odoo's Apps Store download
      path, so they are the only hint that a module came from the store rather
      than from a repository.
    """
    Module = env["ir.module.module"].sudo()
    fields = [
        "name",
        "latest_version",
        "published_version",
        "author",
        "website",
        "url",
        "license",
        "auto_install",
    ]
    # `imported` is contributed by base_import_module, so it only exists when
    # that module is installed. Its absence means nothing was DB-imported.
    has_imported = "imported" in Module._fields
    if has_imported:
        fields.append("imported")

    rows = Module.search_read([("state", "=", "installed")], fields)
    core_dir = _core_addons_dir()
    out = []
    for r in rows:
        location, addons_root = _module_location(r["name"], core_dir)
        out.append(
            {
                "name": r["name"],
                "installed_version": r["latest_version"] or "",
                "published_version": r["published_version"] or "",
                "author": r["author"] or "",
                "website": r["website"] or "",
                "url": r["url"] or "",
                "license": r["license"] or "",
                "auto_install": bool(r["auto_install"]),
                # Filesystem truth, which outranks whatever the manifest claims.
                "location": location,
                "addons_root": addons_root,
                "imported": bool(r.get("imported")) if has_imported else False,
            }
        )
    return out


def _models(env):
    selections = defaultdict(list)
    sel_rows = (
        env["ir.model.fields.selection"]
        .sudo()
        .search_read([], ["field_id", "value", "name"], order="field_id, sequence, id")
    )
    for s in sel_rows:
        selections[s["field_id"][0]].append([s["value"], s["name"]])

    fields_by_model = defaultdict(list)
    field_rows = (
        env["ir.model.fields"]
        .sudo()
        .search_read(
            [],
            [
                "model",
                "name",
                "ttype",
                "relation",
                "required",
                "readonly",
                "store",
                "related",
                "compute",
                "state",
            ],
        )
    )
    for f in field_rows:
        fields_by_model[f["model"]].append(
            {
                "name": f["name"],
                "ttype": f["ttype"],
                "selection": selections.get(f["id"]) or None,
                "relation": f["relation"] or None,
                "required": bool(f["required"]),
                # A stored-computed field cannot be written to, and an automation
                # trigger placed on one never fires. Both are silent failures
                # unless the generator can see these three flags.
                "readonly": bool(f["readonly"]),
                "store": bool(f["store"]),
                "computed": bool(f["compute"]),
                "related": f["related"] or None,
                "custom": f["state"] == "manual",
            }
        )

    model_rows = env["ir.model"].sudo().search_read([], ["model", "state", "transient"])
    out = []
    for m in model_rows:
        name = m["model"]
        owner = _defining_module(env, name)
        out.append(
            {
                "model": name,
                "custom": m["state"] == "manual",
                "transient": bool(m["transient"]),
                "module": owner,
                # Odoo's own convention for a model's external id.
                "xmlid": "%s.model_%s" % (owner, name.replace(".", "_")) if owner else None,
                "fields": _merge_registry_flags(env, name, fields_by_model.get(name, [])),
            }
        )
    return out


def _defining_module(env, model_name):
    """The module that *defines* a model, not one that merely inherits it.

    ``ir.model.data`` holds a row per module that touches the model, so reading
    xmlids gives an arbitrary inheritor — ``res.partner`` resolves to ``account``
    on an accounting install. ``_original_module`` is the registry's record of
    who declared it, which is what ``depends`` and ``ref=`` actually need.
    """
    try:
        return env[model_name]._original_module or None
    except Exception:  # noqa: BLE001 - a stale ir.model row must not break the export
        return None


def _merge_registry_flags(env, model_name, field_dicts):
    """Overlay store/computed/related/readonly from the registry.

    ``ir.model.fields.compute`` only holds *Studio* compute code; a Python
    ``@api.depends`` field leaves that column empty, so trusting it reports every
    core computed field as a plain stored column. The registry knows the truth.
    """
    try:
        registry_fields = env[model_name]._fields
    except Exception:  # noqa: BLE001
        return field_dicts
    for f in field_dicts:
        rf = registry_fields.get(f["name"])
        if rf is None:
            continue
        related = getattr(rf, "related", None)
        if isinstance(related, (list, tuple)):
            related = ".".join(related)
        f["store"] = bool(rf.store)
        f["computed"] = bool(rf.compute)
        f["related"] = related or None
        f["readonly"] = bool(rf.readonly)
    return field_dicts


def _xmlid_map(env, model):
    """res_id -> 'module.name' for all external ids of ``model``."""
    rows = (
        env["ir.model.data"]
        .sudo()
        .search_read([("model", "=", model)], ["module", "name", "res_id"])
    )
    out = {}
    for r in rows:
        out.setdefault(r["res_id"], f"{r['module']}.{r['name']}")
    return out


def _is_module_xmlid(xmlid):
    return bool(xmlid) and xmlid.split(".", 1)[0] not in NON_MODULE_XMLID_MODULES


def _views(env):
    """Customized/inherited views only: hand-made, Studio-made, or arch-edited."""
    xmlids = _xmlid_map(env, "ir.ui.view")
    out = []
    views = env["ir.ui.view"].sudo().search([("model", "!=", False), ("type", "!=", "qweb")])
    for v in views:
        custom = v.arch_updated or not _is_module_xmlid(xmlids.get(v.id))
        if not custom:
            continue
        out.append(
            {
                "model": v.model,
                "type": v.type,
                "inherit_id_xmlid": xmlids.get(v.inherit_id.id) if v.inherit_id else None,
                "arch": v.arch,
            }
        )
    return out


def _settings(env):
    """Boolean/selection res.config.settings values — structural toggles only.

    Deliberately NEVER Char/Text settings: core modules store secrets there
    (e.g. google_recaptcha's recaptcha_private_key is a Char settings field
    backed by ir.config_parameter). Secret-NAMED boolean/selection fields are
    additionally dropped by snapshot_lib.redact_settings.

    Values are read off an **instantiated** record rather than ``default_get``.
    ``default_get`` resolves only ``group_*``, ``module_*`` and explicitly
    defaulted fields — it does not resolve fields ``related`` through
    ``company_id``, which is where much of the real policy lives. Measured on a
    sale/account/stock/purchase install: 153 boolean and selection fields exist,
    ``default_get`` returns 89, and an instantiated record resolves all 153.
    Among the 64 it misses, 26 are company-related, including
    ``po_double_validation`` ('one_step') and ``po_lock`` ('edit') — approval
    policy a generated module has to respect.

    The declared field type is still not trustworthy, so each value is checked
    against it: ``is_installed_<module>`` fields are *declared* boolean but
    resolve to the module's **integer id** (e.g. ``505``), which differs between
    any two databases and reports a permanent false mismatch against a replica.

    The Char/Text exclusion is what keeps secrets out; it is a separate filter on
    field *type* and is unaffected by where the value is read from.
    """
    settings = env["res.config.settings"].sudo()
    names = sorted(
        name for name, f in settings._fields.items() if f.type in ("boolean", "selection")
    )
    record = settings.create({})
    out = {}
    for name in names:
        try:
            value = getattr(record, name)
        except Exception:  # noqa: BLE001 - one unreadable setting must not lose the export
            continue
        expected = bool if settings._fields[name].type == "boolean" else str
        # `False` is how Odoo spells "unset" for a selection; keep it, it is
        # real configuration. `None` and wrong-typed values are not.
        if value is False or isinstance(value, expected):
            out[name] = value
    return out


def _config_params(env):
    rows = (
        env["ir.config_parameter"]
        .sudo()
        .search_read([("key", "in", list(CONFIG_PARAM_ALLOWLIST))], ["key", "value"])
    )
    return {r["key"]: r["value"] for r in rows}


def _groups(env):
    """Security groups with the number of users holding each.

    ``all_users_count`` is implied-inclusive on purpose: a user granted
    "Sales/Administrator" holds the salesman group only by implication, so the
    explicit membership count (``user_ids``) reads 0 for groups that are very
    much in use. Odoo 19 only — 17/18 name this field differently.
    """
    xmlids = _xmlid_map(env, "res.groups")
    out = []
    for g in env["res.groups"].sudo().search([]):
        xmlid = xmlids.get(g.id)
        out.append(
            {
                "xmlid": xmlid if _is_module_xmlid(xmlid) else None,
                "name": g.display_name,
                "users_count": g.all_users_count,
            }
        )
    return out


def _automations(env):
    """Automated actions: what fires, on what, and under what condition.

    ``filter_domain`` is the condition, not the code — an automation on
    ``project.task.checklist.line`` that only acts when ``state = 'done'``
    behaves nothing like one that fires on every write, and a generator that
    cannot see the difference will duplicate or contradict it. Server-action
    code bodies remain excluded.
    """
    if "base.automation" not in env:
        return []
    out = []
    for a in env["base.automation"].sudo().search([]):
        out.append(
            {
                "name": a.name,
                "model": a.model_id.model,
                "trigger": a.trigger,
                "filter_domain": a.filter_domain or None,
                "filter_pre_domain": a.filter_pre_domain or None,
                "active": bool(a.active),
            }
        )
    return out


def _record_counts(env, models):
    """pg_class reltuples estimates — instant, and never touches row data.

    PostgreSQL 14+ stores ``reltuples = -1`` to mean *never analyzed*, which is
    "unknown", not "empty". Clamping that to 0 would assert that a table holding
    real data is empty — a confident lie is worse than an absent number, because
    a consumer reading it concludes the customer does no manufacturing, raises no
    purchase requests, and so on. Unknown is therefore exported as ``null``.

    ANALYZE would produce real numbers but writes statistics and scans tables on
    a customer's production database, which an export button has no business
    doing; ``count(*)`` across every model risks sequential scans on a large
    system. Reporting the uncertainty is the honest option and costs nothing.
    """
    tables = {m["model"]: m["model"].replace(".", "_") for m in models if not m["transient"]}
    env.cr.execute(
        "SELECT relname, reltuples::bigint FROM pg_class WHERE relkind = 'r' AND relname = ANY(%s)",
        (list(tables.values()),),
    )
    by_table = dict(env.cr.fetchall())
    out = {}
    for model, table in tables.items():
        if table not in by_table:
            continue
        estimate = int(by_table[table])
        out[model] = None if estimate < 0 else estimate
    return out
