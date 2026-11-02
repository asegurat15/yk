# Kabay Invoice Report Pro

Version: **19.0.1.9.11**

Odoo 19 Enterprise report customization for invoices and sales quotations.


## 19.0.1.9.11

- Corrige la advertencia de Odoo por dos campos de `res.company` con la misma etiqueta `Diseño de factura`.
- Mantiene `kabay_invoice_report_design` únicamente como campo técnico de compatibilidad, con una etiqueta distinta.
- Conserva `invoice_report_design` como el campo funcional mostrado al usuario.
- Incrementa la versión del manifiesto para forzar la actualización automática del módulo en Odoo.sh.


## 19.0.1.9.8

- Oculta en cotizaciones y órdenes de venta el campo editable de descripción
  de los productos cuando la compañía utiliza el Diseño 2.
- Mantiene disponible la descripción de los productos para las compañías que
  utilizan el Diseño 1.
- Conserva internamente la descripción estándar del producto y no altera los
  datos históricos de las líneas de venta.


## 19.0.1.9.3

- Restaura la descripción editable de cada línea de producto en facturas, cotizaciones y órdenes.
- Ya no elimina una segunda línea por parecerse al nombre del producto.
- Conserva todas las líneas adicionales de `line.name` como descripción real del usuario.
- Mantiene la primera línea como nombre principal y muestra el resto debajo, respetando saltos de línea.


## 19.0.1.9.2

- Agrega el vendedor de la factura en los dos diseños, debajo de la referencia de pago.
- Unifica la referencia de pago visible como `Número de factura - NCF` cuando ambos valores existen.
- Cambia la etiqueta fiscal del Diseño 1 de `Válida hasta` a `Vencimiento NCF`.
- Evita mostrar el vendedor duplicado en el bloque de datos del cliente del Diseño 1.

## 19.0.1.9.1

- Optimiza los tres reportes para impresión en formato US Letter.
- Amplía el área útil reduciendo márgenes laterales e inferior del formato de impresión.
- Aumenta de forma notable el tamaño del logo en facturas y cotización/orden.
- Incrementa la tipografía general, tablas, totales y datos de empresa para mejorar la lectura en papel.
- Aumenta el espaciado interno de filas para aprovechar mejor la página sin perder estabilidad de paginación.
- Mantiene las correcciones de compatibilidad con Chrome/PDFium y de página adicional del Diseño 1.

## 19.0.1.8.2

- Corrige la página adicional en blanco del Diseño 1 sin reintroducir los recuadros de Chrome/PDFium.

## 19.0.1.8.1

- Corrige artefactos de recuadros/líneas fantasma visibles en Chrome/PDFium al abrir o imprimir los PDF.
- Sustituye tablas estructurales colapsadas por renderizado separado sin bordes exteriores.
- Elimina bordes duplicados entre filas y celdas y normaliza trazos fraccionarios a 1 px.
- Mantiene únicamente los separadores horizontales necesarios en tablas de productos y totales.
- Agrega una línea divisora superior explícita al pie de página de cotizaciones y órdenes de venta.

## 19.0.1.8.0

- Aumentado el tamaño del logo en los dos diseños de factura y en cotización/orden.
- Agregado el RNC de la empresa debajo de la dirección en cotizaciones y órdenes.
- Aumentada la tipografía general de los tres PDF y reducidos espacios verticales innecesarios.
- Traducidas las etiquetas de fecha, vendedor y plazo de pago de la cotización al español.
- Resaltado visualmente el plazo de pago en los dos diseños de factura y en cotización/orden.
- Eliminadas líneas duplicadas en nombres/descripciones de productos sin perder descripciones adicionales reales.
- Modernizada la tabla de productos del Diseño 1 con mejor distribución, jerarquía y separadores de fila.
- Traducido el contador de páginas de la cotización a español.


## Invoices

- The existing company-selectable invoice layouts remain unchanged.
- The invoice router continues to use the company of each invoice.
- No additional invoice print action is created.

