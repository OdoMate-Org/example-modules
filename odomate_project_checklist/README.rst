=======================
Project Task Checklists
=======================

.. |badge_license| image:: https://img.shields.io/badge/license-LGPL--3-blue.png
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

|badge_license|

Reusable, step-by-step checklists for Odoo Project tasks, with per-task
customization, live progress tracking, and auto-stamped start/end dates.

Define a checklist template once, attach it to any task, and let each task keep
its own independent, freely editable copy. A progress bar (cancelled steps
excluded) and self-managing Start/End dates keep everyone honest about where a
task really stands.

Features
========

* Reusable checklist **templates**, managed under Project → Configuration →
  Checklists, with drag-reorderable steps.
* One-click apply onto a task; the steps become an independent copy you can add
  to, delete, rename, and reorder.
* Inline **Start / Done / Cancel** buttons per step, with color-coded rows and
  an editable status field for corrections.
* Stored **progress** field that excludes cancelled steps, shown as a progress
  bar on the task form and in the task list.
* Automatic **Start Date** (first step started) and **End Date** (100% reached,
  self-clearing if progress drops).
* Confirmation **wizard** before replacing a checklist that already has
  progress.

Installation
============

#. Copy ``project_checklist`` into your addons path.
#. Update the Apps list in Developer Mode.
#. Install **Project Task Checklists**.

Depends on ``project``.

Configuration
=============

No configuration required. Optionally create your own templates under
**Project → Configuration → Checklists** (Project Manager rights required).

Bug Tracker
===========

Please report issues to support@odomate.pro.

Credits
=======

Authors
-------

* OdoMate

Maintainer
----------

This module is maintained by OdoMate — https://odomate.pro
