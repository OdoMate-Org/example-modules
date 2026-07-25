===========================================
Product Kind — Manufacturing Classification
===========================================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

|badge1|

A hierarchical, production-oriented **Product Kind** classification that flows
from products through sales into manufacturing. Confirmed sale order lines and
manufacturing orders **freeze a snapshot** of the kind, so historical documents
stay accurate even after a product is reclassified — while products and their
bills of materials keep a live link to the current kind.

Features
========

* Draggable, multi-level Product Kind catalog (Hierarchy / List / Kanban / Form).
* Production semantics per kind: route type, manufacturing mode, engineering and
  team-planning flags.
* Live product ↔ kind ↔ bill-of-materials link.
* Snapshot freezing on sale order confirmation and manufacturing order creation.
* Model-level snapshot immutability (only a Product Kind Manager may change a
  frozen snapshot — enforced even against direct API/import writes).
* Subtree smart buttons: Products, BoMs, Sale Lines, Manufacturing Orders.
* Multi-company aware, with global (company-less) kinds and a dedicated partial
  unique index for their codes.
* Ukrainian translation included.

Installation
============

This module depends on ``mrp``, ``sale`` and ``web_hierarchy``. Install those
(Odoo resolves them automatically), then install *Product Kind — Manufacturing
Classification* from the Apps list.

Configuration
=============

Open **Manufacturing ▸ Configuration ▸ Product Kinds** and build your tree.
Assign kinds to products from the product form. See ``doc/USER_GUIDE.md`` (English)
or ``doc/USER_GUIDE.uk.md`` (Ukrainian) for the full walkthrough.

Credits
=======

Authors
~~~~~~~

* OdoMate

Maintainer
~~~~~~~~~~~

This module is maintained by OdoMate — https://odomate.pro — support@odomate.pro
