# -*- coding: utf-8 -*-

import pytz

from markupsafe import Markup

from odoo import fields, models
from odoo.tools.mail import is_html_empty


_INVOICE_REPORT_DESIGN_SELECTION = [
    ("current", "Diseño 1"),
    ("new", "Diseño 2"),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    invoice_report_design = fields.Selection(
        selection=_INVOICE_REPORT_DESIGN_SELECTION,
        string="Diseño de factura",
        compute="_compute_invoice_report_design",
        inverse="_inverse_invoice_report_design",
        required=True,
        help=(
            "Selecciona el diseño utilizado para las facturas y notas de crédito "
            "emitidas por esta empresa."
        ),
    )

    # Compatibility field for databases or deployed copies that briefly used
    # this prefixed technical name in the company view. It is intentionally
    # non-stored, so loading the new Python code never requires a PostgreSQL
    # column before the module upgrade is executed.
    kabay_invoice_report_design = fields.Selection(
        selection=_INVOICE_REPORT_DESIGN_SELECTION,
        string="Diseño de factura (compatibilidad)",
        compute="_compute_kabay_invoice_report_design",
        inverse="_inverse_kabay_invoice_report_design",
        help="Campo técnico de compatibilidad para actualizaciones anteriores.",
    )

    def _invoice_report_design_key(self):
        self.ensure_one()
        return "kabay_invoice_report_pro.invoice_report_design.%s" % (self.id or 0)

    def _get_invoice_report_design_value(self):
        self.ensure_one()
        value = self.env["ir.config_parameter"].sudo().get_param(
            self._invoice_report_design_key()
        )
        return value if value in {"current", "new"} else "current"

    def _set_invoice_report_design_value(self, value):
        self.ensure_one()
        if not self.id:
            return
        safe_value = value if value in {"current", "new"} else "current"
        self.env["ir.config_parameter"].sudo().set_param(
            self._invoice_report_design_key(), safe_value
        )

    def _compute_invoice_report_design(self):
        """Read the report choice from a company-specific system parameter.

        The field is intentionally non-stored. This prevents a registry loaded
        with the new Python code from trying to read a not-yet-created column
        from ``res_company`` before the module upgrade can start.
        """
        for company in self:
            company.invoice_report_design = company._get_invoice_report_design_value()

    def _inverse_invoice_report_design(self):
        for company in self:
            company._set_invoice_report_design_value(
                company.invoice_report_design or "current"
            )

    def _compute_kabay_invoice_report_design(self):
        """Keep the temporary prefixed field synchronized with the main field."""
        for company in self:
            company.kabay_invoice_report_design = (
                company._get_invoice_report_design_value()
            )

    def _inverse_kabay_invoice_report_design(self):
        for company in self:
            company._set_invoice_report_design_value(
                company.kabay_invoice_report_design or "current"
            )

    def _kabay_report_tz(self):
        """Return a safe timezone name for report helpers.

        Some deployed revisions of this module used this helper while
        rendering company terms from QWeb. Keep it available so reports
        generated from Print, Email or WhatsApp do not fail if that code path
        is still referenced during an upgrade.
        """
        self.ensure_one()
        return (
            self.env.context.get("tz")
            or getattr(self.env.user, "tz", False)
            or getattr(self.partner_id, "tz", False)
            or "UTC"
        )

    def _kabay_report_terms_html(self, lang=None):
        """Return the company T&C configured in Accounting settings.

        Reports deliberately read the company configuration at print time instead
        of the document's cached ``note``/``narration``.  This keeps quotations and
        invoices aligned per company and prevents Odoo's web-terms URL from being
        printed as a second/duplicate terms block.
        """
        self.ensure_one()
        company = self.with_context(lang=lang) if lang else self

        # "Add a Note" stores the configured text in invoice_terms.  When a
        # database uses the web-page option, prefer the actual configured HTML
        # content over the generated /terms URL so the PDF still contains a
        # single, direct T&C block.
        terms_type = company.terms_type if "terms_type" in company._fields else "plain"
        if terms_type == "html" and "invoice_terms_html" in company._fields:
            value = company.invoice_terms_html
        else:
            value = company.invoice_terms if "invoice_terms" in company._fields else ""
        if is_html_empty(value):
            return Markup("")
        return Markup(value)

