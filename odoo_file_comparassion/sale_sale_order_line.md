# Cambios Lógicos: sale_order_line.py

## 🔍 Descripción general

Se han detectado 16 cambios lógicos significativos en el modelo `sale.order.line` entre las versiones 18.2 (original) y 18.2-marin (modificada). Los cambios más importantes incluyen:

- Reestructuración del método `create()` con nuevos hooks de extensibilidad
- Refactorización del método `write()` con métodos de validación separados
- Consolidación masiva de 4 métodos de cálculo de facturas en uno solo (con posible bug)
- Cambios en la validación de distribución analítica (ahora en todos los estados)
- Cambios en el cálculo de descuentos para combo items
- Nueva lógica para cantidad transferida (productos consu usan "stock_move")
- Bug potencial en `_compute_product_uom_qty()`
- Cambio radical en `_compute_product_uom_updatable()` (lógica invertida)
- Eliminación completa de métodos de catálogo de productos

---

## 🧠 Cambios lógicos detectados

### 1. **Reestructuración del método `create()` con nueva lógica de hooks**

**Versión 18.2 (original):**
```python
@api.model_create_multi
def create(self, vals_list):
    for vals in vals_list:
        if vals.get("display_type") or self.default_get(["display_type"]).get("display_type"):
            vals["product_uom_qty"] = 0.0
        if "technical_price_unit" in vals and "price_unit" not in vals:
            vals.pop("technical_price_unit")
    lines = super().create(vals_list)
    for line in lines:
        linked_line = line._get_line_linked()
        if linked_line:
            line.linked_line_id = linked_line
    if self.env.context.get("sale_no_log_for_new_lines"):
        return lines
    for line in lines:
        if line.product_id and line.state == "sale":
            msg = _("Extra line with %s", line.product_id.display_name)
            line.order_id.message_post(body=msg)
    return lines
```

**Versión 18.2-marin (modificada):**
```python
@api.model_create_multi
def create(self, vals_list):
    self._sanitize_create_display_type_vals(vals_list)
    res = super().create(vals_list)
    for line in res:
        linked_line = line._get_line_linked()
        if linked_line:
            line.linked_line_id = linked_line
    lines_confirmed = res.filtered(
        lambda l: l.state == "sale" and (not l.display_type)
    )
    lines_confirmed._hook_on_created_confirmed_lines()
    return res
```

**Impacto:**
- Se mueve la lógica de sanitización de valores a un método separado `_sanitize_create_display_type_vals()`
- Se cambia la lógica de logging: ahora solo filtra líneas confirmadas sin display_type
- Se introduce el método hook `_hook_on_created_confirmed_lines()` para lógica personalizable
- El método hook maneja el contexto `sale_no_log_for_new_lines` internamente
- Mayor modularidad y extensibilidad del código

---

### 2. **Refactorización completa del método `write()` con validaciones separadas**

**Versión 18.2 (original):**
```python
def write(self, values):
    if "display_type" in values and self.filtered(
        lambda line: line.display_type != values.get("display_type")
    ):
        raise UserError(...)
    if "product_id" in values and any(...):
        raise UserError(...)
    if "product_uom_qty" in values:
        precision = self.env["decimal.precision"].precision_get("Product Unit")
        self.filtered(...)._update_line_quantity(values)
    if ("technical_price_unit" in values and "price_unit" not in values
        and (not self.env.context.get("sale_write_from_compute"))):
        values.pop("technical_price_unit")
    protected_fields = self._get_protected_fields()
    if any(self.order_id.mapped("locked")) and any(...):
        # Validación de campos protegidos
        raise UserError(...)
    return super().write(values)
```

**Versión 18.2-marin (modificada):**
```python
def write(self, vals):
    self._check_write_protected_fields(vals)
    self._check_write_display_type(vals)
    self._check_write_product_updatable(vals)
    self._sanitize_write_vals_technical_price_unit(vals)
    previous_vals = self._prepare_write_previous_vals(vals)
    res = super().write(vals)
    confirmed_lines = self.filtered(
        lambda l: l.order_id.state == "sale" and (not l.display_type)
    )
    confirmed_lines._hook_on_written_confirmed_lines(vals, previous_vals)
    return res
```

**Impacto:**
- Se eliminó completamente la lógica de `_update_line_quantity()` del método write
- Se movieron todas las validaciones a métodos separados (mejor separación de responsabilidades)
- Se introduce `_prepare_write_previous_vals()` para capturar valores antes del write
- Se introduce hook `_hook_on_written_confirmed_lines()` que reemplaza la lógica anterior
- El logging de cantidades ahora se maneja en el hook, no directamente en write
- **PÉRDIDA DE FUNCIONALIDAD**: No se llama explícitamente a `_update_line_quantity()` en el nuevo código

