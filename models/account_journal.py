from odoo import models, api, fields, _
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    is_third_party_billed = fields.Boolean()