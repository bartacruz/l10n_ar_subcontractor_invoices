# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)
                
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    invoiced_by_subcontractor = fields.Boolean(compute='_compute_invoiced_by_subcontractor', string=_('Invoiced by subcontractor'), store=True)
    subcontractor_customer_id = fields.Many2one('res.partner', string=_('Purchase customer'))
    
    @api.depends('order_line')
    def _compute_invoiced_by_subcontractor(self):
        for record in self:
            #print("record=",record,[l.product_id.invoice_policy for l in record.order_line])
            ibs = [l.product_id.invoiced_by_subcontractor for l in record.order_line]
            #print("PurchaseOrder",record, "compute_subcontractor",record.order_line,tp)
            if not all(ibs) and any(ibs):
                # raise ValidationError(_('Third party records must have ALL third party lines.'
                #                         'problematic record: %s' % record))
                _logger.warning(_('Third party records must have ALL third party lines.'
                                        'problematic record: %s' % record))
            record.invoiced_by_subcontractor = all(ibs) and any(ibs)
            if record.invoiced_by_subcontractor and record._get_sale_orders().partner_id:
                record.subcontractor_customer_id = record._get_sale_orders().partner_id.id

    # override
    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        vals = super(PurchaseOrder, self)._prepare_invoice()
        if self.invoiced_by_subcontractor and self.subcontractor_customer_id:
            
            # purchase.order genera facturas de proveedores ("in_invoice") en
            # el diario de compras.
            # Las facturas terecerizadas deben ser "out_invoice" (son hacia
            # el cliente) y quedar asentadas en el diario de facturas tercerizadas
    
            vals['move_type'] = 'out_invoice'
            # El partner generador de la factura es el partner de la orden de 
            # compra (o su parent)
            invoice_partner = self.partner_id.parent_id or self.partner_id
            vals['subcontractor_partner_id'] = invoice_partner.id
            
            # TODO: chequear el parent del cliente.
            # Hoy no lo hacemos porque no trabajamos todavia con clientes de tereceros.
            vals['partner_id'] = self.subcontractor_customer_id.id
            vals['fiscal_position_id']: (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(self.subcontractor_customer_id.id)).id
            
            # El diario de facturas tercerizadas (ver account_journal.py)
            vals['journal_id'] = self.env['account.move']._get_subcontractor_journal(['sale']).id
            # print("prepare_invoice return",vals)
        return vals

