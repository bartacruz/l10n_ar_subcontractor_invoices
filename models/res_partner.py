from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"

    third_party_pos_number = fields.Integer(string=_('Third Party POS'),
                                            help=_('Point of sale used to post third party invoices'))
    