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
    subcontractor_invoice_ids = fields.One2many('account.move','subcontractor_partner_id',_('Subcontractor invoices'))
    subcontractor_invoice_count = fields.Integer('Subcontractor invoice count', compute="_compute_subcontractor_invoice_count", store=True)
    
    @api.depends('subcontractor_invoice_ids')
    def _compute_subcontractor_invoice_count(self):
        for record in self:
            record.subcontractor_invoice_count = len(record.subcontractor_invoice_ids)
    
    def action_open_subcontractor_invoices(self):
        self.ensure_one()
        action = self.env.ref("l10n_ar_subcontractor_invoices.action_subcontractor_invoice_type").read()[0]
        action["context"] = {}
        action["domain"] = [("id", "in", self.subcontractor_invoice_ids.ids)]
        
        return action