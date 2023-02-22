# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    # Agregamos la politica de facturacion por terceros
    # invoice_policy = fields.Selection(selection_add=[('subcontractor','Invoiced by Subcontractor')])

    invoiced_by_subcontractor = fields.Boolean(string=_('Invoiced by subcontractor'))

    