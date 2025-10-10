# Cambios Lógicos: account_move_line.py

## 🔍 Descripción general
Se detectaron cambios críticos en el flujo de reinvoicing de gastos y en la estructura de métodos auxiliares. Los principales cambios incluyen: refactorización del método `_prepare_analytic_lines`, modificación en el retorno del método `_sale_get_invoice_price`, cambios en validaciones de estados de orden de venta, y actualización de referencias de campos relacionales.

---

## 🧠 Cambios lógicos detectados

### 1. **Refactorización completa de `_prepare_analytic_lines`**

**Estado:** Método eliminado completamente de la versión 18.2-marin

**Versión 18.2 (original):**
```python
def _prepare_analytic_lines(self):
    """Note: This method is called only on the move.line that having an analytic distribution, and
    so that should create analytic entries.
    """
    values_list = super(AccountMoveLine, self)._prepare_analytic_lines()
    move_to_reinvoice = self.env["account.move.line"]
    if len(values_list) > 0:
        for index, move_line in enumerate(self):
            values = values_list[index]
            if "so_line" not in values:
                if move_line._sale_can_be_reinvoice():
                    move_to_reinvoice |= move_line
    if move_to_reinvoice.filtered(
        lambda aml: not aml.move_id.reversed_entry_id and aml.product_id
    ):
        map_sale_line_per_move = (
            move_to_reinvoice._sale_create_reinvoice_sale_line()
        )
        for values in values_list:
            sale_line = map_sale_line_per_move.get(values.get("move_line_id"))
            if sale_line:
                values["so_line"] = sale_line.id
    return values_list
```

**Versión 18.2-marin:**
- Método completamente eliminado

**Impacto:**
- La lógica de generación de líneas analíticas con reinvoicing ya no se ejecuta en este modelo
- El flujo de vinculación automática de líneas de gasto a órdenes de venta durante la creación de líneas analíticas ha sido removido
- Esta funcionalidad probablemente se movió a otro modelo o se implementó de forma diferente en el core

---

### 2. **Nueva función auxiliar `_get_move_lines_to_reinvoice`**

**Estado:** Método añadido en la versión 18.2-marin

**Versión 18.2:** No existe

**Versión 18.2-marin (nueva):**
```python
def _get_move_lines_to_reinvoice(self, values_list):
    """Filter the move lines that can be reinvoiced: a cost (negative amount) analytic line without SO line but with a product can be reinvoiced"""
    move_to_reinvoice = self.env["account.move.line"]
    for index, values in enumerate(values_list):
        move_line = self[index]
        if "so_line" not in values:
            if move_line._sale_can_be_reinvoice():
                move_to_reinvoice |= move_line
    return move_to_reinvoice
```

**Impacto:**
- Nueva función modular que extrae la lógica de filtrado de líneas reinvoiceables
- Separa la responsabilidad de identificar qué líneas pueden ser reinvoiced
- Permite reutilización desde otros métodos (probablemente llamada desde el modelo padre o analytic.line)

---

### 3. **Cambio en validación de estados en `_sale_create_reinvoice_sale_line`**

**Versión 18.2 (original):**
```python
if sale_order.state in ("draft", "sent"):
    raise UserError(
        _(
            "The Sales Order %(order)s to be reinvoiced must be validated before registering expenses.",
            order=sale_order.name,
        )
    )
```

**Versión 18.2-marin (modificada):**
```python
if sale_order.state == "draft":
    raise UserError(
        _(
            "The Sales Order %(order)s to be reinvoiced must be validated before registering expenses.",
            order=sale_order.name,
        )
    )
```

**Impacto:**
- Ahora **se permite reinvoicear gastos en órdenes de venta con estado "sent"**
- Versión original bloqueaba tanto "draft" como "sent"
- Nueva lógica: solo las órdenes en estado "draft" son bloqueadas
- Esto facilita el flujo de gastos en órdenes cotizadas pero aún no confirmadas

---

### 4. **Cambio crítico en el retorno de `_sale_get_invoice_price`**

