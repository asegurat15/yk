from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    total_boxes = fields.Integer(string="Total cajas", compute="_compute_totals_boxes_qty", store=False)
    total_qty = fields.Float(string="Total cantidad", compute="_compute_totals_boxes_qty", store=False)

    @api.depends('invoice_line_ids.boxes', 'invoice_line_ids.quantity', 'invoice_line_ids.display_type')
    def _compute_totals_boxes_qty(self):
        for move in self:
            lines = move.invoice_line_ids

            move.total_boxes = sum(lines.mapped('boxes') or [0])
            move.total_qty = sum(lines.mapped('quantity') or [0.0])


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    po_number   = fields.Char(string="PO#")
    color       = fields.Char(string="color")
    style       = fields.Char(string="Estilo")
    boxes       = fields.Integer(string="Cajas/Paq.")
    lot_number  = fields.Char(string="Lot #")


class SaleOrder(models.Model):
    _inherit = "sale.order"
    total_boxes = fields.Integer(string="Total cajas", compute="_compute_totals_boxes_qty", store=True)
    total_qty = fields.Float(string="Total cantidad", compute="_compute_totals_boxes_qty", store=True)

    @api.depends('order_line.boxes', 'order_line.product_uom_qty', 'order_line.display_type', 'order_line.is_downpayment')
    def _compute_totals_boxes_qty(self):
        for order in self:
            lines = order.order_line.filtered(lambda l: not l.display_type and not l.is_downpayment)

            order.total_boxes = sum(lines.mapped('boxes') or [0])
            order.total_qty = sum(lines.mapped('product_uom_qty') or [0.0])

    def _prepare_invoice(self):
        self.ensure_one()
        vals = super()._prepare_invoice()
        vals.update({
            'partner_shipping_id': self.partner_shipping_id.id,
        })
        return vals


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    po_number   = fields.Char(string="PO#")
    color       = fields.Char(string="color")
    style       = fields.Char(string="Estilo")
    boxes       = fields.Integer(string="Cajas/Paq.")
    lot_number  = fields.Char(string="Lot #")


    def action_duplicate_last_line(self):
        """Se llama desde el botón del o2m. Crea una nueva línea clonando la última línea 'de producto'."""
        order = self.env['sale.order'].browse(self.env.context.get('order_id'))
        if not order or not order.exists():
            return

        lines = order.order_line.filtered(lambda l: not l.display_type and not l.is_downpayment)
        if not lines:
            return
        last = lines[-1]

        vals = {
            'order_id': order.id,
            'po_number': last.po_number,
            'color': last.color,
            'style': last.style,
            'boxes': last.boxes,
            'lot_number': last.lot_number,
            'product_id': last.product_id.id,
            'name': last.name,
            'product_uom_id': last.product_uom_id.id, 
            'product_uom_qty': last.product_uom_qty,
            'price_unit': last.price_unit,
            'discount': last.discount,
            'tax_ids': [(6, 0, last.tax_ids.ids)],
            'customer_lead': last.customer_lead,
        }

        self.env['sale.order.line'].create(vals)
        return

    def _prepare_invoice_line(self, **optional_values):
        vals = super()._prepare_invoice_line(**optional_values)
        vals.update({
            'po_number': self.po_number,
            'color': self.color,
            'style': self.style,
            'color': self.color,
            'boxes': self.boxes,
            'lot_number': self.lot_number,
        })
        return vals