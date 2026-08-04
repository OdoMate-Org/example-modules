=================
OdoMate Connector
=================

.. |badge_license| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

|badge_license|

Exports a **redacted structural snapshot** of your Odoo database
(``odomate_context.json``) so `OdoMate <https://www.odomate.pro>`_ can generate
modules that fit your real environment — and test them against a replica of it.

Structural context, never your business records
===============================================

**Included**

* Installed modules, each classified as core / enterprise / OCA /
  third-party / custom, with the manifest provenance (website, licence,
  version) needed to fetch the same source again
* Models and fields, including Studio and ``x_`` customizations, with selection
  values and relations
* Views you have customized or inherited
* Configuration toggles and an allowlisted subset of system parameters
* Security groups and the number of users holding each
* Automated-action names and their models
* Per-model record **counts**

**Never included**

* Business records of any kind — no partner, employee or user data, no emails,
  no names
* Credentials, API keys, tokens or secret system parameters
* The raw database UUID (exported only as a SHA-256 hash)

Any key or value matching ``key|secret|token|password|api|dkim|private`` is
dropped, on top of an allowlist that decides what is considered at all. Only
boolean and selection settings are read — Odoo stores real secrets in *text*
settings fields, so those are never touched.

The module makes **no network calls**, stores nothing, and adds no third-party
Python dependencies. The output is plain, pretty-printed JSON: open it and see
exactly what would leave your system before you share it.

Usage
=====

#. Install the module (see below).
#. Go to **Settings ▸ Technical ▸ Export OdoMate Context**. The entry requires
   the *Settings* administration group.
#. Press **Generate snapshot**. You get a summary of what was collected and a
   download link for ``odomate_context.json``.
#. Review the file, then upload it in your OdoMate workspace.

Installation
============

Copy the ``odomate_connector`` folder into your addons path, update the apps
list, and install **OdoMate Connector**.

Targets Odoo 19, Community and Enterprise.

Size limits
===========

The snapshot is capped at roughly 5 MB. If a database would exceed that, the
export degrades in disclosed stages — first dropping customized view bodies
(keeping their structure), then the field lists of standard models that carry
no customizations. Whatever was dropped is recorded in the file's ``truncated``
list, so a consumer never has to guess whether it is complete.

Credits
=======

Authors
-------

* OdoMate

Maintainer
----------

This module is maintained by OdoMate — https://www.odomate.pro

For support: support@odomate.pro
