from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    kabay_force_consumer_invoice_title = fields.Boolean(
        string="Mostrar como factura de consumo (sin NCF)",
        help=(
            "Muestra las facturas de cliente de este diario como Factura de "
            "Consumo aunque el contacto tenga RNC. Esta opción sólo cambia el "
            "título impreso; no asigna un B02/NCF ni consume secuencias fiscales."
        ),
    )

    @api.constrains("kabay_force_consumer_invoice_title")
    def _check_kabay_consumer_invoice_without_fiscal_documents(self):
        for journal in self.filtered("kabay_force_consumer_invoice_title"):
            if (
                "l10n_latam_use_documents" in journal._fields
                and journal.l10n_latam_use_documents
            ):
                raise ValidationError(
                    _(
                        "La opción 'Mostrar como factura de consumo (sin NCF)' "
                        "sólo puede usarse en diarios que no usan documentos fiscales."
                    )
                )

    def write(self, vals):
        result = super().write(vals)
        if "l10n_latam_use_documents" in vals:
            self._check_kabay_consumer_invoice_without_fiscal_documents()
        return result
