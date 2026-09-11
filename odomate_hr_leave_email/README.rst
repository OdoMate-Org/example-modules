==========================
Time Off Requests by Email
==========================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge2| image:: https://img.shields.io/badge/odoo-19.0-purple.png
    :alt: Odoo 19.0

|badge1| |badge2|

Publishes one email address that turns an incoming message into an ordinary
Time Off request (``hr.leave``) for the employee who sent it. Dates are read
from the body of the message in ``YYYY-MM-DD`` or ``DD/MM/YYYY`` format, the
request lands in Time Off like any other, and Odoo's normal approval flow takes
over from there.

Nothing is guessed. A message whose sender, dates or Time Off type cannot be
resolved is refused, recorded in the *Email Requests* log under
**Time Off / Reporting**, and answered with the accepted date formats. The mail
gateway is never allowed to fail on a bad message.

Features
========

* One shipped ``mail.alias`` pointing at ``hr.leave``, restricted to
  authenticated employees.
* Sender resolution against the user login, the user email and the employee's
  ``work_email``.
* Two accepted date formats, first date to second date, single date means one
  day off.
* A read-only *Email Requests* log — one row per message, colour-coded by
  outcome, with the refusal reason and a link to the created request.
* An explanatory reply to the sender on refusal, restating the accepted date
  formats.
* Detection of the missing ``mail.alias.domain`` case, surfaced on the settings
  screen instead of an unusable address.
* Multi-company record rule; unresolved senders stay visible to Time Off staff
  in every company.

Installation
============

#. Copy ``odomate_hr_leave_email`` into your addons path.
#. Restart the Odoo service.
#. Go to **Apps**, click **Update Apps List**, search for
   *Time Off Requests by Email* and click **Activate**.

``hr_holidays`` and ``mail`` are installed automatically if missing.

Configuration
=============

#. Set an alias domain under **Settings → General Settings → Discuss →
   Alias Domain**. Without one the address cannot receive anything, and the
   settings screen says so.
#. Configure an incoming mail server or a catch-all forwarded to Odoo.
#. Go to **Settings → Employees → Time Off Requests by Email** and switch
   *Requests by Email* on.
#. Choose the *Time Off Type for Email Requests*. A type that requires no
   allocation avoids balance failures.
#. Publish the address shown in *Time Off Email Address*.

Usage
=====

Employees write to the published address with the first and last day of their
absence in the body, for example ``2026-03-09 to 2026-03-13`` or
``09/03/2026 - 13/03/2026``. Time Off officers follow the outcome under
**Time Off → Reporting → Email Requests**.

Full documentation: ``doc/USER_GUIDE.md`` (English), ``doc/USER_GUIDE.uk.md``
(Ukrainian).

Known limitations
=================

* Whole days only — half days and hours are not supported.
* Only the first two dates in the body are used; the subject line is ignored.
* ``March 9th``, ``9 Mar 2026`` and US-order ``03/09/2026`` are not recognised.
* Approval, cancellation and allocation are not driven by email.
* One address for the whole database; no per-company or per-department address.

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
