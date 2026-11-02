from odoo.tests.common import TransactionCase


class TestReportTimezone(TransactionCase):
    """Las fechas del PDF se imprimen en hora local, no en UTC."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({
            "name": "Kabay Timezone Test",
            "country_id": cls.env.ref("base.do").id,
        })

    def test_country_timezone_is_used_when_nothing_is_configured(self):
        self.company.partner_id.tz = False
        self.env.user.tz = False
        self.assertEqual(self.company._kabay_report_tz(), "America/Santo_Domingo")

    def test_configured_company_timezone_wins(self):
        self.company.partner_id.tz = "America/New_York"
        self.env.user.tz = "Europe/Madrid"
        self.assertEqual(self.company._kabay_report_tz(), "America/New_York")