## Sales quotations

All quotations in state **Quotation** or **Quotation Sent** use the isolated
quotation design based on the supplied `S135643` PDF reference, regardless of
the quotation company.

Confirmed sales orders continue using Odoo's standard sales-order report.
The module inherits the existing `sale.report_saleorder_raw` wrapper and does
not add a duplicate option to the Print menu.

The quotation contains:

- Company logo and company address.
- Customer name, address, country, and RNC.
- Quotation number, date, salesperson, and payment terms.
- Description, quantity, unit price, and tax columns.
- Subtotal, ITBIS, and total.
- Company/order-specific commercial terms taken from the quotation Terms and Conditions field.
- Company/user email and company website in the footer when configured.

## Terms and conditions source

Quotations and both invoice designs read the terms directly from the company
configuration in Accounting > Configuration > Settings > Default Terms & Conditions.
No commercial terms are hardcoded in the report, and the generated `/terms` URL is
not printed as an additional duplicate block.

## 19.0.1.7.0

- El diseño de referencia ahora se utiliza tanto en cotizaciones como en órdenes de venta confirmadas, para todas las empresas.
- El título y la etiqueta de fecha cambian según el estado del documento.


## Cotizaciones y órdenes de venta

El diseño personalizado se aplica sin condiciones de estado a todos los documentos de `sale.order`: borrador, enviado, confirmado/bloqueado y cancelado, para todas las empresas.


## 19.0.1.7.0

- Added an isolated A4 paper format to the standard sale report action.
- Removed the large blank area that the standard external-header margin reserved above the quotation.
- Kept the same report action and the same custom layout for every sale order state.


## 19.0.1.7.0

- Increased quotation typography for better readability.
- Strengthened the light gray separators between every product row.
- Added a clear black separator above Subtotal.
- Added a clear black separator between ITBIS and Total.
- Kept the custom quotation layout active for every sales document state and every company.


## 19.0.1.7.0

- The quotation tax column now shows the assigned tax names.
- Lines without taxes show `Sin impuesto` instead of an empty cell.
- Payment terms use the order term, then the customer's company-dependent term, and finally `Pago Contado`.

## Integración con Configurar diseño del documento

Desde la versión 19.0.1.7.0, los dos diseños de factura y el reporte de cotización/orden consumen directamente los campos estándar de Odoo 19 configurados en **Ajustes > Configurar diseño del documento**:

- `res.company.logo`: logo del documento.
- `res.company.company_details`: bloque Dirección / datos de la empresa.
- `res.company.report_footer`: Pie de página.

Los cambios realizados por el usuario en ese asistente se reflejan automáticamente en los PDFs de la empresa correspondiente. El texto de cheques también usa dinámicamente `company.name` y ya no contiene un nombre de empresa fijo.


## Multi-company quotation terms

The quotation report now prints the Terms and Conditions stored on each sale order (`sale.order.note`), so different companies can use different terms while keeping the same quotation design.


## 19.0.1.9.5
- Cotizaciones y ambos diseños de factura leen directamente los Términos y Condiciones configurados en la compañía.
- Se eliminan términos comerciales estáticos del Diseño 2.
- Se evita imprimir una segunda sección con la URL `/terms`.
- Los términos se resuelven por compañía y al momento de imprimir, incluso para documentos existentes.

## 19.0.1.9.6

- Diseño 2: oculta en facturas y cotizaciones la descripción adicional escrita debajo del producto.
- Diseño 1: mantiene sin cambios el nombre y la descripción adicional del producto.
- El cambio afecta únicamente la salida de los reportes; no elimina ni modifica la descripción guardada en las líneas de venta o factura.


## 19.0.1.9.7

- Corrige el renderizado de cotizaciones al generar adjuntos desde Imprimir, Correo o WhatsApp.
- Añade el helper de compatibilidad `_kabay_report_tz` en `res.company`.
- Hace más robusta la lectura de términos y condiciones por empresa durante actualizaciones.