---

### 3. **Cambio en la validación de distribución analítica - Filtro de estado eliminado**

**Versión 18.2 (original):**
```python
def _validate_analytic_distribution(self):
    for line in self.filtered(
        lambda l: not l.display_type and l.state in ["draft", "sent"]
    ):
        line._validate_distribution(
            **{
                "product": line.product_id.id,
                "business_domain": "sale_order",
                "company_id": line.company_id.id,
            }
        )
```

**Versión 18.2-marin (modificada):**
```python
def _validate_analytic_distribution(self):
    for line in self.filtered(lambda l: not l.display_type):
        line._validate_distribution(
            **{
                "product": line.product_id.id,
                "business_domain": "sale_order",
                "company_id": line.company_id.id,
            }
        )
```

**Impacto:**
- **CAMBIO IMPORTANTE**: Se eliminó el filtro `l.state in ["draft", "sent"]`
- Ahora se valida la distribución analítica en TODOS los estados, no solo draft y sent
- Esto podría causar validaciones adicionales en líneas confirmadas o canceladas
- Podría generar errores de validación que antes no ocurrían

---

### 4. **Consolidación de métodos de cálculo de facturas - CAMBIO MASIVO**

**Versión 18.2 (original):**
Tenía 4 métodos separados:
```python
@api.depends(
    "amount_invoiced_taxexc_taxinc_taxinc_taxinc",
    "price_unit",
    "product_id",
    "product_uom_qty",
    "qty_transfered",
    "state",
)
def _compute_amount_to_invoice_taxexc_taxinc_taxinc_taxinc_taxinc(self):
    # Lógica compleja de cálculo basada en precio unitario y descuentos
    ...

@api.depends("discount", "price_total", "product_uom_qty", "qty_invoiced_posted", "qty_transfered")
def _compute_amount_to_invoice_taxinc_taxinc(self):
    # Cálculo basado en precio total
    ...

@api.depends("invoice_line_ids", "invoice_line_ids.move_id.move_type", ...)
def _compute_invoice_amounts(self):  # Primera versión
    # Calcula amount_invoiced_taxexc usando price_subtotal
    ...

@api.depends("invoice_line_ids", "invoice_line_ids.move_id.state", ...)
def _compute_invoice_amounts(self):  # Segunda versión (duplicado)
    # Calcula amount_invoiced_taxinc usando price_total
    ...
```

**Versión 18.2-marin (modificada):**
```python
@api.depends(
    "invoice_line_ids.parent_state",
    "invoice_line_ids.product_uom_id",
    "invoice_line_ids.quantity",
    "price_subtotal",
    "price_total",
    "product_uom_qty",
    "qty_transfered",
    "state",
)
def _compute_invoice_amounts(self):
    """Compute the quantity invoiced. If case of a refund..."""
    combo_lines = set()
    for line in self.filtered(lambda l: not l.display_type):
        vals = {
            "qty_to_invoice": 0.0,
            "qty_invoiced": 0.0,
            "amount_to_invoice_taxinc": 0.0,
            "amount_to_invoice_taxexc": 0.0,
            "amount_invoiced_taxinc": 0.0,
            "amount_invoiced_taxexc": 0.0,
        }
        if line.state != "sale":
            line.write(vals)
            continue
        qty_policy = (
            line.product_uom_qty
            if line.product_id.invoice_policy == "order"
            else line.qty_transfered
        )
        vals.update({
            "qty_to_invoice": qty_policy,
            "amount_to_invoice_taxinc": line.price_subtotal,  # NOTA: taxinc usa price_subtotal
            "amount_to_invoice_taxexc": line.price_total,      # NOTA: taxexc usa price_total
        })
        if not line.invoice_line_ids:
            line.write(vals)
            continue
        for invoice_line in line._get_invoice_line_ids().filtered(
            lambda x: x.parent_state == "posted"
        ):
            invoice_date = invoice_line.move_id.invoice_date
            vals["qty_invoiced"] += (
                invoice_line.product_uom_id._compute_quantity(
                    invoice_line.quantity, line.product_uom_id
                )
                * -invoice_line.move_id.direction_sign
            )
            vals["amount_invoiced_taxexc"] += (
                invoice_line.currency_id._convert(
                    invoice_line.price_subtotal,
                    line.currency_id,
                    line.company_id,
                    invoice_date,
                )
                * -invoice_line.move_id.direction_sign
            )
            vals["amount_invoiced_taxinc"] += (
                invoice_line.currency_id._convert(
                    invoice_line.price_total,
                    line.currency_id,
                    line.company_id,
                    invoice_date,
                )
                * -invoice_line.move_id.direction_sign
            )
        if line.product_id.type == "combo" or (line.combo_item_id and line.linked_line_id):
            combo_lines.add(line.linked_line_id)
        else:
            vals["qty_to_invoice"] = max(0, vals["qty_to_invoice"] - vals["qty_invoiced"])
            vals["amount_to_invoice_taxexc"] = vals["qty_to_invoice"] * line.price_unit_discounted_taxexc
            vals["amount_to_invoice_taxinc"] = vals["qty_to_invoice"] * line.price_unit_discounted_taxinc
        line.write(vals)
    for combo_line in combo_lines:
        # Lógica de combo lines
        ...
```

