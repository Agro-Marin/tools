# Cambios Lógicos: account_move.py

## 🔍 Descripción general
Se detectó un cambio crítico en la lógica de validación de crédito del cliente. El cálculo ahora considera montos con impuestos incluidos en lugar de montos sin impuestos, lo que hace la validación más estricta y realista.

---

## 🧠 Cambios lógicos detectados

### 1. **Cambio crítico en cálculo de monto a facturar en `_get_partner_credit_warning_exclude_amount`**

**Versión 18.2 (original):**
```python
def _get_partner_credit_warning_exclude_amount(self):
    exclude_amount = super()._get_partner_credit_warning_exclude_amount()
    for order in self.line_ids.sale_line_ids.order_id:
        order_amount = min(
            self._get_sale_order_invoiced_amount(order), order.amount_to_invoice
        )
        order_amount_company = order.currency_id._convert(
            max(order_amount, 0),
            self.company_id.currency_id,
            self.company_id,
            fields.Date.context_today(self),
        )
        exclude_amount += order_amount_company
    return exclude_amount
```

**Versión 18.2-marin (modificada):**
```python
def _get_partner_credit_warning_exclude_amount(self):
    exclude_amount = super()._get_partner_credit_warning_exclude_amount()
    for order in self.line_ids.sale_line_ids.order_id:
        order_amount = min(
            self._get_sale_order_invoiced_amount(order),
            order.amount_to_invoice_taxinc,
        )
        order_amount_company = order.currency_id._convert(
            max(order_amount, 0),
            self.company_id.currency_id,
            self.company_id,
            fields.Date.context_today(self),
        )
        exclude_amount += order_amount_company
    return exclude_amount
```

**Impacto:**
- Campo cambió de `order.amount_to_invoice` a `order.amount_to_invoice_taxinc`
- **Diferencia funcional importante:**
  - `amount_to_invoice`: Monto sin impuestos pendiente de facturar
  - `amount_to_invoice_taxinc`: Monto **CON impuestos** pendiente de facturar
- **Efecto:** La advertencia de crédito del cliente ahora excluye montos con impuestos incluidos
- **Impacto en negocio:** Cálculo de crédito disponible del cliente es más preciso al considerar el monto total (con impuestos) que será cobrado
- **Cambio en lógica financiera**: Ahora la validación de límite de crédito es más estricta/realista al incluir impuestos

---

### 2. **Simplificación de filtro en `_get_sale_order_invoiced_amount`**

**Versión 18.2 (original):**
```python
def _get_sale_order_invoiced_amount(self, order):
    """
    Consider all lines on any invoice in self that stem from the sales order `order`. (All those invoices belong to order.company_id)
    This function returns the sum of the totals of all those lines.
    Note that this amount may be bigger than `order.amount_total`.
    """
    order_amount = 0
    for invoice in self:
        prices = sum(
            invoice.line_ids.filtered(
                lambda x: x.display_type not in ("line_note", "line_section")
                and order in x.sale_line_ids.order_id
            ).mapped("price_total")
        )
        order_amount += invoice.currency_id._convert(
            prices * -invoice.direction_sign,
            order.currency_id,
            invoice.company_id,
            invoice.date,
        )
    return order_amount
```

**Versión 18.2-marin (modificada):**
```python
def _get_sale_order_invoiced_amount(self, order):
    """Consider all lines on any invoice in self that stem from the sales order `order`.
    (All those invoices belong to order.company_id)
    This function returns the sum of the totals of all those lines.
    Note that this amount may be bigger than `order.amount_total`."""
    order_amount = 0
    for invoice in self:
        prices = sum(
            invoice.line_ids.filtered(
                lambda l: order in l.sale_line_ids.order_id
            ).mapped("price_total")
        )
        order_amount += invoice.currency_id._convert(
            prices * -invoice.direction_sign,
            order.currency_id,
            invoice.company_id,
            invoice.date,
        )
    return order_amount
```

**Impacto:**
- **Filtro eliminado:** Ya no se excluyen líneas con `display_type` en `("line_note", "line_section")`
- **Cambio en cálculo:**
  - Versión original: Solo suma líneas de producto/servicio (excluye notas y secciones)
  - Versión nueva: Suma **todas** las líneas de factura relacionadas con la orden
- **Posible impacto:** Si las líneas de tipo nota o sección tienen `price_total != 0`, ahora se incluirán en el cálculo
- **Análisis:** En la práctica, las líneas de tipo `line_note` y `line_section` **normalmente tienen `price_total = 0`**, por lo que este cambio probablemente no afecta el resultado
- **Razón del cambio:** Simplificación del código asumiendo que líneas de display ya tienen precio 0
- **Riesgo:** Si por alguna razón una línea de sección/nota tiene precio, ahora se contaría (bug potencial en caso de datos inconsistentes)

---

## ⚙️ Resumen de impactos funcionales

| Cambio | Impacto | Severidad |
|--------|---------|-----------|
| Cambio `amount_to_invoice` → `amount_to_invoice_taxinc` | **Cálculo de crédito ahora incluye impuestos** | **Alto** |
| Eliminación de filtro `display_type` en suma de precios | Simplificación, riesgo bajo si datos son consistentes | Medio |

---

## 🎯 Cambios de lógica de negocio críticos

### **1. Validación de límite de crédito ahora considera impuestos**

En `_get_partner_credit_warning_exclude_amount`, el cambio de `amount_to_invoice` a `amount_to_invoice_taxinc` significa que:

**Comportamiento anterior:**
- El sistema calculaba el crédito disponible basándose en el monto sin impuestos

**Comportamiento nuevo:**
- El sistema calcula el crédito disponible basándose en el monto con impuestos incluidos

**Ejemplo práctico:**
- Orden de venta: $1000 + 16% IVA = $1160 total
- Crédito del cliente: $2000
- **Versión 18.2:** Excluye $1000 → Cliente tiene $1000 disponible
- **Versión 18.2-marin:** Excluye $1160 → Cliente tiene $840 disponible

**Impacto:** La validación de límite de crédito es más estricta y realista, previniendo sobregiros al considerar el monto total que el cliente pagará.

---

### **2. Cálculo de monto facturado ahora incluye líneas de display (potencial)**

La eliminación del filtro `display_type not in ("line_note", "line_section")` en `_get_sale_order_invoiced_amount` significa:

**Comportamiento anterior:**
- Solo se sumaban líneas de producto/servicio
- Líneas de nota y sección se excluían explícitamente

**Comportamiento nuevo:**
- Se suman **todas** las líneas relacionadas con la orden
- Si por alguna razón una línea de nota/sección tiene precio, ahora se incluirá

**Riesgo:**
- En teoría, las líneas de display no deberían tener precio
- Si hay datos inconsistentes (líneas de nota con precio), el cálculo será incorrecto
- **Recomendación:** Verificar que no existan registros con `display_type in ('line_note', 'line_section')` y `price_total != 0`

---

## 📌 Conclusión

La versión 18.2-marin introduce dos cambios lógicos en el módulo de account_move relacionados con el cálculo de montos facturados:

**Puntos clave:**
1. ⚠️ Validación de crédito ahora más estricta (incluye impuestos)
2. ⚠️ Simplificación de filtro puede causar problemas si hay datos inconsistentes

**Sin bugs críticos detectados**, pero el cambio en la validación de crédito puede impactar el flujo de aprobación de órdenes si los clientes están cerca de su límite de crédito.
