============================================
HR Notices, Announcements & Acknowledgements
============================================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge2| image:: https://img.shields.io/badge/Odoo-19.0-purple.png
    :alt: Odoo 19.0

|badge1| |badge2|

Publish HR announcements to a precisely targeted audience, track who
acknowledged them, and keep HR-only saved reminders over any date field on
employees, contract versions, applicants or time off. A systray counter shows
each user the announcements addressed to them that they have not yet
acknowledged.

Features
========

* Approval workflow: Draft, Waiting for Approval, Published, with Refused and
  Expired as terminal branches. Publishing is restricted to HR Administrators
  and enforced in the method, not only in the view.
* Audience targeting: everyone, selected employees, selected departments
  (exact match, no hierarchy walk), or selected job positions.
* Acknowledgement tracking with acknowledged count, audience size and a
  has-not-acknowledged list. Acknowledging is idempotent.
* Saved date reminders over a whitelist of HR models, with a live count of
  matching records evaluated as the calling user.
* Daily scheduled action that expires announcements past their display window.
* Multi-company record rules on every model, and field-level protection on the
  acknowledgement fields.
* Ukrainian translation included.

Installation
============

#. Copy ``odomate_hr_notices`` into your Odoo addons path.
#. Restart the Odoo service.
#. Activate developer mode and update the apps list.
#. Install *HR Notices* from the Apps menu.

Configuration
=============

#. Go to *Employees > Configuration > Announcement Categories* and create the
   categories you need.
#. Optionally, go to *Employees > Configuration > Date Reminders* to save the
   date questions your HR team asks regularly.

No new security groups are created. The module reuses ``base.group_user``,
``hr.group_hr_user`` and ``hr.group_hr_manager``.

Usage
=====

*Employees > Notices > All Announcements* to draft and publish.
*Employees > Notices > Announcements* shows each user the announcements
addressed to them.

Full documentation, including the audience rules and a field reference, is in
``doc/USER_GUIDE.md`` (English) and ``doc/USER_GUIDE.uk.md`` (Ukrainian).

Known limitations
=================

* "Acknowledged" records a button press only; it is not evidence that the
  announcement was read or understood.
* Department targeting is exact — parent departments do not cascade to their
  children.
* Reminders evaluate date conditions only; amount, state and status conditions
  are out of scope by design.

Credits
=======

Authors
-------

* OdoMate

Maintainers
-----------

This module is maintained by OdoMate.

* Website: https://odomate.pro
* Support: support@odomate.pro