**Impacto:**
- **ELIMINACIÓN MASIVA**: Se eliminaron 3 métodos separados de cálculo
- **CONSOLIDACIÓN**: Todo se calcula ahora en un solo método `_compute_invoice_amounts()`
- **BUG POTENCIAL**: Hay una inversión de nombres: `amount_to_invoice_taxinc` usa `price_subtotal` y `amount_to_invoice_taxexc` usa `price_total` (líneas 323-324)
- **CAMBIO EN DEPENDENCIAS**: Ahora depende de `parent_state` en lugar de `move_id.state`
- **NUEVA LÓGICA**: Solo considera facturas con `parent_state == "posted"` en lugar de lógica más compleja
- **NUEVA FUNCIONALIDAD**: Calcula `qty_to_invoice` dentro de este método (antes era método separado)
- **NUEVA LÓGICA**: Usa `price_unit_discounted_taxexc` y `price_unit_discounted_taxinc` para montos a facturar
- **ELIMINACIÓN**: Ya no maneja diferencias de descuentos entre líneas de factura y líneas de venta

---

### 5. **Eliminación completa de métodos `_compute_qty_invoiced()` y `_compute_qty_invoiced_posted()`**

**Versión 18.2 (original):**
```python
@api.depends("invoice_line_ids.move_id.state", "invoice_line_ids.quantity")
def _compute_qty_invoiced(self):
    """Compute the quantity invoiced. If case of a refund..."""
    for line in self:
        qty_invoiced = 0.0
        for invoice_line in line._get_invoice_line_ids():
            if (invoice_line.move_id.state != "cancel"
                or invoice_line.move_id.payment_state == "invoicing_legacy"):
                if invoice_line.move_id.move_type == "out_invoice":
                    qty_invoiced += invoice_line.product_uom_id._compute_quantity(
                        invoice_line.quantity, line.product_uom_id
                    )
                elif invoice_line.move_id.move_type == "out_refund":
                    qty_invoiced -= invoice_line.product_uom_id._compute_quantity(
                        invoice_line.quantity, line.product_uom_id
                    )
        line.qty_invoiced = qty_invoiced

@api.depends("invoice_line_ids.move_id.state", "invoice_line_ids.quantity")
def _compute_qty_invoiced_posted(self):
    """This method is almost identical to '_compute_qty_invoiced()'..."""
    for line in self:
        qty_invoiced_posted = 0.0
        for invoice_line in line._get_invoice_line_ids():
            if (invoice_line.move_id.state == "posted"
                or invoice_line.move_id.payment_state == "invoicing_legacy"):
                qty_unsigned = invoice_line.product_uom_id._compute_quantity(
                    invoice_line.quantity, line.product_uom_id
                )
                qty_signed = qty_unsigned * -invoice_line.move_id.direction_sign
                qty_invoiced_posted += qty_signed
        line.qty_invoiced_posted = qty_invoiced_posted
```

**Versión 18.2-marin (modificada):**
Estos métodos fueron COMPLETAMENTE ELIMINADOS. La lógica se integró en `_compute_invoice_amounts()`.

**Impacto:**
- **ELIMINACIÓN TOTAL**: Los métodos `_compute_qty_invoiced()` y `_compute_qty_invoiced_posted()` ya no existen
- **CONSOLIDACIÓN**: Su lógica ahora está dentro de `_compute_invoice_amounts()`
- **CAMBIO EN CÁLCULO**: La nueva versión usa `direction_sign` directamente en lugar de diferenciar move_type
- **SIMPLIFICACIÓN**: Ya no hay separación entre qty_invoiced y qty_invoiced_posted

---

### 6. **Eliminación del método `_compute_qty_to_invoice()` - Consolidado**

**Versión 18.2 (original):**
```python
@api.depends("product_uom_qty", "qty_invoiced", "qty_transfered", "state")
def _compute_qty_to_invoice(self):
    """Compute the quantity to invoice. If the invoice policy is order..."""
    combo_lines = set()
    for line in self:
        if line.state == "sale" and (not line.display_type):
            if line.product_id.type == "combo":
                combo_lines.add(line)
            elif line.product_id.invoice_policy == "order":
                line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
            else:
                line.qty_to_invoice = line.qty_transfered - line.qty_invoiced
            if line.combo_item_id and line.linked_line_id:
                combo_lines.add(line.linked_line_id)
        else:
            line.qty_to_invoice = 0
    for combo_line in combo_lines:
        if any(...):
            combo_line.qty_to_invoice = combo_line.product_uom_qty - combo_line.qty_invoiced
        else:
            combo_line.qty_to_invoice = 0
```

