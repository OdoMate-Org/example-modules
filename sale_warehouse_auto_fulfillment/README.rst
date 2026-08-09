==============================
Sale Warehouse Auto Fulfillment
==============================

.. |badge_license| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. |badge_version| image:: https://img.shields.io/badge/odoo-19.0-purple.png
    :alt: Odoo 19.0

|badge_license| |badge_version|

Three per-warehouse switches turn a single **Confirm** click on a sales order
into a complete fulfillment run: the delivery is validated in full, the customer
invoice is created and the invoice is posted. Everything runs inside one
database savepoint, so a real error leaves the order as a quotation with nothing
half-done, and the failure is recorded in ``ir.logging`` through an independent
transaction.

Installation
============

#. Copy ``sale_warehouse_auto_fulfillment`` into your Odoo addons path.
#. Open **Apps**, click **Update Apps List**.
#. Search for *Sale Warehouse Auto Fulfillment* and click **Activate**.

Dependencies: ``sale_stock``, ``account``, ``mail``.

Configuration
=============

Go to **Inventory ▸ Configuration ▸ Warehouses**, open a warehouse and use the
three checkboxes next to **Short Name**:

* **Ship Automatically** (``auto_ship``) — validate the delivery in full, all
  lines, no backorder, no stock availability check.
* **Create Invoice Automatically** (``auto_invoice_create``) — run standard
  invoice creation, respecting each product's invoicing policy. When there is
  nothing to invoice the step is skipped silently and a chatter note is added.
* **Confirm Invoice Automatically** (``auto_invoice_confirm``) — post the
  invoice this run just created. It has no effect on its own.

All three are off after installation. No new group, menu, screen or model is
added; the automation runs behind the existing **Confirm** button.

Known limitations
=================

* No partial shipping — automatic delivery is all-or-nothing.
* No stock availability check — negative stock is intended behaviour.
* Lot/serial-tracked products are out of scope; a required lot is a real failure.
* No per-order override and no exception list.
* Invoices are posted, never emailed.
* Automation history lives in ``ir.logging`` only (developer-facing).

Documentation
=============

See ``doc/USER_GUIDE.md`` for the full guide, worked examples and a demo-data
walkthrough.

Credits
=======

Author and maintainer: **OdoMate** — https://odomate.pro — support@odomate.pro
