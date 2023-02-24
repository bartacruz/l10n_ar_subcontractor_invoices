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
    invoiced_by_display_name = fields.Char(_('Invoiced by'), compute="_compute_invoiced_by", store=True)
    
    @api.depends('subcontractor_partner_id','invoiced_by_subcontractor')
    def _compute_invoiced_by(self):
        for record in self:
            if record.invoiced_by_subcontractor:
                record.invoiced_by_display_name = record.subcontractor_partner_id.name
            else:
                record.invoiced_by_display_name = record.company_id.partner_id.name
    
    @api.model
    def _get_subcontractor_journal(self, journal_types):
        # TODO: check company_id
        domain = [('type', 'in', journal_types), ('invoiced_by_subcontractor','=',True)]
        #print('_get_subcontractor_journal domain=',domain)
        journal = self.env['account.journal'].search(domain, limit=1)
        return journal
    
    def _fix_subcontractor_tax_lines(self):
        self.ensure_one()
        print('_fix_subcontractor_tax_lines')
        # find tax lines
        tax_lines = self.line_ids.filtered('tax_repartition_line_id')
        product_id = self.line_ids.mapped('product_id')
        print('_fix_subcontractor_tax_lines pre=',tax_lines,product_id)
        if tax_lines and product_id:
            account_id = product_id[0]._get_product_accounts()['income']
            print('_fix_subcontractor_tax_lines change',tax_lines.mapped('account_id.name'),"to",account_id.name)
            tax_lines.account_id = account_id
        print('_fix_subcontractor_tax_lines exiting')
        
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
            if record.invoiced_by_subcontractor:
                record._fix_subcontractor_tax_lines()
    
    def _compute_l10n_latam_document_type(self):
        no_subinvoiced = self.filtered(lambda x: not x.invoiced_by_subcontractor)
        super(AccountMove, no_subinvoiced)._compute_l10n_latam_document_type()
        for record in self-no_subinvoiced:
        
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
            record.l10n_latam_document_type_id = 6
            subcontractor_letters = issue_letters[record.subcontractor_partner_id.l10n_ar_afip_responsibility_type_id.code]
            customer_letters = receive_letters[record.partner_id.l10n_ar_afip_responsibility_type_id.code]
            letters = list(set(subcontractor_letters) & set(customer_letters))
            types = record.env['l10n_latam.document.type'].search(['&',('l10n_ar_letter','in',letters), ('internal_type','=','invoice')])
            record.l10n_latam_document_type_id = types[0]
    
    @api.constrains('name', 'journal_id', 'state')
    def _check_unique_sequence_number(self):
        no_subinvoiced = self.filtered(lambda x: not x.invoiced_by_subcontractor)
        if self != no_subinvoiced:
            # Subcontractor invoices can have same sequence numbers.
            # TODO: Check uniqueness between invoices of the same subcontractor
            print('_check_unique_sequence_number','Ignoring move invoiced by subcontractor', self-no_subinvoiced)
            
        super(AccountMove, no_subinvoiced)._check_unique_sequence_number()

    # def _move_autocomplete_invoice_lines_values(self):
    #     print('_move_autocomplete_invoice_lines_values')
    #     super(AccountMove, self)._move_autocomplete_invoice_lines_values()
        
    # def _recompute_tax_lines(self, recompute_tax_base_amount=False, tax_rep_lines_to_recompute=None):
    #     print('_recompute_tax_lines entering')
    #     super(AccountMove, self)._recompute_tax_lines(recompute_tax_base_amount, tax_rep_lines_to_recompute)
    #     if self.invoiced_by_subcontractor:
    #         print('_recompute_tax_lines subcontractor')
    #         # find tax lines
    #         tax_lines = self.line_ids.filtered('tax_repartition_line_id')
    #         product_id = self.line_ids.mapped('product_id')
    #         print('_recompute_tax_lines pre=',tax_lines,product_id)
    #         if tax_lines and product_id:
    #             account_id = product_id[0]._get_product_accounts()['income']
    #             print('_recompute_tax_lines post',account_id.name)
    #             tax_lines.account_id = account_id
    #     print('_recompute_tax_lines exiting')

    # sequence.mixin override
    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super(AccountMove, self)._get_last_sequence_domain(relaxed)
        if self.subcontractor_partner_id:
            # Aumentamos el dominio de busqueda para obtener solo las facturas del
            # proveedor
            where_string += " AND  subcontractor_partner_id= %(subcontractor_partner_id)s"
            param['subcontractor_partner_id'] = self.subcontractor_partner_id.id or 0
        
        return where_string, param
    
    def _set_next_sequence(self):
        if self.subcontractor_partner_id:
            context = {
                'default_afip_invoicing_partner': self.subcontractor_partner_id,
                'default_l10n_ar_afip_pos_number': self.subcontractor_partner_id.subcontractor_pos_number
            }
            # post with context to AFIP WS 
            self = self.with_context(context)
        print('_set_next_sequence context',self._context)
        return super(AccountMove, self)._set_next_sequence()
        
    def _get_starting_sequence(self):
        self.ensure_one()
        if self.subcontractor_partner_id:
            context = {
                'default_afip_invoicing_partner': self.subcontractor_partner_id,
                'default_l10n_ar_afip_pos_number': self.subcontractor_partner_id.subcontractor_pos_number
            }
            # post with context to AFIP WS 
            self = self.with_context(context)
        print('_get_starting_sequence context',self._context)
        return super(AccountMove,self)._get_starting_sequence()
    
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

