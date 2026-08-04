"""Pure-stdlib snapshot logic for the OdoMate connector.

Everything that decides WHAT goes into odomate_context.json lives here so it
can be unit-tested without an Odoo runtime. MUST NOT import odoo or any
third-party package — this file ships inside the customer-installed module.
"""

import hashlib
import json
import re

SCHEMA_VERSION = 1
# 1.1.0 added module provenance (website/url/licence/published_version).
# 1.2.0 reports unknown record counts as null (was 0) and reads settings from
#       an instantiated record, recovering company-related policy fields.
# Consumers read this to tell whether a snapshot carries those fields.
CONNECTOR_VERSION = "1.2.0"
MAX_SNAPSHOT_BYTES = 5 * 1024 * 1024

# Spec: drop any config key/value matching these patterns (defense-in-depth on
# top of the allowlist).
SECRET_RE = re.compile(r"(key|secret|token|password|api|dkim|private)", re.IGNORECASE)


def redact_params(params: dict, allowlist: frozenset) -> dict:
    """Allowlist-first, then drop any key OR value matching SECRET_RE."""
    out = {}
    for key in sorted(allowlist):
        if key not in params:
            continue
        value = params[key]
        if SECRET_RE.search(key):
            continue
        if isinstance(value, str) and SECRET_RE.search(value):
            continue
        out[key] = value
    return out


def redact_settings(settings: dict) -> dict:
    """Drop settings whose field NAME matches the secret patterns."""
    return {k: v for k, v in settings.items() if not SECRET_RE.search(k)}


def hash_db_uuid(db_uuid: str) -> str:
    """Identity without identifying: sha256 of the raw database uuid."""
    return "sha256:" + hashlib.sha256((db_uuid or "").encode()).hexdigest()


def classify_module_source(author, website, license_) -> str:
    """core|enterprise|oca|thirdparty|custom, derived per spec from author/website/license.

    Order matters: enterprise modules are also authored by Odoo S.A., so the
    license check must come first.
    """
    author_l = (author or "").lower()
    website_l = (website or "").lower()
    if (license_ or "").startswith(("OEEL", "OPL")):
        return "enterprise"
    if "odoo community association" in author_l or "github.com/oca" in website_l:
        return "oca"
    if author_l.strip() in ("odoo s.a.", "odoo sa", "odoo"):
        return "core"
    if not author_l.strip() and not website_l.strip():
        return "custom"
    return "thirdparty"


# ir.config_parameter keys worth exporting. Allowlist-first: anything not
# listed here never leaves the database, whatever it contains.
#
# Every entry must survive SECRET_RE — a key matching it (e.g.
# "auth_signup.reset_password", which contains "password") is dropped by
# redact_params anyway, so listing it only misleads. Guarded by
# tests/test_build_snapshot.py::TestConfigParamAllowlist.
CONFIG_PARAM_ALLOWLIST = frozenset(
    {
        "auth_signup.invitation_scope",
        "base_setup.default_user_rights",
        "mail.restrict.template.rendering",
        "product.weight_in_lbs",
        "product.volume_in_cubic_feet",
        "web_editor.allow_inline_scripts",
    }
)


def build_snapshot(raw: dict, connector_version: str, generated_at: str) -> dict:
    """Assemble the redacted snapshot from the collector's raw dicts.

    Deterministic: same raw input → same output (all lists sorted). Never
    mutates ``raw``.
    """
    modules = sorted(
        (
            {
                "name": m["name"],
                "installed_version": m["installed_version"],
                # Store-known modules carry a published_version; repo-hosted
                # ones do not. Kept because it is the clearest signal of where
                # a module can be fetched from again.
                "published_version": m.get("published_version") or "",
                "source": classify_module_source(
                    m.get("author"), m.get("website"), m.get("license")
                ),
                "author": m.get("author") or "",
                # OCA puts the exact repository here, which turns rebuilding a
                # replica into a clone instead of a lookup.
                "website": m.get("website") or "",
                "url": m.get("url") or "",
                "license": m.get("license") or "",
                "auto_install": bool(m.get("auto_install")),
            }
            for m in raw["modules"]
        ),
        key=lambda m: m["name"],
    )
    edition = (
        "enterprise"
        if any((m.get("license") or "").startswith(("OEEL", "OPL")) for m in raw["modules"])
        else "community"
    )
    models = sorted(
        (
            {
                "model": m["model"],
                "custom": bool(m["custom"]),
                "fields": sorted((dict(f) for f in m["fields"]), key=lambda f: f["name"]),
            }
            for m in raw["models"]
            if not m.get("transient")
        ),
        key=lambda m: m["model"],
    )
    views = sorted(
        (
            {
                "model": v["model"],
                "type": v["type"],
                "inherit_id_xmlid": v.get("inherit_id_xmlid"),
                "custom": True,
                "arch": v.get("arch"),
            }
            for v in raw["views"]
        ),
        key=lambda v: (v["model"], v["type"], v["inherit_id_xmlid"] or ""),
    )
    groups = sorted(
        (
            {
                "xmlid": g.get("xmlid"),
                "name": g["name"],
                "custom": g.get("xmlid") is None,
                "users_count": int(g["users_count"]),
            }
            for g in raw["groups"]
        ),
        key=lambda g: (g["xmlid"] is None, g["xmlid"] or "", g["name"]),
    )
    instance = {
        "odoo_version": raw["instance"]["odoo_version"],
        "edition": edition,
        "db_uuid_hash": hash_db_uuid(raw["instance"].get("db_uuid") or ""),
        "languages": list(raw["instance"]["languages"]),
        "multi_company": bool(raw["instance"]["multi_company"]),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "connector_version": connector_version,
        "generated_at": generated_at,
        "instance": instance,
        "modules": modules,
        "models": models,
        "views": views,
        "settings": redact_settings(raw["settings"]),
        "config_params": redact_params(raw["config_params"], CONFIG_PARAM_ALLOWLIST),
        "groups": groups,
        "automations": sorted(
            (dict(a) for a in raw["automations"]), key=lambda a: (a["model"], a["name"])
        ),
        "record_counts": dict(raw["record_counts"]),
    }


def serialize(snapshot: dict) -> "tuple[str, list[str]]":
    """JSON-serialize with the hard size cap and staged, disclosed truncation.

    Stages (spec: ~5 MB cap):
      1. drop customized-view archs (keep the structural metadata),
      2. drop field lists of standard models that carry no custom fields.
    The applied stages are recorded in the payload's ``truncated`` list.
    """
    truncated = []
    snap = dict(snapshot)

    def dump() -> str:
        snap["truncated"] = list(truncated)
        return json.dumps(snap, ensure_ascii=False, sort_keys=True, indent=2)

    payload = dump()
    if len(payload.encode()) > MAX_SNAPSHOT_BYTES:
        truncated.append("view_archs")
        snap["views"] = [dict(v, arch=None) for v in snap["views"]]
        payload = dump()
    if len(payload.encode()) > MAX_SNAPSHOT_BYTES:
        truncated.append("standard_model_fields")
        snap["models"] = [
            m if m["custom"] or any(f["custom"] for f in m["fields"]) else dict(m, fields=[])
            for m in snap["models"]
        ]
        payload = dump()
    return payload, truncated
