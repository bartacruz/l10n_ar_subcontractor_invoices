# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

from odoo import fields, models, api, _

import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    subcontractor_pos_number = fields.Integer(string=_('Subcontractor POS'),
                                            help=_('Point of sale used to post subcontractor invoices'))
    subcontractor_invoice_ids = fields.One2many('account.move','subcontractor_partner_id',_('Subcontractor invoices'))
    subcontractor_invoice_count = fields.Integer('Subcontractor invoice count', compute="_compute_subcontractor_invoice_count", store=True)
    
    def action_subcontractor_fetch_pos(self):
        journal = self.env['account.move']._get_subcontractor_journal(['sale'])
        print("company", self.company_id)
        company = journal.company_id
        afip_ws = journal.afip_ws
        for record in self:
            context = {
                'default_afip_invoicing_partner': record,
            }
            ws = company.with_context(context).get_connection(afip_ws).connect()
            
            res = ws.ParamGetPtosVenta()
            _logger.info("Subcontractor %s pos %s", record.name, res)
            print(res)
            print("Resultado:", ws.Resultado)
            if not res:
                _logger.warning("Subcontractor %s has no POS", record.name)
            elif len(res)>1:
                _logger.warning("Subcontractor %s has %s POS: %s", record.name, len(res), res)
            else:
                pos = res[0].split('|')[0]
                _logger.info("Subcontractor %s has POS=%s", record.name, pos)
                record.subcontractor_pos_number= pos
        # if res:
        #     self.pos = res[0].split('|')[0]
        #     self.partner_id.towing_driver_point_of_sale = self.pos
        # elif not self.pos:
        #     self.pos = self.partner_id.towing_driver_point_of_sale
    
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