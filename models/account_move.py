# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"
    
    invoiced_by_subcontractor = fields.Boolean(compute='_compute_invoiced_by_subcontractor', string=_('Invoiced by subcontractor'), store=True)
    subcontractor_partner_id = fields.Many2one('res.partner', string=_('Invoice subcontractor'))
    
    @api.model
    def _get_subcontractor_journal(self, journal_types):
        # TODO: check company_id
        domain = [('type', 'in', journal_types), ('invoiced_by_subcontractor','=',True)]
        #print('_get_subcontractor_journal domain=',domain)
        journal = self.env['account.journal'].search(domain, limit=1)
        return journal
    
    @api.depends('invoice_line_ids')
    def _compute_invoiced_by_subcontractor(self):
        for record in self:
            third_all = all(l.invoiced_by_subcontractor for l in record.invoice_line_ids)
            third_any = any(l.invoiced_by_subcontractor for l in record.invoice_line_ids)
            if not third_all and third_any:
                raise ValidationError(_('Third party moves must have ALL third party lines.'
                                        'problematic record: %s' % record))
            record.invoiced_by_subcontractor = third_all
    
    # sequence.mixin override
    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super(AccountMove, self)._get_last_sequence_domain(relaxed)
        if self.subcontractor_partner_id:
            # Aumentamos el dominio de busqueda para obtener solo las facturas del
            # proveedor
            where_string += " AND  subcontractor_partner_id= %(subcontractor_partner_id)s"
            param['subcontractor_partner_id'] = self.subcontractor_partner_id.id or 0
        
        return where_string, param
    
    def _post(self, soft=True):
        subcontractor_invoices = self.filtered(lambda x: x.subcontractor_partner_id)
        normal_invoices = self - subcontractor_invoices
        
        # posteo las facturas que no son de terceros
        res = super(AccountMove, normal_invoices)._post(soft)
        
        for inv in subcontractor_invoices:
            # ver y usar https://github.com/bartacruz/odoo-argentina-ce/tree/15.0-third_party_invoice
            # hasta que acepten el pull-request...
            
            partner = inv.subcontractor_partner_id
            context = {
                'default_afip_invoicing_partner': partner,
                'default_l10n_ar_afip_pos_number': partner.subcontractor_pos_number
            }
            # post with context to AFIP WS 
            res = res + super(AccountMove, inv.with_context(context))._post(soft)
        return res
            
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    invoiced_by_subcontractor = fields.Boolean(compute='_compute_invoiced_by_subcontractor', string=_('Billing subcontractor'), store=True)
    
    @api.depends('product_id')
    def _compute_invoiced_by_subcontractor(self):
        for record in self:
            record.invoiced_by_subcontractor = record.product_id.invoice_policy == 'subcontractor'