**Versión 18.2-marin (modificada):**
Este método fue ELIMINADO. La lógica se integró en `_compute_invoice_amounts()`.

**Impacto:**
- **ELIMINACIÓN**: El método dedicado `_compute_qty_to_invoice()` ya no existe
- **CAMBIO DE TRIGGER**: Las dependencias cambiaron completamente
- La lógica de combo lines se mantiene pero dentro de `_compute_invoice_amounts()`

---

### 7. **Cambio en `_compute_amounts()` - Ahora usa write() en lugar de asignación directa**

**Versión 18.2 (original):**
```python
@api.depends("discount", "price_unit", "product_uom_qty", "tax_ids")
def _compute_amounts(self):
    for line in self:
        base_line = line._prepare_base_line_for_taxes_computation()
        self.env["account.tax"]._add_tax_details_in_base_line(base_line, line.company_id)
        line.price_subtotal = base_line["tax_details"]["raw_total_excluded_currency"]
        line.price_total = base_line["tax_details"]["raw_total_included_currency"]
        line.price_tax = line.price_total - line.price_subtotal
```

**Versión 18.2-marin (modificada):**
```python
@api.depends("discount", "price_unit", "product_uom_qty", "tax_ids")
def _compute_amounts(self):
    for line in self.filtered(lambda l: not l.display_type):
        base_line = line._prepare_base_line_for_taxes_computation()
        self.env["account.tax"]._add_tax_details_in_base_line(base_line, line.company_id)
        vals = {
            "price_subtotal": base_line["tax_details"]["raw_total_excluded_currency"],
            "price_total": base_line["tax_details"]["raw_total_included_currency"],
            "price_tax": base_line["tax_details"]["raw_total_included_currency"]
                        - base_line["tax_details"]["raw_total_excluded_currency"],
            "price_unit_discounted_taxexc": (
                base_line["tax_details"]["raw_total_excluded_currency"] / base_line["quantity"]
                if base_line["quantity"] else 0.0
            ),
            "price_unit_discounted_taxinc": (
                base_line["tax_details"]["raw_total_included_currency"] / base_line["quantity"]
                if base_line["quantity"] else 0.0
            ),
        }
        line.write(vals)
```

**Impacto:**
- **NUEVO FILTRO**: Ahora solo computa para líneas sin display_type
- **NUEVOS CAMPOS COMPUTADOS**: Ahora también calcula `price_unit_discounted_taxexc` y `price_unit_discounted_taxinc`
- **CAMBIO EN MÉTODO**: Usa `write()` en lugar de asignación directa (esto puede tener implicaciones de rendimiento)
- **IMPACTO**: Los nuevos campos calculados se usan en `_compute_invoice_amounts()`

---

### 8. **Cambio en `_compute_analytic_distribution()` - Cambio de depends**

**Versión 18.2 (original):**
```python
@api.depends("order_id.partner_id", "product_id")
def _compute_analytic_distribution(self):
    for line in self:
        if not line.display_type:
            distribution = line.env["account.analytic.distribution.model"]._get_distribution(...)
            line.analytic_distribution = distribution or line.analytic_distribution
```

**Versión 18.2-marin (modificada):**
```python
@api.depends("partner_id", "product_id")
def _compute_analytic_distribution(self):
    for line in self.filtered(lambda l: not l.display_type):
        distribution = line.env["account.analytic.distribution.model"]._get_distribution(...)
        line.analytic_distribution = distribution or line.analytic_distribution
```

**Impacto:**
- **CAMBIO EN DEPENDENCIAS**: Ahora depende de `partner_id` directamente en lugar de `order_id.partner_id`
- **OPTIMIZACIÓN**: Usa filtered en lugar de if dentro del loop
- Podría afectar cuándo se recalcula la distribución analítica

---

### 9. **Cambio en lógica de cálculo de descuento**

**Versión 18.2 (original):**
```python
@api.depends("product_id", "product_uom_id", "product_uom_qty")
def _compute_discount(self):
    discount_enabled = self.env["product.pricelist.item"]._is_discount_feature_enabled()
    for line in self:
        if not line.product_id or line.display_type:
            line.discount = 0.0
        if not (line.order_id.pricelist_id and discount_enabled):
            continue
        if line.combo_item_id:
            line.discount = line._get_line_linked().discount
            continue
        line.discount = 0.0
        if not line.pricelist_item_id._show_discount():
            continue
        line = line.with_company(line.company_id)
        pricelist_price = line._get_pricelist_price()
        base_price = line._get_pricelist_price_before_discount()
        if base_price != 0:
            discount = (base_price - pricelist_price) / base_price * 100
            if discount > 0 and base_price > 0 or (discount < 0 and base_price < 0):
                line.discount = discount
```

