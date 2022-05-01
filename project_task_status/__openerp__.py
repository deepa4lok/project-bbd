# -*- coding: utf-8 -*-
{
    'name': 'Project Management - BBD',
    'version': '1.1',
    'author': 'Deepa Venkatesh',
    'website': 'https://www.odoo.com/page/project-management',
    'category': 'Project Management',
    'sequence': 8,
    'summary': 'Projects, Tasks',
    'depends': ['project'
    ],
    'description': """
Report Analysis on Task Management
=====================================================
This modules provides an overview of Task assignments collectively of all projects. 
Further it also provides an option to download the report in JSON format.
    """,
    'data': [
        "views/project.xml",
        "reports/report_task_status_view.xml"

    ],
    'demo': [],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}