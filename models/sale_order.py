from odoo import api, fields, models, _
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def _get_invoiceable_lines(self, final=False):
        lines = super(SaleOrder, self)._get_invoiceable_lines(final=final)
        for line in self.order_line:
            print("Line to invoice?",line.product_id,line.qty_to_invoice, line.invoice_status)
        return lines

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        super(SaleOrderLine,self)._get_to_invoice_qty()
        for line in self:
            if line.product_id.invoiced_by_subcontractor:
                # Don't include this line in the sale order invoice
                print("subcontracted line, setting qty_to_invoice=0",line)
                line.qty_to_invoice = 0
            