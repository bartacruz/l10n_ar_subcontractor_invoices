# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    # Agregamos el la politica de facturacin por terceros
    invoice_policy = fields.Selection(selection_add=[('third_party','Customer billed by contractor')])
    
    