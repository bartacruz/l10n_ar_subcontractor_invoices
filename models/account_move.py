from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"
    
    is_third_party_billed = fields.Boolean(compute='_compute_third_party', store=True)
    third_party_partner_id = fields.Many2one('res.partner')    
    
    @api.model
    def _get_third_party_journal(self, journal_types):
        # TODO: check company_id
        domain = [('type', 'in', journal_types), ('is_third_party_billed','=',True)]
        print('_get_third_party_journal domain=',domain)
        journal = self.env['account.journal'].search(domain, limit=1)
        return journal
    
    # Computes
    
    @api.depends('invoice_line_ids')
    def _compute_third_party(self):
        for record in self:
            third_all = all(l.is_third_party_billed for l in record.invoice_line_ids)
            third_any = any(l.is_third_party_billed for l in record.invoice_line_ids)
            if not third_all and third_any:
                raise ValidationError(_('Third party moves must have ALL third party lines.'
                                        'problematic record: %s' % record))
            record.is_third_party_billed = third_all
    
    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super(AccountMove, self)._get_last_sequence_domain(relaxed)
        if self.third_party_partner_id:
            where_string += " AND  third_party_partner_id= %(third_party_partner_id)s"
            param['third_party_partner_id'] = self.third_party_partner_id.id or 0
        return where_string, param
    
    def _post(self, soft=True):
        third_party_invoices = self.filtered(lambda x: x.third_party_partner_id)
        normal_invoices = self - third_party_invoices
        res = super(AccountMove, normal_invoices)._post(soft)
        for inv in third_party_invoices:
            partner = inv.third_party_partner_id
            context = {
                'default_afip_invoicing_partner': partner,
                'default_l10n_ar_afip_pos_number': partner.third_party_pos_number
            }
            # post with context to AFIP WS 
            res = res + super(AccountMove, inv.with_context(context))._post(soft)
        return res
        
            
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    is_third_party_billed = fields.Boolean(compute='_compute_third_party', store=True)
    
    @api.depends('product_id')
    def _compute_third_party(self):
        for record in self:
            record.is_third_party_billed = record.product_id.invoice_policy == 'third_party'