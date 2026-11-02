# -*- coding: utf-8 -*-

from odoo import api, fields, models

from .report_utils import split_product_description


class SaleOrder(models.Model):
    _inherit = "sale.order"

    kabay_hide_product_description = fields.Boolean(
        string="Ocultar descripción de productos",
        compute="_compute_kabay_hide_product_description",
        help=(
            "Campo técnico que oculta la descripción editable de las líneas "
            "cuando la compañía utiliza el Diseño 2."
        ),
    )

    @api.depends("company_id")
    def _compute_kabay_hide_product_description(self):
        for order in self:
            order.kabay_hide_product_description = (
                order.company_id.invoice_report_design == "new"
            )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _kabay_report_line_parts(self):
        """Split and de-duplicate the product description for PDF reports."""
        self.ensure_one()
        return split_product_description(self.name)
