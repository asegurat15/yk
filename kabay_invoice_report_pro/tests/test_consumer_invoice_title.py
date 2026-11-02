from odoo.tests.common import TransactionCase


class TestConsumerInvoiceTitle(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Kabay Consumer Invoice Test",
                "country_id": cls.env.ref("base.do").id,
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Non-fiscal Customer Invoices",
                "code": "KCT",
                "type": "sale",
                "company_id": cls.company.id,
            }
        )
        cls.partner_with_vat = cls.env["res.partner"].create(
            {
                "name": "Customer With RNC",
                "vat": "132122771",
                "country_id": cls.env.ref("base.do").id,
            }
        )
        cls.partner_without_vat = cls.env["res.partner"].create(
            {
                "name": "Customer Without RNC",
                "country_id": cls.env.ref("base.do").id,
            }
        )

    def _new_invoice(self, partner):
        return self.env["account.move"].new(
            {
                "move_type": "out_invoice",
                "journal_id": self.journal.id,
                "company_id": self.company.id,
                "partner_id": partner.id,
            }
        )

    def test_force_consumer_title_keeps_customer_vat(self):
        self.journal.kabay_force_consumer_invoice_title = True
        invoice = self._new_invoice(self.partner_with_vat)

        self.assertEqual(invoice._kabay_get_document_title(), "BORRADOR - Factura de Consumo")
        self.assertEqual(invoice.partner_id.vat, "132122771")

        invoice.state = "posted"
        self.assertEqual(invoice._kabay_get_document_title(), "Factura de Consumo")

        invoice.state = "cancel"
        self.assertEqual(invoice._kabay_get_document_title(), "CANCELADA - Factura de Consumo")

    def test_unconfigured_journal_keeps_existing_fallback(self):
        invoice_with_vat = self._new_invoice(self.partner_with_vat)
        invoice_without_vat = self._new_invoice(self.partner_without_vat)

        self.assertEqual(
            invoice_with_vat._kabay_get_document_title(),
            "BORRADOR - Factura de Crédito Fiscal",
        )
        self.assertEqual(
            invoice_without_vat._kabay_get_document_title(),
            "BORRADOR - Factura de Consumo",
        )
