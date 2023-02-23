# -*- coding: utf-8 -*-
{
    'name': "Subcontractor invoices to clients",
    'version': '15.0.0.1.0',
    'category': 'Localization/Argentina',
    'author': "Julio Santa Cruz",
    'website': "https://github.com/bartacruz",
    'summary': """
        Create invoices from your subcontractors to clients directly
        using AFIP electronic invoices""",
    
    "license": "AGPL-3",
    'depends': ['l10n_ar','account','sale_purchase','l10n_ar_afipws_fe'],
    'data': [
        'views/account_journal.xml',
        'views/account_move.xml',
        'views/product_template.xml',
        'views/purchase_order.xml',
        'views/res_partner.xml',
    ],
}
