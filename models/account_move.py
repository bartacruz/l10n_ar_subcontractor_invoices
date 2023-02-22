# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"
    
    # TODO: agregar un constrain. Si es invoiced_by_subcontractor TIENE que tener el partner seteado
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
            ibs = [l.product_id.invoiced_by_subcontractor for l in record.invoice_line_ids]
            print(record.invoice_line_ids,all(ibs))
            if not all(ibs) and any(ibs):
                raise ValidationError(_('Mixing subcontracted product lines with normal ones'
                                        'problematic record: %s' % record))
            if len(record.invoice_line_ids) == 0 and record.subcontractor_partner_id:
                record.invoiced_by_subcontractor = True
            else:    
                record.invoiced_by_subcontractor = any(ibs) and all(ibs)
            print('_compute_invoiced_by_subcontractor', record,record.invoiced_by_subcontractor)
    
    def _compute_l10n_latam_document_type(self):
        if not self.invoiced_by_subcontractor:
            super(AccountMove, self)._compute_l10n_latam_document_type()
            return
        
        issue_letters = {
            '1': ['A', 'B', 'E', 'M'],
            '3': [],
            '4': ['C'],
            '5': [],
            '6': ['C', 'E'],
            '9': ['I'],
            '10': [],
            '13': ['C', 'E'],
            '99': []
        }
        receive_letters = {
            '1': ['A', 'B', 'C', 'E', 'M', 'I'],
            '3': ['B', 'C', 'I'],
            '4': ['B', 'C', 'I'],
            '5': ['B', 'C', 'I'],
            '6': ['A', 'B', 'C', 'I'],
            '9': ['E'],
            '10': ['E'],
            '13': ['A', 'B', 'C', 'I'],
            '99': ['B', 'C', 'I']
        }
        self.l10n_latam_document_type_id = 6
        subcontractor_letters = issue_letters[self.subcontractor_partner_id.l10n_ar_afip_responsibility_type_id.code]
        customer_letters = receive_letters[self.partner_id.l10n_ar_afip_responsibility_type_id.code]
        letters = list(set(subcontractor_letters) & set(customer_letters))
        types = self.env['l10n_latam.document.type'].search(['&',('l10n_ar_letter','in',letters), ('internal_type','=','invoice')])
        self.l10n_latam_document_type_id = types[0]

    # sequence.mixin override
    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super(AccountMove, self)._get_last_sequence_domain(relaxed)
        if self.subcontractor_partner_id:
            # Aumentamos el dominio de busqueda para obtener solo las facturas del
            # proveedor
            where_string += " AND  subcontractor_partner_id= %(subcontractor_partner_id)s"
            param['subcontractor_partner_id'] = self.subcontractor_partner_id.id or 0
        
        return where_string, param
    
    def _check_argentinean_invoice_taxes(self):
        moves = self.filtered(lambda x: not x.invoiced_by_subcontractor)
        super(AccountMove, moves)._check_argentinean_invoice_taxes()
        
    def create(self, vals):
        print(vals)
        if 'subcontractor_partner_id' in vals:
            
            partner = self.env['res.partner'].browse(vals.get('subcontractor_partner_id'))
            context = {
                'default_afip_invoicing_partner': partner,
                'default_l10n_ar_afip_pos_number': partner.subcontractor_pos_number
            }
            # post with context to AFIP WS 
            self = self.with_context(context)
        print("subcontract? context", self._context)
        return super(AccountMove, self).create(vals)
        
            
        
    
    def _post(self, soft=True):
        subcontractor_invoices = self.filtered(lambda x: x.subcontractor_partner_id)
        normal_invoices = self - subcontractor_invoices
        
        # posteo las facturas que no son de subcontratistas
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
            
# class AccountMoveLine(models.Model):
#     _inherit = "account.move.line"
    
#     invoiced_by_subcontractor = fields.Boolean(compute='_compute_invoiced_by_subcontractor', string=_('Billing subcontractor'), store=True)
    
#     @api.depends('product_id')
#     def _compute_invoiced_by_subcontractor(self):
#         for record in self:
#             record.invoiced_by_subcontractor = record.product_id.invoice_policy == 'subcontractor'