**Versión 18.2-marin (modificada):**
```python
@api.depends("product_id", "product_uom_id", "product_uom_qty")
def _compute_discount(self):
    discount_enabled = self.env["product.pricelist.item"]._is_discount_feature_enabled()
    for line in self:
        if (line.display_type or not line.product_id
            or (not (line.order_id.pricelist_id and discount_enabled))):
            line.discount = False
            continue
        line.discount = 0.0
        if not line.pricelist_item_id._show_discount():
            continue
        line = line.with_company(line.company_id)
        pricelist_price = line._get_pricelist_price()
        base_price = line._get_pricelist_price_before_discount()
        if base_price != 0:
            discount = (base_price - pricelist_price) / base_price * 100
            if discount > 0 and base_price > 0 or (discount < 0 and base_price < 0):
                line.discount = discount
```

**Impacto:**
- **ELIMINACIÓN**: Se eliminó la lógica especial para combo_item_id
- **CAMBIO DE VALOR**: Ahora asigna `False` en lugar de `0.0` cuando no hay producto/pricelist
- **SIMPLIFICACIÓN**: La condición inicial se consolidó en una sola expresión
- **PÉRDIDA DE FUNCIONALIDAD**: Ya no copia el descuento de la línea vinculada para combo items

---

### 10. **Cambio en `_compute_product_uom_qty()` - Lógica completamente diferente**

**Versión 18.2 (original):**
```python
@api.depends("display_type", "product_id")
def _compute_product_uom_qty(self):
    for line in self:
        if line.display_type:
            line.product_uom_qty = 0.0
```

**Versión 18.2-marin (modificada):**
```python
@api.depends("product_id")
def _compute_product_uom_qty(self):
    for line in self:
        if line.product_id and (not line.product_uom_qty):
            line.product_uom_qty = 1.0
        else:
            line.product_qty = False
```

**Impacto:**
- **CAMBIO RADICAL**: La lógica es completamente opuesta
- **ELIMINACIÓN**: Ya no depende de `display_type`
- **NUEVA LÓGICA**: Si hay producto pero no hay cantidad, asigna 1.0
- **BUG POTENCIAL**: Asigna a `product_qty` (que probablemente no existe) en lugar de `product_uom_qty`
- **POSIBLE ERROR**: La línea `line.product_qty = False` parece un typo (debería ser product_uom_qty)

---

### 11. **Cambio en `_compute_product_uom_updatable()` - Nueva lógica basada en locked**

**Versión 18.2 (original):**
```python
@api.depends("state")
def _compute_product_uom_updatable(self):
    for line in self:
        line.product_uom_updatable = line.ids and line.state in ["sale", "cancel"]
```

**Versión 18.2-marin (modificada):**
```python
@api.depends("locked", "state")
def _compute_product_uom_updatable(self):
    for line in self:
        line.product_uom_updatable = (
            not line.ids or line.state == "draft" or (not line.locked)
        )
```

**Impacto:**
- **CAMBIO COMPLETO DE LÓGICA**: Completamente invertida
- **NUEVA DEPENDENCIA**: Ahora depende de `locked` además de `state`
- **ORIGINAL**: Updatable si tiene ids Y state in ["sale", "cancel"]
- **NUEVO**: Updatable si NO tiene ids O state == "draft" O NO está locked
- **IMPACTO**: Comportamiento completamente diferente

---

### 12. **Eliminación completa de dependencia en `_compute_qty_transfered()`**

**Versión 18.2 (original):**
```python
@api.depends(
    "analytic_line_ids.product_uom_id",
    "analytic_line_ids.so_line",
    "analytic_line_ids.unit_amount",
    "qty_transfered_method",
)
def _compute_qty_transfered(self):
    # ... lógica
```

**Versión 18.2-marin (modificada):**
```python
@api.depends("qty_transfered_method")
def _compute_qty_transfered(self):
    # ... lógica (idéntica)
```

**Impacto:**
- **SIMPLIFICACIÓN**: Eliminó las dependencias de analytic_line_ids
- La lógica interna es idéntica
- Podría causar que no se recalcule cuando cambien líneas analíticas

---

### 13. **Cambio significativo en `_compute_qty_transfered_method()` - Nueva lógica**

