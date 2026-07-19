{
    'name': "Project Task Checklists",
    'summary': "Odoo Project Task Checklists module automates step-by-step checklist "
               "tracking on project tasks, letting teams standardize recurring workflows "
               "and monitor completion without manual status updates. "
               "task checklist module | project | reusable template | "
               "progress tracking | management | "
               "recurring workflow | completion tracking | "
               "onboarding | automation",
    'description': """
Project Task Checklists
=======================

Attach reusable, step-by-step checklists to project tasks, customize them
per task, track completion with a live progress bar, and let start/end dates
stamp themselves automatically.
    """,
    'author': "OdoMate",
    'website': "https://odomate.pro",
    'support': "info@odomate.pro",
    'category': 'Services/Project',
    'version': '19.0.1.0.2',
    'license': 'LGPL-3',
    'depends': ['project'],
    'data': [
        'security/ir.model.access.csv',
        'security/project_checklist_security.xml',
        'views/project_checklist_template_views.xml',
        'views/project_task_views.xml',
        'wizard/wizard_project_checklist_views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
