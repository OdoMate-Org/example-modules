{
    'name': "Project Task Checklists",

    'summary': """
        Project task checklist templates: reusable step-by-step checklists,
        per-task customization, checklist progress bar, task start/end date
        auto-stamping, to-do steps tracking for Odoo Project
    """,

    'description': """
Project Task Checklists
=======================
Reusable checklist templates (Project > Configuration > Checklists) that can be
applied to any Project task in one click. Each task gets its own independent
copy of the steps, which can be edited, reordered, extended or removed.

* Start / Done / Cancel buttons per step with colour-coded status
* Checklist progress bar on the task form and in the task list
  (cancelled steps are excluded from the calculation)
* Start Date and End Date auto-stamped from checklist activity and
  self-healing when progress drops below 100%
* Confirmation wizard when replacing a checklist that is already in progress
* Steps follow the task's own visibility rules
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro",
    'support': "support@odomate.pro",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/20.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Services/Project',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['project'],

    # always loaded
    'data': [
        'security/ir.access.csv',
        'wizard/project_task_checklist_replace_wizard_views.xml',
        'views/project_checklist_template_views.xml',
        'views/project_task_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
