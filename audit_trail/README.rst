===========
Audit Trail
===========

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge2| image:: https://img.shields.io/badge/Odoo-19.0-875A7B.png
    :target: https://www.odoo.com
    :alt: Odoo 19.0

|badge1| |badge2|

A configurable audit trail that records who did what to which watched record,
with before/after field values, browsing and export activity, and session
context — without slowing down or bloating the rest of the system.

Watch settings are declared per model and per company. Nothing is recorded until
a rule is confirmed, and each rule chooses independently whether to record
creations, updates, deletions, exports and views. Models without an active rule
pay only a cached set-membership check.

Features
========

* **Watch rules per model, per company** — draft/active workflow, unique at the
  database level, with a message pointing at the existing rule on conflict.
* **Full or light detail** — full stores old *and* new values; light skips the
  extra read and stores new values only.
* **Deletion snapshots** — keep the field values of a record at the moment it was
  deleted, with excluded fields scrubbed out.
* **Export tracking** — records exactly which record ids left the system, with a
  button to reopen that precise set.
* **View tracking** — optional per-row read auditing for list views and record
  opens.
* **Exclusions** — excluded users produce no event at all; excluded fields never
  appear in recorded values or snapshots.
* **Working sessions** — events are grouped into per-user sessions with an
  inactivity timeout, and linked to the screen they came from.
* **Retention clean-up** — an opt-in scheduled job that deletes expired events in
  self-re-triggering batches.

Installation
============

#. Copy this module into your Odoo addons path.
#. Restart the Odoo server.
#. Go to **Apps**, click **Update Apps List**.
#. Search for **Audit Trail** and press **Install**.

Configuration
=============

#. Go to **Audit Trail → Configuration → Watch Rules** and create a rule for the
   model you want to watch.
#. Choose the detail level and tick the actions to record.
#. Optionally add excluded users and excluded fields.
#. Press **Confirm** — recording starts immediately.

Retention clean-up is off by default and can be enabled under
**Audit Trail → Configuration → Clean-up Settings**.

Usage
=====

Recorded events are available under **Audit Trail → Logs**, individual field
changes across every watched model under **Audit Trail → Field Changes**, and
per-user working sessions under **Audit Trail → Sessions**. Contact forms gain a
**View Logs** button for auditors.

Full documentation: ``doc/USER_GUIDE.md``.

Known limitations
=================

* No tamper-proofing — audit administrators may delete history.
* No approval, blocking, alerting, or dashboards; this module only records.
* View tracking generates one event per displayed row and is off by default.
* Read tracking is skipped on read-only database cursors (replica deployments).

Bug Tracker
===========

Please report issues to support@odomate.pro.

Credits
=======

Authors
-------

* OdoMate

Maintainers
-----------

This module is maintained by OdoMate — https://odomate.pro
