# -*- coding: utf-8 -*-

import re
from datetime import date, datetime
from urllib.parse import quote_plus

from odoo import _, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _kabay_new_format_datetime_value(self, value):
        """Format optional fiscal signature values without assuming an addon."""
        if not value:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%d-%m-%Y %H:%M:%S")
        if isinstance(value, date):
            return value.strftime("%d-%m-%Y")

        text = str(value).strip()
        if not text:
            return ""
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return parsed.strftime("%d-%m-%Y %H:%M:%S")
        except (TypeError, ValueError):
            return text

    def _kabay_new_customer_address_lines(self):
        self.ensure_one()
        partner = self.partner_id
        locality = ", ".join(
            str(part).strip()
            for part in (
                partner.street2,
                partner.city,
                partner.state_id.name if partner.state_id else False,
                partner.zip,
            )
            if part
        )
        country = partner.country_id.name if partner.country_id else ""
        return [line for line in (partner.street or "", locality, country) if line]

    def _kabay_new_safe_field_value(self, record, field_name):
        """Read optional provider fields without making the report depend on them."""
        if not record or field_name not in record._fields:
            return False
        try:
            return record.sudo()[field_name]
        except Exception:
            return False

    def _kabay_new_optional_records(self):
        """Return fiscal records that can contain e-CF metadata."""
        self.ensure_one()
        records = [self]
        seen = {(self._name, self.id)}
        for field_names in (
            (
                "ecf_document_id",
                "l10n_do_ecf_document_id",
                "fiscal_document_id",
                "electronic_document_id",
            ),
            (
                "l10n_do_fiscal_sequence_id",
                "fiscal_sequence_id",
                "account_fiscal_sequence_id",
                "ncf_sequence_id",
                "ecf_sequence_id",
            ),
        ):
            record = False
            for field_name in field_names:
                record = self._kabay_new_safe_field_value(self, field_name)
                if record:
                    break
            if record:
                record_key = (record._name, record.id)
                if record_key not in seen:
                    records.append(record)
                    seen.add(record_key)
        return records

    def _kabay_new_find_optional_value(self, field_names, technical_tokens=(), field_types=()):
        """Read a known optional field, then use a conservative technical-name scan."""
        self.ensure_one()
        records = self._kabay_new_optional_records()

        for record in records:
            for field_name in field_names:
                value = self._kabay_new_safe_field_value(record, field_name)
                if value:
                    return value

        if not technical_tokens:
            return False

        for record in records:
            for field_name, field in record._fields.items():
                lowered = field_name.lower()
                if not all(token in lowered for token in technical_tokens):
                    continue
                if field_types and getattr(field, "type", "") not in field_types:
                    continue
                value = self._kabay_new_safe_field_value(record, field_name)
                if value:
                    return value
        return False

    def _kabay_new_get_security_code(self):
        self.ensure_one()
        value = self._kabay_new_find_optional_value(
            (
                "l10n_do_ecf_security_code",
                "l10n_do_security_code",
                "ecf_security_code",
                "fiscal_security_code",
                "security_code",
                "codigo_seguridad",
            ),
            technical_tokens=("security",),
            field_types=("char", "text", "selection"),
        )
        if not value:
            value = self._kabay_new_find_optional_value(
                (),
                technical_tokens=("seguridad",),
                field_types=("char", "text", "selection"),
            )
        return self._kabay_value_as_text(value).strip()

    def _kabay_new_get_signature_datetime(self):
        self.ensure_one()
        value = self._kabay_new_find_optional_value(
            (
                "l10n_do_ecf_sign_date",
                "l10n_do_ecf_signature_date",
                "l10n_do_signature_date",
                "ecf_signature_date",
                "digital_signature_date",
                "signature_date",
                "date_signed",
                "signed_at",
                "fecha_firma_digital",
                "fecha_firma",
            ),
            technical_tokens=("signature",),
            field_types=("date", "datetime", "char"),
        )
        if not value:
            value = self._kabay_new_find_optional_value(
                (),
                technical_tokens=("firma",),
                field_types=("date", "datetime", "char"),
            )
        return self._kabay_new_format_datetime_value(value)

    def _kabay_new_get_qr_values(self):
        """Return fiscal QR data from optional localization/provider fields."""
        self.ensure_one()
        known_fields = (
            "QR_code",
            "l10n_do_ecf_qr_code",
            "l10n_do_qr_code",
            "ecf_qr_code",
            "fiscal_qr_code",
            "qr_code",
            "qr_image",
            "qr_code_image",
            "qr_url",
            "qr_code_url",
        )
        records = self._kabay_new_optional_records()

        candidates = []
        for record in records:
            for field_name in known_fields:
                value = self._kabay_new_safe_field_value(record, field_name)
                if value:
                    candidates.append((record._fields[field_name], value))

        if not candidates:
            for record in records:
                for field_name, field in record._fields.items():
                    if "qr" not in field_name.lower():
                        continue
                    if getattr(field, "type", "") not in ("binary", "char", "text", "html"):
                        continue
                    value = self._kabay_new_safe_field_value(record, field_name)
                    if value:
                        candidates.append((field, value))

        for field, value in candidates:
            field_type = getattr(field, "type", "")
            if field_type == "binary":
                return {"binary": value, "src": ""}

            text = self._kabay_value_as_text(value).strip()
            if not text:
                continue
            image_match = re.search(r"<img[^>]+src=[\"']([^\"']+)", text, re.IGNORECASE)
            if image_match:
                text = image_match.group(1)
            if text.startswith(("data:image/", "/web/image", "/report/barcode")):
                return {"binary": False, "src": text}
            if re.fullmatch(r"[A-Za-z0-9+/=\s]+", text) and len(text) > 200:
                return {
                    "binary": False,
                    "src": "data:image/png;base64,%s" % re.sub(r"\s+", "", text),
                }

            # Provider modules frequently store the DGII verification URL or the
            # QR payload, not a rendered image. Use Odoo's standard barcode route.
            return {
                "binary": False,
                "src": (
                    "/report/barcode/?type=QR&value=%s&width=180&height=180"
                    % quote_plus(text)
                ),
            }

        return {"binary": False, "src": ""}

    def _kabay_new_get_tax_label(self):
        self.ensure_one()
        tax_totals = self.tax_totals or {}
        labels = []
        for subtotal in tax_totals.get("subtotals", []):
            for group in subtotal.get("tax_groups", []):
                label = group.get("group_name")
                if label and label not in labels:
                    labels.append(label)
        return ", ".join(labels) if labels else _("Impuestos")

    def _kabay_new_get_payment_values(self):
        """Backward-compatible alias for the shared invoice payment helper."""
        self.ensure_one()
        return self._kabay_get_payment_values()

    def _kabay_new_get_report_lines(self):
        self.ensure_one()
        lines = []
        taxable_amount = 0.0
        exempt_amount = 0.0

        for line in self._get_move_lines_to_report():
            if line.display_type == "product":
                line_parts = self._kabay_line_parts(line)
                tax_amount = line.price_total - line.price_subtotal
                has_nonzero_tax = not self.currency_id.is_zero(tax_amount)
                if has_nonzero_tax:
                    taxable_amount += line.price_subtotal
                else:
                    exempt_amount += line.price_subtotal
                lines.append(
                    {
                        "display_type": "product",
                        "record": line,
                        "primary": line_parts["primary"],
                        "detail": line_parts["detail"],
                        "tax_amount": tax_amount,
                    }
                )
            elif line.display_type in ("line_section", "line_subsection", "line_note"):
                lines.append(
                    {
                        "display_type": line.display_type,
                        "record": line,
                    }
                )

        return {
            "lines": lines,
            "taxable_amount": taxable_amount,
            "exempt_amount": exempt_amount,
        }

    def _kabay_new_is_electronic_fiscal_document(self):
        self.ensure_one()
        fiscal_number = self._kabay_get_fiscal_number().upper()
        document_code = self._kabay_get_document_code().upper()
        document_type = self._kabay_value_as_text(
            self._kabay_get_document_type_record()
        ).casefold()
        return (
            fiscal_number.startswith("E")
            or document_code.startswith("E")
            or "electr" in document_type
        )

    def _kabay_new_get_document_title(self):
        self.ensure_one()
        title = self._kabay_get_document_title()
        if self._kabay_new_is_electronic_fiscal_document() and "electr" not in title.casefold():
            title = _("%s Electrónica") % title
        return title

    def _kabay_new_invoice_report_data(self):
        """Prepare all isolated data used only by the second invoice design."""
        self.ensure_one()
        partner = self.partner_id
        report_lines = self._kabay_new_get_report_lines()
        text_blocks = self._kabay_invoice_text_blocks()
        fiscal_number = self._kabay_get_fiscal_number()
        is_electronic = self._kabay_new_is_electronic_fiscal_document()
        payments = self._kabay_new_get_payment_values()
        qr = self._kabay_new_get_qr_values()
        amount_paid = self.amount_total - self.amount_residual
        salesperson = self._kabay_first_field_value(self, ("invoice_user_id", "user_id"))

        company_terms = self.company_id._kabay_report_terms_html(
            lang=self.partner_id.lang or self.env.user.lang
        )

        return {
            "document_title": self._kabay_new_get_document_title(),
            "fiscal_number": fiscal_number,
            "fiscal_label": _("e-NCF") if is_electronic else _("NCF"),
            "fiscal_expiration": self._kabay_get_fiscal_expiration(),
            "fiscal_expiration_label": (
                _("Vencimiento e-NCF")
                if is_electronic
                else _("Vencimiento NCF")
            ),
            "invoice_date": self._kabay_format_date_value(self.invoice_date),
            "customer_phone": self._kabay_value_as_text(
                self._kabay_first_field_value(partner, ("phone", "mobile"))
            ),
            "customer_address_lines": self._kabay_new_customer_address_lines(),
            "origin": self.invoice_origin or "",
            "payment_term": self.invoice_payment_term_id.display_name if self.invoice_payment_term_id else _("Pago Contado"),
            "payment_reference": self._kabay_get_payment_reference_display(),
            "salesperson": self._kabay_value_as_text(salesperson),
            "company_terms": company_terms,
            "lines": report_lines["lines"],
            "taxable_amount": report_lines["taxable_amount"],
            "exempt_amount": report_lines["exempt_amount"],
            "tax_label": self._kabay_new_get_tax_label(),
            "payments": payments,
            "show_paid_amount": bool(payments) and not self.currency_id.is_zero(amount_paid),
            "amount_paid": amount_paid,
            "qr": qr,
            "security_code": self._kabay_new_get_security_code(),
            "signature_datetime": self._kabay_new_get_signature_datetime(),
        }
