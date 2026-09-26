===========
Audit Trail
===========

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

|badge1|

Records who created, changed, deleted, exported or listed which watched record,
when, with field-level before/after values. Watching is configured per kind of
record and per company through Draft/Active watch rules, and old history can be
removed by a batch-limited scheduled clean-up that each company switches on
deliberately.

**Table of contents**

.. contents::
   :local:

Installation
============

Install **Audit Trail** from the Apps menu. It depends on ``base``, ``web``,
``base_setup`` and ``product``. System administrators automatically become
Audit Administrators.

Configuration
=============

#. Go to *Audit → Configuration → Rules*, create a rule, choose the kind of
   record, detail level (Full or Light) and the actions to record, then click
   *Confirm*.
#. Optionally go to *Audit → Configuration → Settings* and switch on
   *Remove Old History* with the number of months to keep.

Usage
=====

* *Audit → Logs*: recorded events with their field changes.
* *Audit → Log Lines*: flat list of every changed field.
* *Audit → Sessions*: working sessions and their events.
* *View Logs* button on Contacts, Bank Accounts and Price Lists.

See ``doc/USER_GUIDE.md`` for the full guide (also in Ukrainian and Polish).

Known issues / Roadmap
======================

* Only changes made through the ORM are recorded.
* The event company is the user's current company at change time.
* Binary and one-to-many fields are not compared.
* Audit Administrators can delete history (no tamper-proof sealing).

Credits
=======

Authors
-------

* OdoMate

Maintainers
-----------

This module is maintained by OdoMate — https://odomate.pro — support@odomate.pro
