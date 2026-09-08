=================================
Employee Document Expiry Tracking
=================================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge2| image:: https://img.shields.io/badge/odoo-19.0-brightgreen.png
    :alt: Odoo 19.0

|badge1| |badge2|

Track expiring employee documents — work permits, licences, certificates — with
configurable chasing patterns, renewal that preserves history, and a daily
scheduled action that expires and chases without anyone having to remember.

Each document type carries a chasing pattern (on expiry, once N days before,
daily before, or daily after) and a reminder delay. The daily cron expires
documents whose date has passed, then emails the employee and puts a To-Do on
their manager for every document whose chasing pattern says today is a chase
day. Renewal moves the old dates and the old scans into a history row and gives
the document new ones, so nothing is overwritten and nothing is duplicated.

Features
========

* Four chasing patterns per document type, with a configurable reminder delay
* Daily scheduled action: automatic expiry, then edge-correct notification
* Reminder email to the employee plus a manager To-Do dated on the expiry date
* Renewal wizard that re-points the superseded scans onto a history row
* One valid document per employee and type, enforced in Python and by a
  partial unique index in the database
* "Days remaining" wording (``Expired 12 days`` / ``Today`` / ``Tomorrow`` /
  a plain number), searchable through a date-range filter
* Employees see their own documents read-only; HR sees everything
* Multi-company record rules on documents and renewal history
* Forms & Templates: blank paperwork anyone can download
* Ukrainian translation included

Installation
============

#. Copy ``odomate_hr_documents`` into your Odoo addons path.
#. Restart the Odoo service.
#. Go to **Apps**, click **Update Apps List**.
#. Search for *Employee Document Expiry Tracking* and click **Install**.

Dependencies (``hr``, ``mail``) install automatically.

Configuration
=============

#. Go to **Employees → Employee Documents → Document Types** (HR managers).
#. Create one type per kind of document, setting its **Chasing Pattern** and
   **Reminder Days**.
#. Check **Settings → Technical → Scheduled Actions → Employee Documents:
   expire and chase** is active. It runs once a day.

Usage
=====

Record documents under **Employees → Employee Documents → Documents**, attach
the scan in the chatter, and press **Mark Valid**. Use **Renew** when a new
document arrives — the wizard keeps the old dates and scans as history.

Full documentation, including worked examples of all four chasing patterns and
the complete access matrix, is in ``doc/USER_GUIDE.md`` (English) and
``doc/USER_GUIDE.uk.md`` (Ukrainian).

Known limitations
=================

* No approval workflow, no blocking of payroll/leave/scheduling
* No employee self-service upload or renewal
* No OCR or data extraction from scans
* No escalation beyond one email and one manager To-Do
* No printable report
* ``identification_id`` / ``passport_id`` / ``work_permit_*`` on ``hr.employee``
  are deliberately left untouched

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
