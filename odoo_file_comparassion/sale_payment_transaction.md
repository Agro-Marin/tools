# Cambios Lógicos: payment_transaction.py

## 🔍 Descripción general
Se detectaron cambios importantes en el flujo de confirmación de órdenes, condiciones de envío de emails y contexto de ejecución. Estos cambios afectan el comportamiento del procesamiento de pagos y la generación automática de facturas.

---

## 🧠 Cambios lógicos detectados

### 1. **Cambio en filtro de estados de órdenes en `_check_amount_and_confirm_order`**

**Versión 18.2 (original):**
```python
def _check_amount_and_confirm_order(self):
    confirmed_orders = self.env["sale.order"]
    for tx in self:
        if len(tx.sale_order_ids) == 1:
            quotation = tx.sale_order_ids.filtered(
                lambda so: so.state in ("draft", "sent")
            )
            if quotation and quotation._is_confirmation_amount_reached():
                quotation.with_context(send_email=True).action_confirm()
                confirmed_orders |= quotation
    return confirmed_orders
```

**Versión 18.2-marin (modificada):**
```python
def _check_amount_and_confirm_order(self):
    confirmed_orders = self.env["sale.order"]
    for tx in self:
        if len(tx.sale_order_ids) == 1:
            quotation = tx.sale_order_ids.filtered(lambda so: so.state == "draft")
            if quotation and quotation._is_confirmation_amount_reached():
                quotation.with_context(send_email=True).action_confirm()
                confirmed_orders |= quotation
    return confirmed_orders
```

**Impacto:**
- El filtro cambió de `("draft", "sent")` a solo `"draft"`
- **Las órdenes en estado "sent" ya no se confirman automáticamente al recibir el pago**
- Versión original: Confirmaba órdenes en estado "draft" o "sent"
- Versión nueva: Solo confirma órdenes en estado "draft"
- **Impacto funcional:** Cambio significativo en el flujo de ventas - las cotizaciones enviadas no se confirmarán automáticamente
- **Razón probable:** En Odoo 18, el estado "sent" podría requerir aprobación manual antes de confirmar

---

### 2. **Cambio en filtro de estados de órdenes en `_post_process` (transacciones pending)**

**Versión 18.2 (original):**
```python
for pending_tx in self.filtered(lambda tx: tx.state == "pending"):
    super(PaymentTransaction, pending_tx)._post_process()
    sales_orders = pending_tx.sale_order_ids.filtered(
        lambda so: so.state in ["draft", "sent"]
    )
```

**Versión 18.2-marin (modificada):**
```python
for pending_tx in self.filtered(lambda tx: tx.state == "pending"):
    super(PaymentTransaction, pending_tx)._post_process()
    sales_orders = pending_tx.sale_order_ids.filtered(
        lambda so: so.state == "draft"
    )
```

**Impacto:**
- El filtro cambió de `["draft", "sent"]` a solo `"draft"`
- **Las órdenes en estado "sent" ya no se procesan en transacciones pendientes**
- Esto afecta el envío de emails de cotización para pagos pendientes
- **Impacto funcional:** Comportamiento más restrictivo en el procesamiento de pagos pendientes

---

### 3. **Eliminación de condición de contexto en `_post_process`**

**Versión 18.2 (original):**
```python
if auto_invoice and (
    not self.env.context.get("skip_sale_auto_invoice_send")
):
    if str2bool(
        self.env["ir.config_parameter"]
        .sudo()
        .get_param("sale.async_emails")
    ) and (
        send_invoice_cron := self.env.ref(
            "sale.send_invoice_cron", raise_if_not_found=False
        )
    ):
        send_invoice_cron._trigger()
    else:
        self._send_invoice()
```

**Versión 18.2-marin (modificada):**
```python
if auto_invoice:
    if str2bool(
        self.env["ir.config_parameter"]
        .sudo()
        .get_param("sale.async_emails")
    ) and (
        send_invoice_cron := self.env.ref(
            "sale.send_invoice_cron", raise_if_not_found=False
        )
    ):
        send_invoice_cron._trigger()
    else:
        self._send_invoice()
```

**Impacto:**
- Se removió la condición `not self.env.context.get("skip_sale_auto_invoice_send")`
- **El envío automático de facturas ya no puede ser deshabilitado por contexto**
- Versión original: Permitía saltar el envío de emails con el flag de contexto
- Versión nueva: Siempre envía emails si `auto_invoice` está activo
- **Impacto funcional:** Pérdida de flexibilidad para deshabilitar envío de emails en casos específicos
- **Riesgo:** Si algún proceso externo dependía de este flag para evitar envío de emails, ahora se enviarán

---

### 4. **Cambio en referencia de objeto `self.env` → `tx.env` en `_send_invoice`**

**Versión 18.2 (original):**
```python
def _send_invoice(self):
    for tx in self.with_user(SUPERUSER_ID):
        # ...
        tx.env["account.move.send"]._generate_and_send_invoices(
            invoice_to_send, **send_context
        )
```

**Versión 18.2-marin (modificada):**
```python
def _send_invoice(self):
    for tx in self.with_user(SUPERUSER_ID):
        # ...
        self.env["account.move.send"]._generate_and_send_invoices(
            invoice_to_send, **send_context
        )
```

**Impacto:**
- Cambió de `tx.env` a `self.env`
- **Cambio en el contexto de ejecución del envío de facturas**
- `tx.env` usa el entorno de la transacción iterada (con contexto de compañía)
- `self.env` usa el entorno del recordset original
- **Impacto funcional:** El envío de facturas ahora usa el contexto original en lugar del contexto específico de cada transacción
- **Riesgo:** Si hay múltiples transacciones con diferentes compañías, el comportamiento podría cambiar

---

## ⚙️ Resumen de impactos funcionales

| Cambio | Impacto | Severidad |
|--------|---------|-----------|
| Filtro excluye estado "sent" en confirmación de órdenes | Órdenes "sent" ya no se confirman automáticamente | Alto |
| Filtro excluye estado "sent" en procesamiento pendiente | Órdenes "sent" no se procesan en pagos pendientes | Medio |
| Eliminación de flag `skip_sale_auto_invoice_send` | Pérdida de control para deshabilitar envío de emails | Medio |
| Cambio `tx.env` → `self.env` en envío de facturas | Cambio en contexto de ejecución | Medio |

---

## 📌 Conclusión

La versión 18.2-marin introduce cambios significativos en el procesamiento de transacciones de pago:

1. **Cambio de comportamiento crítico**: Las órdenes en estado "sent" ya no se confirman automáticamente al recibir pago
2. **Pérdida de flexibilidad**: Ya no se puede deshabilitar el envío automático de emails mediante flag de contexto
3. **Cambio en contexto de envío**: Las facturas ahora se envían con el contexto original en lugar del contexto por transacción

El cambio más crítico es la exclusión del estado "sent" en la confirmación automática de órdenes, lo cual puede impactar significativamente el flujo de ventas si se esperaba que las cotizaciones enviadas se confirmaran automáticamente al recibir el pago.
