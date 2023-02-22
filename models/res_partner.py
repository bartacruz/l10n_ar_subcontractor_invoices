# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

from odoo import fields, models, api, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    subcontractor_pos_number = fields.Integer(string=_('Subcontractor POS'),
                                            help=_('Point of sale used to post subcontractor invoices'))


    