**Versión 18.2 (original):**
```python
@api.depends("is_expense")
def _compute_qty_transfered_method(self):
    """Sale module compute delivered qty for product [('type', 'in', ['consu']), ('service_type', '=', 'manual')]
        - consu + expense_policy : analytic (sum of analytic unit_amount)
        - consu + no expense_policy : manual (set manually on SOL)
        - service (+ service_type='manual', the only available option) : manual

    This is true when only sale is installed: sale_stock redifine the behavior for 'consu' type,
    and sale_timesheet implements the behavior of 'service' + service_type=timesheet.
    """
    for line in self:
        if line.is_expense:
            line.qty_transfered_method = "analytic"
        else:
            line.qty_transfered_method = "manual"
```

**Versión 18.2-marin (modificada):**
```python
@api.depends("is_expense", "product_id")
def _compute_qty_transfered_method(self):
    """Sale module compute delivered qty for product [('type', 'in', ['consu']), ('service_type', '=', 'manual')]
    -consu + expense_policy : analytic (sum of analytic unit_amount)
    -consu + no expense_policy : manual (set manually on SOL)
    -service (+ service_type='manual', the only available option) : manual

    This is true when only sale is installed: sale_stock redifine the behavior for 'consu' type,
    and sale_timesheet implements the behavior of 'service' + service_type=timesheet.
    """
    for line in self:
        if line.is_expense:
            line.qty_transfered_method = "analytic"
        elif line.product_id and line.product_type == "service":
            line.qty_transfered_method = "manual"
        elif line.product_id and line.product_type == "consu":
            line.qty_transfered_method = "stock_move"
        else:
            line.qty_transfered_method = False
```

**Impacto:**
- **NUEVA DEPENDENCIA**: Ahora depende también de `product_id`
- **NUEVA LÓGICA**: Diferencia entre productos tipo "service" y "consu"
- **NUEVOS VALORES**: Ahora puede asignar "stock_move" y False, no solo "manual"
- **CAMBIO IMPORTANTE**: Para productos consu no-expense, ahora es "stock_move" en lugar de "manual"
- Esto afectará cómo se calcula la cantidad transferida para diferentes tipos de productos

---

### 14. **Eliminación de métodos `_set_analytic_distribution()` y `_onchange_product_id()`**

**Versión 18.2 (original):**
```python
# =============================================================================
# INVERSE METHODS
# =============================================================================

def _set_analytic_distribution(self, inv_line_vals, **optional_values):
    if self.analytic_distribution and (not self.display_type):
        inv_line_vals["analytic_distribution"] = self.analytic_distribution

# En onchange
@api.onchange("product_id")
def _onchange_product_id(self):
    if not self.product_id:
        return
    self._reset_price_unit()
```

**Versión 18.2-marin (modificada):**
Ambos métodos fueron COMPLETAMENTE ELIMINADOS.

**Impacto:**
- **ELIMINACIÓN**: `_set_analytic_distribution()` ya no existe
- **ELIMINACIÓN**: `_onchange_product_id()` que llamaba a `_reset_price_unit()` ya no existe
- Podría afectar la propagación de distribución analítica a líneas de factura
- El onchange de producto ya no resetea el precio automáticamente

---

### 15. **Eliminación del método `_reset_price_unit()` y nuevos métodos de hook**

**Versión 18.2 (original):**
```python
def _reset_price_unit(self):
    self.ensure_one()
    line = self.with_company(self.company_id)
    price = line._get_price_display()
    product_taxes = line.product_id.taxes_id._filter_taxes_by_company(line.company_id)
    price_unit = line.product_id._get_tax_included_unit_price_from_price(
        price,
        product_taxes=product_taxes,
        fiscal_position=line.order_id.fiscal_position_id,
    )
    line.update({"price_unit": price_unit, "technical_price_unit": price_unit})

def _update_line_quantity(self, values):
    orders = self.mapped("order_id")
    for order in orders:
        line_idss = self.filtered(lambda x: x.order_id == order)
        msg = Markup("<b>%s</b><ul>") % _("The ordered quantity has been updated.")
        for line in line_idss:
            if ("product_id" in values and values["product_id"] != line.product_id.id):
                continue
            msg += Markup("<li> %s: <br/>") % line.product_id.display_name
            msg += _("Ordered Quantity: %(old_qty)s -> %(new_qty)s",
                old_qty=line.product_uom_qty, new_qty=values["product_uom_qty"]
            ) + Markup("<br/>")
            if line.product_id.type == "consu":
                msg += _("Delivered Quantity: %s", line.qty_transfered) + Markup("<br/>")
            msg += _("Invoiced Quantity: %s", line.qty_invoiced) + Markup("<br/>")
        msg += Markup("</ul>")
        order.message_post(body=msg)
```

