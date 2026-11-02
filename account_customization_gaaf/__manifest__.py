{
    "name": "Account move Line Fields Custom Gaaf",
    "version": "1.0",
    "category": "Sales",
    "summary": "Añade campos PO#, Estilo, Cajas, Color, Lot # y Kgs a las líneas de venta",
    'author': 'Kuai-mare carrasquero',
    'license': 'LGPL-3',
    "depends": [
        'sale',
        'account',
        'l10n_do',
    ],
    "data": [
        "views/account_move_views.xml",
        "views/sales_order_views.xml",
        'views/report_invoice_document_inherit.xml',
        'views/sale_order_form_inherit.xml',
    ],
}