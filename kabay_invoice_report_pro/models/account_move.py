# -*- coding: utf-8 -*-

import re
from datetime import date, datetime

from odoo import _, models
from odoo.tools import html2plaintext

from .report_utils import split_product_description


class AccountMove(models.Model):
    _inherit = "account.move"

    _KABAY_NCF_PATTERN = re.compile(r"\b(?:B\d{10}|E\d{12})\b", re.IGNORECASE)

    def _kabay_first_field_value(self, record, field_names):
        """Return the first non-empty optional field without requiring its addon."""
        if not record:
            return False
        for field_name in field_names:
            if field_name in record._fields:
                value = record[field_name]
                if value:
                    return value
        return False

    def _kabay_value_as_text(self, value):
        if not value:
            return ""
        if hasattr(value, "name") and value.name:
            return value.name
        if hasattr(value, "display_name"):
            return value.display_name or ""
        return str(value)

    def _kabay_format_date_value(self, value):
        """Use the dd/mm/yyyy order shown in the Odoo 17 reference invoice."""
        if not value:
            return ""
        if isinstance(value, datetime):
            value = value.date()
        if isinstance(value, date):
            return value.strftime("%d/%m/%Y")
        try:
            parsed = date.fromisoformat(str(value)[:10])
            return parsed.strftime("%d/%m/%Y")
        except (TypeError, ValueError):
            return str(value)

    def _kabay_get_document_type_record(self):
        self.ensure_one()
        return self._kabay_first_field_value(
            self,
            (
                "l10n_latam_document_type_id",
                "l10n_do_document_type_id",
                "document_type_id",
                "fiscal_type_id",
                "ncf_type_id",
            ),
        )

    def _kabay_get_fiscal_sequence_record(self):
        """Locate the fiscal-sequence relation regardless of the third-party field name."""
        self.ensure_one()
        explicit = self._kabay_first_field_value(
            self,
            (
                "l10n_do_fiscal_sequence_id",
                "fiscal_sequence_id",
                "account_fiscal_sequence_id",
                "ncf_sequence_id",
                "ecf_sequence_id",
            ),
        )
        if explicit:
            return explicit

        for field_name, field in self._fields.items():
            if (
                getattr(field, "type", "") == "many2one"
                and getattr(field, "comodel_name", "") == "account.fiscal.sequence"
            ):
                value = self[field_name]
                if value:
                    return value
        return False

    def _kabay_extract_ncf(self, value):
        text = self._kabay_value_as_text(value).strip()
        if not text:
            return ""
        match = self._KABAY_NCF_PATTERN.search(text.upper())
        return match.group(0).upper() if match else ""

    def _kabay_get_fiscal_number(self):
        """Read the NCF/e-NCF from known fields and safe fallbacks used by DO addons."""
        self.ensure_one()

        # Prioritize fields normally used by LATAM/Dominican localizations.
        for field_name in (
            "l10n_latam_document_number",
            "l10n_do_ncf",
            "l10n_do_fiscal_number",
            "l10n_do_ecf_number",
            "ncf",
            "ncf_number",
            "fiscal_number",
            "fiscal_document_number",
            "ecf_number",
            "e_ncf",
            "document_number",
        ):
            if field_name not in self._fields:
                continue
            raw_value = self[field_name]
            text = self._kabay_value_as_text(raw_value).strip()
            if not text:
                continue
            extracted = self._kabay_extract_ncf(text)
            if extracted:
                return extracted
            # Keep a non-accounting fiscal value even when a provider uses a custom format.
            if not self.name or self.name == "/" or text.casefold() != self.name.strip().casefold():
                return text

        # Some implementations append the NCF to the payment reference.
        for value in (self.payment_reference, self.ref):
            extracted = self._kabay_extract_ncf(value)
            if extracted:
                return extracted

        # Last-resort scan: only inspect char/text fields whose technical name is fiscal.
        fiscal_tokens = ("ncf", "ecf", "fiscal")
        for field_name, field in self._fields.items():
            if not any(token in field_name.lower() for token in fiscal_tokens):
                continue
            if getattr(field, "type", "") not in ("char", "text", "selection"):
                continue
            extracted = self._kabay_extract_ncf(self[field_name])
            if extracted:
                return extracted
        return ""

    def _kabay_get_payment_reference_display(self):
        """Return the invoice payment reference in the customer-facing format."""
        self.ensure_one()
        invoice_number = (self.name or "").strip()
        if invoice_number == "/":
            invoice_number = ""
        fiscal_number = self._kabay_get_fiscal_number().strip()

        # Keep the fiscal reference predictable in both invoice designs.
        if invoice_number and fiscal_number:
            return f"{invoice_number} - {fiscal_number}"
        return (self.payment_reference or invoice_number or fiscal_number or "").strip()

    def _kabay_get_document_code(self):
        self.ensure_one()
        records = [self._kabay_get_document_type_record(), self._kabay_get_fiscal_sequence_record()]
        candidate_fields = (
            "code",
            "doc_code_prefix",
            "prefix",
            "fiscal_code",
            "ncf_type",
            "document_code",
            "l10n_do_code",
            "name",
        )
        for record in records:
            if not record:
                continue
            value = self._kabay_first_field_value(record, candidate_fields)
            text = self._kabay_value_as_text(value).upper().strip()
            if text:
                return text
        return ""

    def _kabay_get_document_title(self):
        self.ensure_one()
        fiscal_number = self._kabay_get_fiscal_number().upper()
        document_type = self._kabay_get_document_type_record()
        document_name = self._kabay_value_as_text(document_type).strip()
        document_code = self._kabay_get_document_code()
        searchable = " ".join((fiscal_number, document_code, document_name.upper()))

        title = ""
        fiscal_titles = (
            (("B01", "E31", "CREDITO FISCAL", "CRÉDITO FISCAL"), _("Factura de Crédito Fiscal")),
            (("B02", "E32", "CONSUMO"), _("Factura de Consumo")),
            (("B03", "E33", "NOTA DE DEBITO", "NOTA DE DÉBITO"), _("Nota de Débito")),
            (("B04", "E34", "NOTA DE CREDITO", "NOTA DE CRÉDITO"), _("Nota de Crédito")),
            (("B11", "E41", "COMPRAS"), _("Comprobante de Compras")),
            (("B12", "REGISTRO UNICO", "REGISTRO ÚNICO"), _("Registro Único de Ingresos")),
            (("B13", "E43", "GASTO MENOR"), _("Comprobante para Gastos Menores")),
            (("B14", "E44", "REGIMEN ESPECIAL", "RÉGIMEN ESPECIAL"), _("Comprobante para Regímenes Especiales")),
            (("B15", "E45", "GUBERNAMENTAL"), _("Comprobante Gubernamental")),
            (("B16", "E46", "EXPORTACION", "EXPORTACIÓN"), _("Comprobante para Exportaciones")),
            (("B17", "E47", "PAGOS AL EXTERIOR"), _("Comprobante para Pagos al Exterior")),
        )
        for keys, mapped_title in fiscal_titles:
            if any(key in searchable for key in keys):
                title = mapped_title
                break

        # Use a meaningful localization name when it is more specific than "Factura".
        if not title and document_name and document_name.casefold() not in {
            "factura",
            "invoice",
            "documento",
            "document",
        }:
            title = document_name

        # Dominican fallback when the provider has not exposed the type field on the move.
        fiscal_country = self.company_id.account_fiscal_country_id or self.company_id.country_id
        is_dominican = fiscal_country and fiscal_country.code == "DO"
        if not title and is_dominican:
            if self.move_type == "out_refund":
                title = _("Nota de Crédito")
            elif self.move_type == "out_invoice":
                title = _("Factura de Crédito Fiscal") if self.partner_id.vat else _("Factura de Consumo")

        if not title:
            title_by_type = {
                "out_invoice": _("Factura"),
                "out_refund": _("Nota de Crédito"),
                "out_receipt": _("Recibo"),
                "in_invoice": _("Factura de proveedor"),
                "in_refund": _("Nota de crédito de proveedor"),
                "in_receipt": _("Recibo de proveedor"),
            }
            title = title_by_type.get(self.move_type, _("Documento contable"))

        if self.state == "draft":
            return _("BORRADOR - %s") % title
        if self.state == "cancel":
            return _("CANCELADA - %s") % title
        return title

    def _kabay_get_fiscal_expiration(self):
        self.ensure_one()
        document_type = self._kabay_get_document_type_record()
        sequence = self._kabay_get_fiscal_sequence_record()
        ecf_document = self._kabay_first_field_value(
            self,
            (
                "ecf_document_id",
                "l10n_do_ecf_document_id",
                "fiscal_document_id",
            ),
        )
        records = [self, sequence, document_type, self.journal_id, ecf_document]
        field_names = (
            "l10n_do_ncf_expiration_date",
            "l10n_do_expiration_date",
            "ncf_expiration_date",
            "fiscal_expiration_date",
            "expiration_date",
            "expiry_date",
            "valid_until",
            "validity_date",
            "sequence_expiration_date",
            "date_to",
            "end_date",
        )
        for record in records:
            value = self._kabay_first_field_value(record, field_names)
            if value:
                return self._kabay_format_date_value(value)

        # Safe heuristic for third-party fiscal sequence models.
        for record in (sequence, document_type, ecf_document):
            if not record:
                continue
            for field_name, field in record._fields.items():
                lowered = field_name.lower()
                if not any(token in lowered for token in ("expir", "valid", "date_to", "end_date")):
                    continue
                if getattr(field, "type", "") not in ("date", "datetime"):
                    continue
                value = record[field_name]
                if value:
                    return self._kabay_format_date_value(value)
        return ""

    def _kabay_get_adjustments(self):
        """Return only adjustments that materially change the amount payable."""
        self.ensure_one()
        adjustments = []

        def add_adjustment(amount_field, fixed_label, type_field=None, percent_field=None):
            if amount_field not in self._fields:
                return
            amount = self[amount_field] or 0.0
            if amount <= 0:
                return
            label = fixed_label
            if (
                type_field
                and percent_field
                and type_field in self._fields
                and percent_field in self._fields
                and self[type_field] == "porcentaje"
                and self[percent_field]
            ):
                label = "%s (%s%%)" % (fixed_label, self[percent_field])
            adjustments.append({"label": label, "amount": -amount})

        add_adjustment("imp_retencion", _("Retención de garantía"), "tipo_retencion", "retencion_porcentaje")
        add_adjustment("imp_anticipo", _("Anticipo"), "tipo_anticipo", "anticipo_porcentaje")
        add_adjustment("imp_isn", _("ISN"), "tipo_isn", "isn_porcentaje")
        return adjustments

    def _kabay_company_address_lines(self):
        """Build the three compact address lines used by the reference invoice."""
        self.ensure_one()
        partner = self.company_id.partner_id

        first_line = partner.street or ""
        locality_parts = [
            partner.street2,
            partner.city,
            partner.state_id.name if partner.state_id else False,
            partner.zip,
        ]
        locality_line = " ".join(
            str(part).strip() for part in locality_parts if part
        )
        country_line = partner.country_id.name if partner.country_id else ""
        return [line for line in (first_line, locality_line, country_line) if line]

    def _kabay_company_footer_address(self):
        self.ensure_one()
        partner = self.company_id.partner_id
        parts = [
            partner.street,
            partner.street2,
            partner.city,
            partner.state_id.name if partner.state_id else False,
            partner.zip,
            partner.country_id.name if partner.country_id else False,
        ]
        return ", ".join(str(part).strip() for part in parts if part)

    def _kabay_line_parts(self, line):
        """Separate product text while removing duplicated name lines."""
        return split_product_description(line.name)

    def _kabay_get_payment_values(self):
        """Return posted invoice payments in a PDF-friendly structure."""
        self.ensure_one()
        widget = self.sudo().invoice_payments_widget or {}
        if not isinstance(widget, dict):
            return []

        payments = []
        for payment in widget.get("content", []):
            if payment.get("is_exchange"):
                continue
            payments.append(
                {
                    "date": self._kabay_format_date_value(payment.get("date")),
                    "amount": payment.get("amount", 0.0),
                    "is_refund": bool(payment.get("is_refund")),
                }
            )
        return payments


    def _kabay_clean_report_plaintext(self, value):
        """Convert HTML to readable text without duplicated link footnotes.

        ``html2plaintext`` represents links as ``visible text [1]`` and appends
        ``[1] URL`` at the end. That is useful in plain-text emails, but it makes
        the same URL appear twice in the invoice PDF. Keep the visible URL and
        discard only the generated marker/definition.
        """
        plain = html2plaintext(value or "")
        plain = plain.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not plain:
            return ""

        footnote_numbers = set()
        visible_lines = []
        for line in plain.splitlines():
            match = re.match(r"^\s*\[(\d+)\]\s+https?://\S+\s*$", line)
            if match:
                footnote_numbers.add(match.group(1))
                continue
            visible_lines.append(line.rstrip())

        cleaned = "\n".join(visible_lines)
        for number in footnote_numbers:
            cleaned = re.sub(
                rf"(?<=\S)\s*\[{re.escape(number)}\](?=\s|$)",
                "",
                cleaned,
            )

        cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def _kabay_normalize_comparison_text(self, value):
        """Normalize labels for case-insensitive duplicate detection."""
        text = (value or "").casefold()
        text = text.translate(str.maketrans("áéíóúüñ", "aeiouun"))
        text = re.sub(r"\s+", " ", text)
        return text.strip(" \t\n:;.-")

    def _kabay_format_terms_and_conditions(self, text):
        """Place the terms URL/content on the line below its label.

        The payment-term note often arrives as a single line such as
        ``Términos y condiciones: https://example.com/terms``. The reference
        requested for this report keeps the label on one line and the URL or
        remaining content on the next line.
        """
        if not text:
            return ""

        pattern = re.compile(
            r"(?im)^(\s*(?:términos y condiciones|terminos y condiciones|terms and conditions)\s*:)\s*(\S.*)$"
        )
        formatted = pattern.sub(r"\1\n\2", text)
        formatted = re.sub(r"[ \t]+\n", "\n", formatted)
        formatted = re.sub(r"\n{3,}", "\n\n", formatted)
        return formatted.strip()

    def _kabay_remove_repeated_payment_term(self, text):
        """Remove the payment-term sentence already rendered above the notes."""
        if not text or not self.invoice_payment_term_id:
            return text or ""

        term = self._kabay_normalize_comparison_text(
            self.invoice_payment_term_id.display_name
        )
        if not term:
            return text

        labels = (
            "términos de pago",
            "terminos de pago",
            "condiciones de pago",
            "payment terms",
            "payment term",
        )
        cleaned_lines = []
        for line in text.splitlines():
            normalized_line = self._kabay_normalize_comparison_text(line)
            is_repeated = any(
                normalized_line
                == self._kabay_normalize_comparison_text(f"{label}: {term}")
                for label in labels
            )
            if not is_repeated:
                cleaned_lines.append(line)

        cleaned = "\n".join(cleaned_lines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def _kabay_invoice_text_blocks(self):
        """Split unique payment conditions from the final courtesy message."""
        self.ensure_one()
        payment_note = (
            self.invoice_payment_term_id.note
            if self.invoice_payment_term_id
            else False
        )

        pieces = []
        for value, remove_payment_term in (
            (payment_note, True),
            (self.narration, False),
        ):
            plain = self._kabay_clean_report_plaintext(value)
            if remove_payment_term:
                plain = self._kabay_remove_repeated_payment_term(plain)
            plain = self._kabay_format_terms_and_conditions(plain)
            if plain and plain not in pieces:
                pieces.append(plain)

        combined = "\n\n".join(pieces).strip()
        if not combined:
            return {"conditions": "", "closing": ""}

        blocks = [
            block.strip()
            for block in re.split(r"\n\s*\n", combined)
            if block.strip()
        ]
        closing_markers = (
            "agradecemos",
            "gracias",
            "thank you",
            "we appreciate",
        )
        closing = ""
        if len(blocks) > 1 and blocks[-1].casefold().startswith(closing_markers):
            closing = blocks.pop()
        elif len(blocks) == 1:
            lines = [line.strip() for line in blocks[0].splitlines() if line.strip()]
            for index, line in enumerate(lines):
                if line.casefold().startswith(closing_markers):
                    closing = "\n".join(lines[index:])
                    blocks = ["\n".join(lines[:index]).strip()] if index else []
                    break

        return {
            "conditions": "\n\n".join(blocks).strip(),
            "closing": closing.strip(),
        }

    def _kabay_invoice_report_data(self):
        """Return the exact data blocks used by the Odoo 17-style invoice."""
        self.ensure_one()
        partner = self.partner_id
        adjustments = self._kabay_get_adjustments()

        if "neto_a_cobrar" in self._fields and self.neto_a_cobrar:
            net_amount = self.neto_a_cobrar
        else:
            net_amount = self.amount_total + sum(item["amount"] for item in adjustments)

        salesperson = self._kabay_first_field_value(self, ("invoice_user_id", "user_id"))
        customer_phone = self._kabay_first_field_value(partner, ("mobile", "phone"))
        company_terms = self.company_id._kabay_report_terms_html(
            lang=self.partner_id.lang or self.env.user.lang
        )
        payments = self._kabay_get_payment_values()
        qr = self._kabay_new_get_qr_values()

        return {
            "document_title": self._kabay_get_document_title(),
            "fiscal_number": self._kabay_get_fiscal_number(),
            "fiscal_expiration": self._kabay_get_fiscal_expiration(),
            "customer_label": _("Cliente") if self.is_sale_document(include_receipts=True) else _("Proveedor"),
            "customer_phone": self._kabay_value_as_text(customer_phone),
            "customer_vat": partner.vat or "",
            "salesperson": self._kabay_value_as_text(salesperson),
            "quotation_code": self.invoice_origin or "",
            "reference": self.ref or self.invoice_origin or "",
            "payment_reference": self._kabay_get_payment_reference_display(),
            "payment_term": self.invoice_payment_term_id.display_name if self.invoice_payment_term_id else _("Pago Contado"),
            "company_terms": company_terms,
            "payments": payments,
            "invoice_date": self._kabay_format_date_value(self.invoice_date),
            "due_date": self._kabay_format_date_value(self.invoice_date_due),
            "adjustments": adjustments,
            "show_net_amount": bool(adjustments),
            "net_amount": net_amount,
            "qr": qr,
            "security_code": self._kabay_new_get_security_code(),
            "signature_datetime": self._kabay_new_get_signature_datetime(),
        }


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _kabay_untaxed_unit_price(self):
        """Return one invoice unit excluding any price-included taxes."""
        self.ensure_one()
        return self.tax_ids.compute_all(
            self.price_unit,
            currency=self.currency_id,
            quantity=1.0,
            product=self.product_id,
            partner=self.partner_id,
            is_refund=self.move_id.move_type in ("in_refund", "out_refund"),
        )["total_excluded"]