**Versión 18.2-marin (modificada):**
```python
def _hook_on_created_confirmed_lines(self):
    """Hook method to be able to add custom logic when a line is created and confirmed"""
    if self.env.context.get("sale_no_log_for_new_lines"):
        pass
    for line in self:
        msg = _(f"Extra line with: {line.product_id.display_name}")
        line.order_id.message_post(body=msg)

def _hook_on_written_confirmed_lines(self, write_vals, previous_vals):
    self._log_to_order_quantities_updated(write_vals, previous_vals)

def _log_to_order_quantities_updated(self, write_vals, previous_vals):
    precision = self.env["decimal.precision"].precision_get("Product Unit")
    orders = self.mapped("order_id")
    for order in orders:
        order_lines = self.filtered(lambda l: l.order_id == order)
        order_qty_updated_msg = Markup("<b>%s</b><br/><ul>") % _("The ordered quantities have been updated.")
        flag = False
        for line in order_lines:
            if ("product_id" in write_vals and write_vals["product_id"] != line.product_id.id):
                continue
            line_flag = False
            line_qty_updated_msg = Markup(f"<li>{line.product_id.display_name}:<br/>")
            if ("product_uom_qty" in write_vals
                and float_compare(
                    previous_vals[line.id].get("product_uom_qty"),
                    line.product_uom_qty,
                    precision_digits=precision,
                ) != 0):
                line_flag = True
                line_qty_updated_msg += _(
                    f"-Ordered quantity: {previous_vals[line.id].get('product_uom_qty')} -> {line.product_uom_qty}"
                ) + Markup("<br/>")
                if line.product_id.type == "consu":
                    line_qty_updated_msg += _(f"-Delivered quantity: {line.qty_transfered}") + Markup("<br/>")
                line_qty_updated_msg += _(f"-Invoiced quantity: {line.qty_invoiced}") + Markup("<br/>")
            line_qty_updated_msg += Markup("</li>")
            if line_flag:
                order_qty_updated_msg += line_qty_updated_msg
                flag = True
        order_qty_updated_msg += Markup("</ul>")
        if flag:
            order.message_post(body=order_qty_updated_msg)
```

**Impacto:**
- **ELIMINACIÓN**: `_reset_price_unit()` ya no existe (su lógica se inline en `_compute_price_unit()`)
- **ELIMINACIÓN**: `_update_line_quantity()` ya no existe
- **NUEVOS MÉTODOS**: `_hook_on_created_confirmed_lines()`, `_hook_on_written_confirmed_lines()`, `_log_to_order_quantities_updated()`
- **CAMBIO EN LÓGICA**: Ahora usa un flag para solo postear mensaje si hubo cambios
- **CAMBIO EN MENSAJE**: Ahora usa f-strings y compara con previous_vals
- **NUEVA FUNCIONALIDAD**: Usa `float_compare` para detectar cambios reales en cantidad

---

### 16. **Eliminación completa de métodos del catálogo de productos**

**Versión 18.2 (original):**
```python
# =============================================================================
# PRODUCT_CATALOG METHODS
# =============================================================================

def _get_product_catalog_lines_data(self, **kwargs):
    """Return information about sale order lines in `self`..."""
    if len(self) == 1:
        res = {
            "quantity": self.product_uom_qty,
            "price": self.price_unit,
            "readOnly": self.order_id._is_readonly()
                or self.product_id.sale_line_warn == "block"
                or bool(self.combo_item_id),
        }
        if (self.product_id.sale_line_warn != "no-message"
            and self.product_id.sale_line_warn_msg):
            res["warning"] = self.product_id.sale_line_warn_msg
        return res
    elif self:
        self.product_id.ensure_one()
        line_ids = self[0]
        order = line_ids.order_id
        res = {
            "readOnly": True,
            "price": order.pricelist_id._get_product_price(...),
            "quantity": sum(self.mapped(lambda line: ...)),
        }
        if (self.product_id.sale_line_warn != "no-message"
            and self.product_id.sale_line_warn_msg):
            res["warning"] = self.product_id.sale_line_warn_msg
        return res
    else:
        return {"quantity": 0}

@api.readonly
def action_add_from_catalog(self):
    order = self.env["sale.order"].browse(self.env.context.get("order_id"))
    return order.with_context(child_field="line_ids").action_add_from_catalog()
```

**Versión 18.2-marin (modificada):**
Toda la sección "PRODUCT_CATALOG METHODS" fue COMPLETAMENTE ELIMINADA.

**Impacto:**
- **ELIMINACIÓN MASIVA**: Se eliminaron `_get_product_catalog_lines_data()` y `action_add_from_catalog()`
- **PÉRDIDA DE FUNCIONALIDAD**: Ya no hay soporte para catálogo de productos desde sale.order.line
- Cualquier código que use estos métodos se romperá
- La funcionalidad del catálogo de productos probablemente se movió a otro lugar

