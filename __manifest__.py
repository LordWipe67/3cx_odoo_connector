# -*- coding: utf-8 -*-
{
    'name': '3cx-odoo connector',
    'version': '1.0.0',
    'author': 'Maurizio Aquino',
    'category': 'Sales',
    'sequence': -100,
    'summary': 'Integrazione odoo con 3cx',
    'category': 'Productivity',
    'version': '15.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'partner_firstname'],
    'license': 'AGPL-3',

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/view_form.xml',
        'views/view_tree.xml',
        'views/modify_view_opportunity.xml',
        'views/view_realtime.xml',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],

}
