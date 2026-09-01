#!/usr/bin/env python3
"""Build odomate_connector's listing page: shared render, then its own edits.

The connector is the one published module OdoMate did NOT generate — a person
wrote it. That single fact is why it cannot simply be rendered like the others:
the shared template states, in three separate places, that OdoMate generated
and tested the module you are looking at. On this page each of those is false,
and the showcase playbook calls this out as the mistake that "goes wrong
quietly", because the claim contradicts the module's own SPEC.md sitting in the
same repository.

So: render with the shared skill to get the current design, then re-apply the
connector's own truth on top. The skill itself is deliberately untouched —
teaching it a "first-party mode" would mean every future module carries a
branch that exists for exactly one page.

Run it from anywhere:
    python3 tools/build_connector_page.py

What it changes after the shared render, and why each one:

  1. Removes the disclosure box   — "Generated and automatically tested by
                                    OdoMate" is not true here.
  2. Removes the stats block      — no generation stats exist for a
                                    hand-written module (also just absent from
                                    content.json, so this is belt and braces).
  3. Rewrites the tests line      — the shared copy says "N of them for this
                                    module", which would credit OdoMate with
                                    tests a person wrote.
  4. Rewrites the beta block      — the playbook requires this page to point at
                                    the *generated* modules as evidence, never
                                    at itself.
  5. Retitles the doc card        — it links setup documentation on
                                    docs.odomate.pro, not a user-guide PDF.
  6. Adds the redaction-rules paragraph after the snapshot panels.

Everything else — identity band, CTA ribbon, tabs, section blocks, typography,
audience cards, video card, footer — is whatever the shared template currently
produces, which is the point: this page tracks the others' design for free.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MODULE = REPO / "odomate_connector"
PAGE = MODULE / "static" / "description" / "index.html"
CONTENT = MODULE / "static" / "description" / "content.json"
RENDER = Path.home() / "code" / "odomate-claude-skills" / "odomate-apps-store-page" / "scripts" / "render_page.py"

REDACTION_HTML = (
    '<p style="font-weight:500; font-size:16px; color:#27272a; line-height:1.6; '
    'margin:18px 0 0; text-align:left;">'
    "Two rules decide what leaves your database, and both live in one "
    "dependency-free file (<b>snapshot_lib.py</b>) so they can be reviewed on "
    "their own. First an <b>allowlist</b>: a system parameter is not even "
    "considered unless it is explicitly listed. Then a <b>pattern rule</b>: any "
    "key or value matching <b>key | secret | token | password | api | dkim | "
    "private</b> is dropped, including allowlisted ones. Only boolean and "
    "selection settings are read at all — Odoo core keeps real secrets in text "
    "settings fields, so that whole class is excluded by design rather than by "
    "filtering.</p>"
)

# Only the second paragraph changes. The shared early-beta paragraph above it is
# already true for this module, so it keeps tracking the shared copy — the less
# this file restates, the less there is to drift.
BETA_PARAGRAPH = (
    "OdoMate&#x27;s other modules on this store were generated from a written "
    "specification, not hand-written — each ships with its spec, its automated "
    "tests and a live demo you can click through. Look at one, then request early "
    "beta access: install this connector, export your snapshot, and generate a "
    "module against your own Odoo instead of a demo one. Full platform "
    'documentation: <a href="https://docs.odomate.pro" style="color:#047857; '
    'font-weight:700; text-decoration:none;">docs.odomate.pro</a>.'
)


def edit(html: str, name: str, pattern: str, replacement: str, flags=0) -> str:
    out, n = re.subn(pattern, replacement, html, flags=flags)
    if not n:
        sys.exit(
            f"connector patch '{name}' matched nothing. The shared template has "
            f"changed shape — re-read the rendered page and update this script "
            f"rather than shipping the page with a claim it shouldn't make."
        )
    print(f"  {name} ({n})")
    return out


def main():
    if not RENDER.exists():
        sys.exit(f"render_page.py not found at {RENDER}")
    subprocess.run(
        [sys.executable, str(RENDER), "--module-dir", str(MODULE), "--content", str(CONTENT)],
        check=True,
    )
    html = PAGE.read_text()
    print("connector-only edits:")

    # 1. the disclosure box — a false claim on a hand-written module
    #    Anchored on the sentence itself rather than on the box's styling, so a
    #    restyle of the template can't quietly leave the claim behind.
    html = edit(html, "remove disclosure box",
                r'\s*<div style="margin:24px 0 0[^"]*">\s*<img[^>]*info-circle[^>]*>'
                r'<span[^>]*>Generated and automatically tested by OdoMate\.[^<]*</span>\s*</div>',
                "", flags=re.S)

    # 2. a stats block should never exist here (content.json has no `stats`),
    #    but strip it if one ever slips in — the heading alone is a false claim
    if "built this module unattended" in html:
        html = edit(html, "remove stats block",
                    r'\s*<div style="margin:28px 0 0; background-color:#064e3b.*?</div>\s*</div>\s*</div>',
                    "", flags=re.S)
    else:
        print("  no stats block present (as expected)")

    # 3. don't credit OdoMate with tests a person wrote
    html = edit(html, "reword the automated-tests line",
                r"(<b style=\"color:#09090b;\">Automated tests</b><br>)[^<]*",
                r"\g<1>generated and run with every module OdoMate builds")

    # 4. "Inspect this module ... to try OdoMate on your own specification" offers
    #    THIS module as evidence of what OdoMate generates. It isn't. Point at the
    #    generated modules instead, which is what the playbook requires.
    html = edit(html, "connector beta paragraph",
                r"Inspect this module — the code, the tests, the demo — then request "
                r"early beta access to try OdoMate on your own specification\. Full "
                r'platform documentation: <a href="https://docs\.odomate\.pro"[^>]*>'
                r"docs\.odomate\.pro</a>\.",
                lambda m: BETA_PARAGRAPH)

    # 5. the doc card links setup docs, not a user-guide PDF
    html = edit(html, "doc card heading", r">Read the guide<", ">Set up environment context<")
    html = edit(html, "doc card body",
                r"The full user guide for this module, written in English\.",
                "How to install the connector, export your snapshot and upload it — "
                "step by step on docs.odomate.pro.")
    html = edit(html, "doc card User Guide title", r">User Guide<", ">Documentation<")
    html = edit(html, "doc card EN label",
                r'<span style="display:inline-block; min-width:34px; font-weight:700; color:#09090b; font-size:15px;">EN</span>',
                '<span style="display:inline-block; min-width:34px; font-weight:700; color:#09090b; font-size:15px;">Docs</span>')
    html = edit(html, "doc QR caption", r">EN guide<", ">Setup docs<")

    # 6. The CTA ribbon invites you to "inspect this one, then request access to
    #    try OdoMate on your own spec" — on a generated listing that chain reads
    #    "look at what OdoMate produced". Here it would offer hand-written code as
    #    evidence of generation, which the playbook rules out. Inspection is still
    #    the right invitation for this module, just for the opposite reason: you
    #    are installing it into your own database, so you should read it first.
    html = edit(html, "connector ribbon subtext",
                r"All we ask for is your feedback\. Inspect this one, then request "
                r"access to try OdoMate on your own spec\.",
                "It runs in your own database, so read it before you trust it — "
                "then request access to generate against your real Odoo.")

    # 7. the redaction rules belong with the snapshot panels
    html = edit(html, "redaction-rules paragraph",
                r"(?s)(What the snapshot contains.*?)(\n\s*<div style=\"padding:32px 0 0;\">\s*<h2[^>]*>Screenshots)",
                lambda m: m.group(1) + "\n    " + REDACTION_HTML + m.group(2))

    PAGE.write_text(html)
    print(f"\nwrote {PAGE} ({len(html)} bytes)")

    # the three claims that must never appear on this page
    for claim in ("Generated and automatically tested by OdoMate",
                  "built this module unattended",
                  "of them for this module"):
        if claim in html:
            sys.exit(f"FAILED: page still contains a claim it must not make: {claim!r}")
    print("verified: none of the three generated-module claims appear on this page")


if __name__ == "__main__":
    main()
