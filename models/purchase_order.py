# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)
                
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    is_third_party_billed = fields.Boolean(compute='_compute_third_party', store=True)
    third_party_customer_id = fields.Many2one('res.partner')
    
    @api.depends('order_line')
    def _compute_third_party(self):
        for record in self:
            print("record=",record,[l.product_id.invoice_policy for l in record.order_line])
            tp = [l.product_id.invoice_policy == 'third_party' for l in record.order_line]
            third_all = all(tp)
            third_any = any(tp)
            print("PurchaseOrder",record, "compute_third_party",record.order_line,tp)
            if not third_all and third_any:
                # raise ValidationError(_('Third party records must have ALL third party lines.'
                #                         'problematic record: %s' % record))
                _logger.warning(_('Third party records must have ALL third party lines.'
                                        'problematic record: %s' % record))
            record.is_third_party_billed = third_all
            if record.is_third_party_billed:
                record.third_party_customer_id = record._get_sale_orders().partner_id.id

    # override
    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        vals = super(PurchaseOrder, self)._prepare_invoice()
        print("prepare_invoice gets  ",vals)
        if self.is_third_party_billed and self.third_party_customer_id:
            invoice_partner = self.partner_id.parent_id or self.partner_id
            vals['move_type'] = 'out_invoice'
            vals['third_party_partner_id'] = invoice_partner.id
            # TODO: chequear el parent del cliente.
            # Hoy no lo hacemos porque no trabajamos todavia con clientes de tereceros.
            vals['partner_id'] = self.third_party_customer_id.id
            vals['fiscal_position_id']: (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(self.third_party_customer_id.id)).id
            vals['journal_id'] = self.env['account.move']._get_third_party_journal(['sale']).id
            # if self._get_sale_orders():
            #     vals['journal_id'] = self.env['account.move']._get_third_party_journal(['sale']).id
            print("prepare_invoice return",vals)
        return vals