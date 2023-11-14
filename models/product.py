from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _select_seller(self, partner_id=False, quantity=0.0, date=None, uom_id=False, params=False):
        ret = super(ProductProduct,self)._select_seller(partner_id, quantity, date, uom_id, params)
        if not ret and partner_id and self.service_to_purchase:
            # Creo un product.supplierinfo para el partner
            vals={
                'name': partner_id.id,
                'price': 0,
                'product_tmpl_id': self.product_tmpl_id.id
            }
            ret = self.seller_ids.create(vals)
            _logger.info("Creando proveedor %s para %s" % (partner_id.name,self.name,))
        return ret