---

## ⚙️ Resumen de impactos funcionales

| Cambio | Impacto | Severidad |
|--------|---------|-----------|
| Consolidación de métodos de facturación | Se eliminaron 4 métodos y se unificaron en 1. Posible bug de inversión taxinc/taxexc | Alto |
| Eliminación de validación de estado en distribución analítica | Ahora valida en todos los estados, no solo draft/sent | Alto |
| Cambio en `_compute_qty_transfered_method()` | Productos consu ahora usan "stock_move" en lugar de "manual" | Alto |
| Eliminación de métodos del catálogo de productos | Pérdida completa de funcionalidad de catálogo | Alto |
| Bug en `_compute_product_uom_qty()` | Asigna a campo `product_qty` que probablemente no existe | Alto |
| Método `write()` refactorizado | Ya no llama explícitamente a `_update_line_quantity()` | Medio |
| Cambio en lógica de descuento combo_item | Ya no copia descuento de línea vinculada | Medio |
| Eliminación de `_set_analytic_distribution()` | Podría afectar propagación a facturas | Medio |
| Cambio en `_compute_product_uom_updatable()` | Lógica completamente invertida | Alto |
| Nuevos métodos hook | Mayor extensibilidad con hooks en create/write | Bajo |
| Cambio en `_compute_amounts()` | Usa write() y calcula nuevos campos discounted | Medio |
| Cambio en `_compute_analytic_distribution()` | Depende de partner_id directo | Bajo |
| Eliminación de `_onchange_product_id()` | Ya no resetea precio en onchange | Bajo |
| Eliminación de `_reset_price_unit()` | Lógica inline en compute | Bajo |
| Eliminación dependencias en `_compute_qty_transfered()` | Ya no depende de analytic_line_ids | Medio |

---

## 📌 Conclusión

Se han identificado **16 cambios lógicos significativos** en el archivo `sale_order_line.py`. Los cambios más críticos son:

### Cambios de Alto Impacto:

1. **Consolidación masiva de métodos de facturación**: Se eliminaron 4 métodos separados (`_compute_amount_to_invoice_taxexc_*`, `_compute_amount_to_invoice_taxinc_*`, `_compute_qty_invoiced()`, `_compute_qty_invoiced_posted()`, `_compute_qty_to_invoice()`) y se unificaron en un solo `_compute_invoice_amounts()`. Esto incluye un posible bug donde `amount_to_invoice_taxinc` usa `price_subtotal` y `amount_to_invoice_taxexc` usa `price_total` (inversión de nombres).

2. **Eliminación de filtro de estado en validación analítica**: Ahora se valida la distribución analítica en todos los estados en lugar de solo "draft" y "sent", lo que podría causar validaciones inesperadas en líneas confirmadas o canceladas.

3. **Cambio en método de cantidad transferida**: Para productos consumibles no-expense, ahora usa "stock_move" en lugar de "manual", lo que cambia fundamentalmente cómo se calcula la cantidad entregada.

4. **Eliminación completa de funcionalidad de catálogo de productos**: Los métodos `_get_product_catalog_lines_data()` y `action_add_from_catalog()` fueron completamente eliminados.

5. **Bug potencial en `_compute_product_uom_qty()`**: Asigna a `product_qty` en lugar de `product_uom_qty`, lo que probablemente es un typo.

6. **Cambio radical en `_compute_product_uom_updatable()`**: La lógica se invirtió completamente, afectando cuándo el campo UOM es editable.

### Cambios de Medio Impacto:

- Refactorización del método `write()` con pérdida de llamada explícita a `_update_line_quantity()`
- Eliminación de lógica de descuento para combo_item_id
- Eliminación de `_set_analytic_distribution()` y `_onchange_product_id()`
- Cambio en `_compute_amounts()` que ahora usa `write()` en lugar de asignación directa
- Eliminación de dependencias de `analytic_line_ids` en `_compute_qty_transfered()`

### Mejoras:

- Mayor modularidad con métodos de validación separados en `write()`
- Introducción de hooks para extensibilidad (`_hook_on_created_confirmed_lines()`, `_hook_on_written_confirmed_lines()`)
- Mejor tracking de cambios con `_prepare_write_previous_vals()`
- Logging más inteligente que solo postea cuando hay cambios reales usando `float_compare`

**Recomendaciones**:
- Revisar el posible bug de inversión taxinc/taxexc en `_compute_invoice_amounts()`
- Corregir el bug de `product_qty` en `_compute_product_uom_qty()`
- Verificar que la validación analítica en todos los estados no cause problemas
- Confirmar que el cambio de "manual" a "stock_move" para productos consu es intencional