**Versión 18.2 (original):**
```python
def _sale_get_invoice_price(self, order):
    """Based on the current move line, compute the price to reinvoice the analytic line that is going to be created (so the
    price of the sale line).
    """
    self.ensure_one()
    unit_amount = self.quantity
    amount = (self.credit or 0.0) - (self.debit or 0.0)
    if self.product_id.expense_policy == "sales_price":
        return order.pricelist_id._get_product_price(
            self.product_id, 1.0, uom=self.product_uom_id, date=order.date_order
        )
    uom_precision_digits = self.env["decimal.precision"].precision_get(
        "Product Unit"
    )
    if float_is_zero(unit_amount, precision_digits=uom_precision_digits):
        return 0.0
    if (
        self.company_id.currency_id
        and amount
        and (self.company_id.currency_id == order.currency_id)
    ):
        return self.company_id.currency_id.round(abs(amount / unit_amount))
    price_unit = abs(amount / unit_amount)
    currency_id = self.company_id.currency_id
    if currency_id and currency_id != order.currency_id:
        price_unit = currency_id._convert(
            price_unit,
            order.currency_id,
            order.company_id,
            order.date_order or fields.Date.today(),
        )
    return price_unit
```

**Versión 18.2-marin (modificada):**
```python
def _sale_get_invoice_price(self, order):
    """Based on the current move line, compute the price to reinvoice the analytic line that is going to be created (so the
    price of the sale line)."""
    self.ensure_one()
    unit_amount = self.quantity
    amount = (self.credit or 0.0) - (self.debit or 0.0)
    if self.product_id.expense_policy == "sales_price":
        return order.pricelist_id._get_product_price(
            self.product_id, 1.0, uom=self.product_uom_id, date=order.date_order
        )
    uom_precision_digits = self.env["decimal.precision"].precision_get(
        "Product Unit"
    )
    if float_is_zero(unit_amount, precision_digits=uom_precision_digits):
        return 0.0
    if (
        self.company_id.currency_id
        and amount
        and (self.company_id.currency_id == order.currency_id)
    ):
        return self.company_id.currency_id.round(abs(amount / unit_amount))
    price_unit = abs(amount / unit_amount)
    currency_id = self.company_id.currency_id
    if currency_id and currency_id != order.currency_id:
        price_unit = currency_id._convert(
            price_unit,
            order.currency_id,
            order.company_id,
            order.date_order or fields.Date.today(),
        )
    return
```

**⚠️ CRÍTICO:**
- La última línea cambió de `return price_unit` a `return` (sin valor)
- **BUG INTRODUCIDO:** En el caso de conversión de moneda, el método ahora retorna `None` en lugar del precio convertido
- Esto causará errores en líneas de venta con precios incorrectos (None) cuando hay conversión de moneda
- **Probable error de refactorización automática o herramienta de formateo**

---

## ⚙️ Resumen de impactos funcionales

| Cambio | Impacto | Severidad |
|--------|---------|-----------|
| Eliminación de `_prepare_analytic_lines` | Flujo de reinvoicing movido a otro lugar | Alto |
| Nueva función `_get_move_lines_to_reinvoice` | Modularización, mejor separación de responsabilidades | Medio |
| Permitir estado "sent" en reinvoicing | Mayor flexibilidad en flujo de gastos | Medio |
| Bug en retorno de `_sale_get_invoice_price` | **Precios incorrectos con conversión de moneda** | **CRÍTICO** |

---

## 🐛 Bugs detectados

### **BUG CRÍTICO en `_sale_get_invoice_price` (línea 182)**
```python
return  # ← Debería ser: return price_unit
```

**Efecto:**
- Cuando se ejecuta conversión de moneda entre la moneda de la compañía y la moneda de la orden de venta, el método retorna `None`
- Esto causará que las líneas de venta creadas tengan `price_unit = None` o `0.0`
- **Pérdida de ingresos y datos incorrectos en reportes financieros**

**Solución recomendada:**
```python
return price_unit
```

---

## 📌 Conclusión

La versión 18.2-marin introduce una refactorización significativa del flujo de reinvoicing, eliminando el método `_prepare_analytic_lines` y añadiendo métodos auxiliares más modulares. Sin embargo, contiene un **bug crítico** en el cálculo de precios con conversión de moneda que debe ser corregido inmediatamente.

La lógica de negocio presenta un error que afecta la funcionalidad core del módulo de ventas y debe ser corregido antes de pasar a producción.
