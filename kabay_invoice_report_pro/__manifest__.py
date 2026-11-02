{
    "name": "Kabay Invoice Report Pro",
    "version": "19.0.1.9.11",
    "category": "Accounting/Accounting",
    "summary": "Company-specific invoice and quotation layouts for Odoo PDF output",
    "description": """
Professional accounting invoice report for Odoo 19 Enterprise.

The module reorganizes the standard invoice PDF while preserving the accounting,
fiscal, NCF, taxes, payment, and custom adjustment data already provided by the
installed modules.
    """,
    "author": "Kabay Group",
    "license": "LGPL-3",
    "depends": [
        "account",
        "sale",
        "web",
    ],
    "data": [
        "views/res_company_views.xml",
        # "views/sale_order_views.xml",
        "report/invoice_report_new_templates.xml",
        "report/invoice_report_templates.xml",
        # "report/quotation_report_templates.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "kabay_invoice_report_pro/static/src/css/invoice_report.css",
            "kabay_invoice_report_pro/static/src/css/invoice_report_new.css",
            "kabay_invoice_report_pro/static/src/css/quotation_report.css",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
