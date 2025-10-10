# Cambios Lógicos: sale_order.py

## 🔍 Descripción general
Este documento analiza los cambios lógicos funcionales entre las versiones 18.2 (original, 2070 líneas) y 18.2-marin (modificada, 1880 líneas). Se han identificado 29 cambios lógicos significativos en la gestión del estado "sent", el sistema de aprobaciones, la validación de órdenes, el cálculo de estados de facturación, y la lógica de confirmación de órdenes.

---

## 🧠 Cambios lógicos detectados

### 1. **Eliminación del estado "sent" del modelo**

**Versión 18.2 (original):**
```python
SALE_ORDER_STATE = [
    ("draft", "Quotation"),
    ("sent", "Quotation Sent"),
    ("sale", "Sales Order"),
    ("cancel", "Cancelled"),
]
```

**Versión 18.2-marin (modificada):**
```python
SALE_ORDER_STATE = [
    ("draft", "Quotation"),
    ("sale", "Sales Order"),
    ("cancel", "Cancelled"),
]
```

**Impacto:**
- El estado "sent" (Cotización Enviada) ha sido eliminado completamente del flujo de estados
- Esto afecta todo el ciclo de vida de las órdenes de venta
- Las cotizaciones ya no pueden marcarse como "enviadas" como estado separado
- Cambio fundamental en el workflow de ventas

---

### 2. **Redefinición completa de estados de facturación (INVOICE_STATE)**

**Versión 18.2 (original):**
```python
INVOICE_STATUS = [
    ("upselling", "Upselling Opportunity"),
    ("invoiced", "Fully Invoiced"),
    ("to invoice", "To Invoice"),
    ("no", "Nothing to Invoice"),
]
```

**Versión 18.2-marin (modificada):**
```python
INVOICE_STATE = [
    ("no", "Nothing to invoice"),
    ("to do", "To invoice"),
    ("partially", "Partially invoiced"),
    ("upselling", "Upselling Opportunity"),
    ("done", "Fully invoiced"),
    ("over done", "Upselling"),
]
```

**Impacto:**
- Cambio de nombre de constante: `INVOICE_STATUS` → `INVOICE_STATE`
- Nuevos estados: "partially" (parcialmente facturado) y "over done" (sobre facturado)
- Cambio de nomenclatura: "to invoice" → "to do", "invoiced" → "done"
- Mayor granularidad en el seguimiento del estado de facturación
- Severidad: **Alta** - Afecta toda la lógica de facturación

---

### 4. **Cambios en el método write() - Suscripción de partners**

**Versión 18.2 (original):**
```python
def write(self, vals):
    if "pricelist_id" in vals and any((so.state == "sale" for so in self)):
        raise UserError(_("You cannot change the pricelist of a confirmed order !"))
    res = super().write(vals)
    if vals.get("partner_id"):
        self.filtered(lambda so: so.state in ("sent", "sale")).message_subscribe(
            partner_ids=[vals["partner_id"]]
        )
    return res
```

**Versión 18.2-marin (modificada):**
```python
def write(self, vals):
    if "pricelist_id" in vals and any((order.state == "sale" for order in self)):
        raise UserError(_("You cannot change the pricelist of a confirmed order !"))
    res = super().write(vals)
    if vals.get("partner_id"):
        self.filtered(lambda order: order.state == "sale").message_subscribe(
            partner_ids=[vals["partner_id"]]
        )
    return res
```

**Impacto:**
- La suscripción automática al cambiar partner ahora solo ocurre en estado "sale"
- Antes ocurría en estados "sent" y "sale"
- Los partners no se suscriben automáticamente cuando la orden está en draft (eliminación de "sent")

---

### 6. **Cambio en cálculo de monto facturado (_compute_amount_invoiced)**

**Versión 18.2 (original):**
```python
@api.depends("line_ids.amount_invoiced_taxinc_taxinc")
def _compute_amount_invoiced(self):
    for order in self:
        order.amount_invoiced_taxinc = sum(
            order.line_ids.mapped("amount_invoiced_taxinc_taxinc")
        )
```

**Versión 18.2-marin (modificada):**
```python
@api.depends("line_ids.amount_invoiced_taxinc", "line_ids.amount_to_invoice_taxinc")
def _compute_amount_invoiced(self):
    for order in self:
        order.amount_to_invoice_taxinc = sum(
            order.line_ids.mapped("amount_to_invoice_taxinc")
        )
        order.amount_invoiced_taxinc = sum(
            order.line_ids.mapped("amount_invoiced_taxinc")
        )
```

**Impacto:**
- Ahora calcula DOS campos en lugar de uno: `amount_to_invoice_taxinc` y `amount_invoiced_taxinc`
- Cambio en dependencias: depende de campos diferentes en las líneas
- Cambio de nombres de campos en sale.order.line
- Severidad: **Alta** - Afecta cálculos de facturación

---

### 7. **Nueva lógica de cálculo de approval_state**

**Versión 18.2 (original):**
```python
# No existe este método
```

**Versión 18.2-marin (modificada):**
```python
@api.depends("approval_request_id")
def _compute_approval_state(self):
    for order in self:
        if order.approval_request_id:
            order.approval_state = order.approval_request_id.state
        else:
            order.approval_state = "none"
```

**Impacto:**
- **NUEVO**: Sistema de aprobaciones integrado en sale.order
- Calcula estado de aprobación basado en approval_request_id
- Estados posibles: estado de la solicitud de aprobación o "none"
- Severidad: **Alta** - Funcionalidad completamente nueva

---

### 14. **CAMBIO CRÍTICO: Refactorización completa de _compute_invoice_state**

**Versión 18.2 (original):**
```python
@api.depends("line_ids.invoice_state", "state")
def _compute_invoice_state(self):
    """
    Compute the invoice status of a SO. Possible statuses:
    - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
      invoice. This is also the default value if the conditions of no other status is met.
    - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
    - invoiced: if all SO lines are invoiced, the SO is invoiced.
    - upselling: if all SO lines are invoiced or upselling, the status is upselling.
    """
    confirmed_orders = self.filtered(lambda so: so.state == "sale")
    (self - confirmed_orders).invoice_state = "no"
    if not confirmed_orders:
        return
    lines_domain = [("is_downpayment", "=", False), ("display_type", "=", False)]
    line_invoice_status_all = [
        (order.id, invoice_status)
        for order, invoice_state in self.env["sale.order.line"]._read_group(
            lines_domain + [("order_id", "in", confirmed_orders.ids)],
            ["order_id", "invoice_state"],
        )
    ]
    for order in confirmed_orders:
        line_invoice_status = [
            d[1] for d in line_invoice_state_all if d[0] == order.id
        ]
        if order.state != "sale":
            order.invoice_state = "no"
        elif any(
            (
                invoice_state == "to invoice"
                for invoice_status in line_invoice_status
            )
        ):
            # [lógica adicional para estados especiales]
            order.invoice_state = "to invoice"
        elif line_invoice_status and all(
            (invoice_state == "invoiced" for invoice_status in line_invoice_status)
        ):
            order.invoice_state = "invoiced"
        elif line_invoice_status and all(
            (
                invoice_state in ("invoiced", "upselling")
                for invoice_state in line_invoice_status
            )
        ):
            order.invoice_state = "upselling"
        else:
            order.invoice_state = "no"
```

**Versión 18.2-marin (modificada):**
```python
@api.depends("invoice_ids", "line_ids.invoice_state", "state")
def _compute_invoice_state(self):
    """Compute the invoice status of a SO. Possible statuses:
    - no: If the SO is not in status 'sale' or 'done', we consider that there is nothing to
      invoice. This is also the default value if all lines are in 'no' state.
    - to do: If any SO line is 'to invoice', the whole SO is 'to invoice'.
    - partially: If some SO lines are invoiced and others are pending, the SO is 'partially invoiced'.
    - done: If all SO lines are in 'no' or 'done' state, and at least one is 'done', the SO is 'fully invoiced'.
    - over done: If all SO lines are invoiced and at least one is 'over invoiced', the status is 'over invoiced'.
    - upselling: If all SO lines are invoiced or upselling, the status is 'upselling'.
    """
    confirmed_orders = self.filtered(lambda o: o.state == "sale")
    (self - confirmed_orders).invoice_state = "no"
    if not confirmed_orders:
        return
    lines_domain = [("is_downpayment", "=", False), ("display_type", "=", False)]
    line_invoice_state_all = {}
    for order, invoice_state in self.env["sale.order.line"]._read_group(
        lines_domain + [("order_id", "in", confirmed_orders.ids)],
        ["order_id", "invoice_state"],
    ):
        if not order.id in line_invoice_state_all:
            line_invoice_state_all[order.id] = set()
        line_invoice_state_all[order.id].add(invoice_state)
    for order in confirmed_orders:
        states = line_invoice_state_all[order._origin.id]
        if any((state == "to do" for state in states)):
            # [lógica similar pero con "to do"]
            order.invoice_state = "to do"
        elif not order.invoice_ids or all((state == "to do" for state in states)):
            order.invoice_state = "to do"
        elif any((state == "over done" for state in states)):
            order.invoice_state = "over done"
        elif all((state in ("done", "upselling") for state in states)):
            if any((state == "upselling" for state in states)):
                order.invoice_state = "upselling"
            else:
                order.invoice_state = "done"
        elif any((state == "partially" for state in states)) or (
            not any((state == "partially" for state in states))
            and any((state in ("to do", "done") for state in states))
        ):
            order.invoice_state = "partially"
        else:
            order.invoice_state = "no"
```

**Impacto:**
- **CAMBIO CRÍTICO**: Lógica completamente reescrita
- Nueva dependencia: ahora depende también de "invoice_ids"
- Nuevos estados: "partially", "over done", "to do" (en lugar de "to invoice")
- Usa diccionario con sets en lugar de lista de tuplas (más eficiente)
- Lógica más compleja para manejar facturación parcial y sobre-facturación
- Severidad: **Muy Alta** - Núcleo de la lógica de facturación

---

### 16. **Cambio en compute del equipo de ventas - Inclusión de partner_id en dependencias**

**Versión 18.2 (original):**
```python
@api.depends("user_id")
def _compute_team_id(self):
    cached_teams = {}
    for order in self:
        default_team_id = order._default_team_id()
        user_id = order.user_id.id
        company_id = order.company_id.id
        key = (default_team_id, user_id, company_id)
        if key not in cached_teams:
            cached_teams[key] = (
                self.env["crm.team"]
                .with_context(default_team_id=default_team_id)
                ._get_default_team_id(
                    user_id=user_id,
                    domain=self.env["crm.team"]._check_company_domain(company_id),
                )
            )
        order.team_id = cached_teams[key]
```

**Versión 18.2-marin (modificada):**
```python
@api.depends("partner_id", "user_id")
def _compute_team_id(self):
    cached_teams = {}
    for order in self:
        default_team_id = (
            self.env.context.get("default_team_id", False) or order.team_id.id
        )
        user_id = order.user_id.id
        company_id = order.company_id.id
        key = (default_team_id, user_id, company_id)
        if key not in cached_teams:
            cached_teams[key] = (
                self.env["crm.team"]
                .with_context(default_team_id=default_team_id)
                ._get_default_team_id(
                    user_id=user_id,
                    domain=self.env["crm.team"]._check_company_domain(company_id),
                )
            )
        order.team_id = cached_teams[key]
```

**Impacto:**
- Nueva dependencia: ahora también depende de "partner_id"
- Cambio en obtención de default_team_id: ya no usa método `_default_team_id()`, usa contexto directamente
- El equipo ahora se recalcula cuando cambia el partner

---

### 21. **CAMBIO CRÍTICO: Refactorización completa de action_cancel()**

**Versión 18.2 (original):**
```python
def action_cancel(self):
    """Cancel sales order and related draft invoices."""
    if any((order.locked for order in self)):
        raise UserError(
            _("You cannot cancel a locked order. Please unlock it first.")
        )
    return self._hook_action_cancel()
```

**Versión 18.2-marin (modificada):**
```python
def action_cancel(self):
    self._can_cancel_except_locked()
    self._can_cancel_except_invoiced()
    inv = self.invoice_ids.filtered(lambda inv: inv.state == "draft")
    inv.button_cancel()
    self.write({"state": "cancel"})
    return True
```

**Impacto:**
- **CAMBIO CRÍTICO**: Lógica completamente reescrita
- Ahora valida con métodos específicos: `_can_cancel_except_locked()` y `_can_cancel_except_invoiced()`
- Cancela facturas en draft directamente en lugar de usar hook
- Escribe el estado directamente en lugar de delegar a `_hook_action_cancel()`
- Ya no usa el patrón de hook, implementa toda la lógica directamente
- Severidad: **Muy Alta** - Cambio en flujo de cancelación

---

### 22. **CAMBIO CRÍTICO: Refactorización completa de action_confirm()**

**Versión 18.2 (original):**
```python
def action_confirm(self):
    """Confirm the given quotation(s) and set their confirmation date.

    If the corresponding setting is enabled, also locks the Sale Order.

    :return: True
    :rtype: bool
    :raise: UserError if trying to confirm cancelled SO's
    """
    for order in self:
        error_msg = order._confirmation_error_message()
        if error_msg:
            raise UserError(error_msg)
    self.line_ids._validate_analytic_distribution()
    for order in self:
        if order.partner_id in order.message_partner_ids:
            continue
        order.message_subscribe([order.partner_id.id])
    self.write(self._prepare_confirmation_values())
    context = self._context.copy()
    context.pop("default_name", None)
    context.pop("default_user_id", None)
    self.with_context(context)._hook_action_confirm()
    self.filtered(lambda so: so._should_be_locked()).action_lock()
    if self.env.context.get("send_email"):
        self._mail_confirmation()
    return True
```

**Versión 18.2-marin (modificada):**
```python
def action_confirm(self):
    """Confirm the given quotation(s) and set their confirmation date.

    If the corresponding setting is enabled, also locks the Sale Order.

    :return: True
    :rtype: bool
    :raise: UserError if trying to confirm cancelled SO's"""
    self._can_confirm_proper_state()
    self._can_confirm_has_lines()
    self._can_confirm_lines_have_product()
    for order in self:
        if order._approval_allowed():
            order.write(order._prepare_action_confirm_write_vals())
            order.line_ids._validate_analytic_distribution()
            context = order._context.copy()
            context.pop("default_name", None)
            context.pop("default_user_id", None)
            order.with_context(context)._hook_action_confirm()
            user = self[:1].create_uid
            if user and user.sudo().has_group("sale.group_order_auto_lock"):
                order.action_lock()
            if self.env.context.get("send_email"):
                order._mail_confirmation()
        elif not order.approval_request_id:
            order.approval_request_id = self.env["approval.request"].create(
                order._prepare_approval_request_vals()
            )
            order.approval_request_id.action_confirm()
        else:
            raise UserError(
                _(
                    "This order requires approval before it can be confirmed. Please wait for the approval to be granted."
                )
            )
        if order.partner_id not in order.message_partner_ids:
            order.message_subscribe([order.partner_id.id])
    return True
```

**Impacto:**
- **CAMBIO CRÍTICO**: Integración completa de sistema de aprobaciones
- Nueva validación en tres pasos: `_can_confirm_proper_state()`, `_can_confirm_has_lines()`, `_can_confirm_lines_have_product()`
- Lógica condicional: si no está aprobado, crea solicitud de aprobación automáticamente
- Cambia de validación centralizada a validaciones por orden
- Cambia método de preparación: `_prepare_confirmation_values()` → `_prepare_action_confirm_write_vals()`
- Cambia lógica de bloqueo: usa grupo diferente `group_order_auto_lock` en lugar de `group_auto_done_setting`
- La suscripción del partner se mueve al final del bucle
- Severidad: **Muy Alta** - Núcleo de la lógica de confirmación

---

### 25. **Eliminación de validación de líneas analíticas en action_send_quotation()**

**Versión 18.2 (original):**
```python
def action_send_quotation(self):
    """Opens a wizard to compose an email, with relevant mail template loaded by default"""
    self.filtered(
        lambda so: so.state in ("draft", "sent")
    ).line_ids._validate_analytic_distribution()
    lang = self.env.context.get("lang")
```

**Versión 18.2-marin (modificada):**
```python
def action_send_quotation(self):
    """Opens a wizard to compose an email, with relevant mail template loaded by default"""
    lang = self.env.context.get("lang")
```

**Impacto:**
- Se elimina la validación de distribución analítica antes de enviar cotización
- Ya no filtra por estado "sent" (porque no existe)
- Menos validaciones al enviar email
- Severidad: **Media** - Afecta validaciones

---

### 26. **Cambio en action_view_approval_request()**

**Versión 18.2 (original):**
```python
@api.readonly
def action_view_approval_request(self):
    self.ensure_one()
    return {
        "name": _("Order"),
        "type": "ir.actions.act_window",
        "res_model": "sale.order",
        "res_id": self.id,
        "views": [(False, "form")],
    }
```

**Versión 18.2-marin (modificada):**
```python
def action_view_approval_request(self):
    """Open the approval request associated with this purchase order."""
    self.ensure_one()
    return {
        "name": _("Approval Request"),
        "type": "ir.actions.act_window",
        "res_model": "approval.request",
        "res_id": self.approval_request_id.id,
        "view_mode": "form",
        "views": [[False, "form"]],
        "target": "current",
    }
```

**Impacto:**
- **CAMBIO CRÍTICO**: Ahora abre la solicitud de aprobación en lugar de la orden
- Cambio de modelo: `sale.order` → `approval.request`
- Abre el registro de aprobación asociado
- Severidad: **Alta** - Funcionalidad completamente diferente

---

### 29. **Nuevo método: _prepare_approval_request_vals()**

**Versión 18.2 (original):**
```python
# Método no existe
```

**Versión 18.2-marin (modificada):**
```python
def _prepare_approval_request_vals(self):
    self.ensure_one()
    category = self.get_approval_category()
    res = {
        "company_id": self.company_id.id,
        "category_id": category.id,
        "partner_id": self.partner_id.id,
        "date": fields.Datetime.now(),
        "name": self.name,
        "amount": self.amount_total,
        "reason": self.notes,
    }
    return res
```

**Impacto:**
- **NUEVO**: Método para preparar valores de solicitud de aprobación
- Parte del sistema de aprobaciones integrado
- Severidad: **Alta** - Funcionalidad nueva

---

### 33. **Nuevo método: get_approval_category()**

**Versión 18.2 (original):**
```python
# No existe
```

**Versión 18.2-marin (modificada):**
```python
def get_approval_category(self):
    return self.env.ref("sale.approval_category_sale")
```

**Impacto:**
- **NUEVO**: Retorna categoría de aprobación para ventas
- Parte del sistema de aprobaciones
- Severidad: **Alta** - Funcionalidad nueva

---

### 36. **Cambio en _track_finalize() - Lógica simplificada**

**Versión 18.2 (original):**
```python
def _track_finalize(self):
    """Override of `mail` to prevent logging changes when the SO is in a draft state."""
    if (
        len(self) == 1
        and self.env.cache.contains(self, self._fields["state"])
        and self._discard_tracking()
    ):
        self.env.cr.precommit.data.pop(f"mail.tracking.{self._name}", {})
        self.env.flush_all()
        return
    return super()._track_finalize()
```

**Versión 18.2-marin (modificada):**
```python
def _track_finalize(self):
    """Override of `mail` to prevent logging changes when the SO is in a draft state."""
    if (
        len(self) == 1
        and self.env.cache.contains(self, self._fields["state"])
        and (self.state == "draft")
    ):
        self.env.cr.precommit.data.pop(f"mail.tracking.{self._name}", {})
        self.env.flush_all()
        return
    return super()._track_finalize()
```

**Impacto:**
- Simplificación: ya no usa método `_discard_tracking()`
- Verifica directamente si `state == "draft"`
- Lógica más directa

---

### 37. **CAMBIO CRÍTICO en _track_subtype() - Eliminación de estado "sent"**

**Versión 18.2 (original):**
```python
def _track_subtype(self, init_values):
    self.ensure_one()
    if "state" in init_values and self.state == "sale":
        return self.env.ref("sale.mt_order_confirmed")
    elif "state" in init_values and self.state == "sent":
        return self.env.ref("sale.mt_order_sent")
    return super()._track_subtype(init_values)
```

**Versión 18.2-marin (modificada):**
```python
def _track_subtype(self, init_values):
    self.ensure_one()
    if "state" in init_values and self.state == "sale":
        return self.env.ref("sale.mt_order_confirmed")
    elif "sent" in init_values and self.sent:
        return self.env.ref("sale.mt_order_sent")
    return super()._track_subtype(init_values)
```

**Impacto:**
- **CAMBIO CRÍTICO**: Ya no se dispara al cambiar estado a "sent"
- Ahora se dispara por cambio en campo booleano "sent"
- El estado "sent" se reemplaza por un campo boolean
- Severidad: **Alta** - Cambio en notificaciones automáticas

---

### 38. **Cambio en message_post() - Uso de campo "sent" booleano**

**Versión 18.2 (original):**
```python
def message_post(self, **kwargs):
    if self.env.context.get("mark_so_as_sent"):
        self.filtered(lambda o: o.state == "draft").with_context(
            tracking_disable=True
        ).write({"state": "sent"})
        kwargs["notify_author_mention"] = kwargs.get("notify_author_mention", True)
    return super().message_post(**kwargs)
```

**Versión 18.2-marin (modificada):**
```python
def message_post(self, **kwargs):
    if self.env.context.get("mark_so_as_sent"):
        self.filtered(lambda o: o.state == "draft").with_context(
            tracking_disable=True
        ).write({"sent": True})
        kwargs["notify_author_mention"] = kwargs.get("notify_author_mention", True)
    return super().message_post(**kwargs)
```

**Impacto:**
- **CAMBIO CRÍTICO**: Ahora escribe campo boolean `sent=True` en lugar de cambiar estado
- El "enviado" ahora es un flag, no un estado
- Severidad: **Muy Alta** - Cambio fundamental en modelo de datos

---

### 39. **Eliminación de métodos relacionados con attachments y órdenes EDI**

**Versión 18.2 (original):**
```python
@api.model
def _create_order_from_attachment(self, attachment_ids):
    """Create the sale orders from given attachment_ids and fill data by extracting detail
    from attachments and return generated orders.

    :param list attachment_ids: List of attachments process.
    :return: Recordset of order.
    """
    # [implementación completa]

def create_document_from_attachment(self, attachment_ids):
    """Create the sale orders from given attachment_ids and redirect newly create order view.
    # [implementación completa]

def _extend_with_attachments(self, attachment):
    """Main entry point to extend/enhance order with attachment.
    # [implementación completa]

def _get_order_edi_decoder(self, file_data):
    """To be extended with decoding capabilities of order data from file data.
    # [implementación completa]
```

**Versión 18.2-marin (modificada):**
```python
# Todos estos métodos han sido eliminados
```

**Impacto:**
- **ELIMINADOS**: Funcionalidad completa de importación EDI/archivos
- Ya no se pueden crear órdenes desde attachments
- Severidad: **Muy Alta** - Funcionalidad completa eliminada

---

### 40. **Eliminación de método _fetch_duplicate_orders()**

**Versión 18.2 (original):**
```python
def _fetch_duplicate_orders(self):
    """Fectch duplicated orders.

    :return: Dictionary mapping order to it's related duplicated orders.
    :rtype: dict
    """
    orders = self.filtered(lambda order: order.id and order.client_order_ref)
    if not orders:
        return {}
    used_fields = (
        "company_id",
        "partner_id",
        "client_order_ref",
        "origin",
        "date_order",
        "state",
    )
    self.env["sale.order"].flush_model(used_fields)
    result = self.env.execute_query(
        SQL(
            "\n            SELECT\n                sale_order.id AS order_id,\n                array_agg(duplicate_order.id) AS duplicate_ids\n              FROM sale_order\n              JOIN sale_order AS duplicate_order\n                ON sale_order.company_id = duplicate_order.company_id\n                 AND sale_order.id != duplicate_order.id\n                 AND duplicate_order.state != 'cancel'\n                 AND sale_order.partner_id = duplicate_order.partner_id\n                 AND sale_order.date_order = duplicate_order.date_order\n                 AND sale_order.client_order_ref = duplicate_order.client_order_ref\n                 AND (\n                    sale_order.origin = duplicate_order.origin\n                    OR (sale_order.origin IS NULL AND duplicate_order.origin IS NULL)\n                )\n             WHERE sale_order.id IN %(orders)s\n             GROUP BY sale_order.id\n            ",
            orders=tuple(orders.ids),
        )
    )
    return {order_id: set(duplicate_ids) for order_id, duplicate_ids in result}

@api.depends("client_order_ref", "date_order", "origin", "partner_id")
def _compute_duplicated_order_ids(self):
    order_to_duplicate_orders = self._fetch_duplicate_orders()
    for order in self:
        order.duplicated_order_ids = [
            Command.set(order_to_duplicate_orders.get(order.id, []))
        ]
```

**Versión 18.2-marin (modificada):**
```python
# Métodos completamente eliminados
```

**Impacto:**
- **ELIMINADOS**: Detección de órdenes duplicadas
- Ya no se detectan ni alertan órdenes duplicadas
- Severidad: **Alta** - Funcionalidad de validación eliminada

---

### 44. **Cambio en _hook_action_cancel() - Simplificación**

**Versión 18.2 (original):**
```python
def _hook_action_cancel(self):
    inv = self.invoice_ids.filtered(lambda inv: inv.state == "draft")
    inv.button_cancel()
    return self.write({"state": "cancel"})
```

**Versión 18.2-marin (modificada):**
```python
def _hook_action_cancel(self):
    pass
```

**Impacto:**
- Hook ahora vacío (la lógica se movió a `action_cancel()`)
- Permite sobrescribir sin lógica base

---

### 45. **Nuevos métodos de validación (_can_*)**

**Versión 18.2 (original):**
```python
def _confirmation_error_message(self):
    """Return whether order can be confirmed or not if not then returm error message."""
    self.ensure_one()
    if self.state not in {"draft", "sent"}:
        return _("Some orders are not in a state requiring confirmation.")
    if any(
        (
            not line.display_type
            and (not line.is_downpayment)
            and (not line.product_id)
            for line in self.line_ids
        )
    ):
        return _("A line on these orders missing a product, you cannot confirm it.")
    return False
```

**Versión 18.2-marin (modificada):**
```python
def _approval_allowed(self):
    """Returns whether the order qualifies to be approved by the current user"""
    self.ensure_one()
    return not self.company_id.po_approval or self.approval_state == "approved"

def _can_cancel_except_invoiced(self):
    """Returns whether the order qualifies to be canceled by the current user"""
    orders_with_invoices = self.filtered(
        lambda o: any((i.state == "posted" for i in o.invoice_ids))
    )
    if orders_with_invoices:
        raise UserError(
            _(
                "Unable to cancel sale order(s): %s. You must first cancel their related invoices.",
                format_list(self.env, orders_with_invoices.mapped("display_name")),
            )
        )

def _can_cancel_except_locked(self):
    if any((order.locked for order in self)):
        raise UserError(
            _("You cannot cancel a locked order. Please unlock it first.")
        )

def _can_confirm_has_lines(self):
    orders_without_lines = self.filtered(lambda order: not order.line_ids)
    if orders_without_lines:
        raise UserError(_("No lines on this order. It can not be confirmed."))

def _can_confirm_lines_have_product(self):
    orders_without_line_product = self.filtered(
        lambda order: any(
            (
                not line.display_type
                and (not line.is_downpayment)
                and (not line.product_id)
                for line in order.line_ids
            )
        )
    )
    if orders_without_line_product:
        raise UserError(
            _(
                "A line on these orders is missing a product. It can not be confirmed."
            )
        )

def _can_confirm_proper_state(self):
    orders_wrong_state = self.filtered(lambda order: order.state != "draft")
    if orders_wrong_state:
        raise UserError(_("Some orders are not in a state requiring confirmation."))

def _can_draft_proper_state(self):
    if any((order.state != "cancel" for order in self)):
        raise UserError(
            _("You cannot draft an order in a state different from 'Cancelled'.")
        )
```

**Impacto:**
- **NUEVOS**: 7 métodos de validación específicos
- Reemplazan `_confirmation_error_message()`
- Validaciones más granulares y reutilizables
- Nuevo: `_approval_allowed()` para sistema de aprobaciones
- Nuevo: validación de facturas posted en cancelación
- Cambio en validación de estado: ya no acepta "sent", solo "draft"
- Severidad: **Alta** - Nueva arquitectura de validaciones

---

### 46. **Cambio en _add_base_lines_for_early_payment_discount**

**Versión 18.2 (original):**
```python
tax_ids=line.tax_ids.flatten_taxes_hierarchy().filtered(
    lambda tax: tax.amount_type != "fixed"
),
```

**Versión 18.2-marin (modificada):**
```python
tax_ids=line.tax_ids,
```

**Impacto:**
- Ya no filtra ni aplana jerarquía de impuestos
- Usa todos los impuestos de la línea directamente
- Puede afectar cálculo de descuentos por pago anticipado

---

### 49. **Eliminación de método _default_team_id()**

**Versión 18.2 (original):**
```python
def _default_team_id(self):
    return self.env.context.get("default_team_id", False) or self.team_id.id
```

**Versión 18.2-marin (modificada):**
```python
# Método eliminado - lógica integrada en _compute_team_id()
```

**Impacto:**
- Lógica movida directamente a `_compute_team_id()`
- Menos métodos auxiliares

---

### 50. **Eliminación de método _discard_tracking()**

**Versión 18.2 (original):**
```python
def _discard_tracking(self):
    self.ensure_one()
    return (
        self.state == "draft"
        and request
        and request.env.context.get("catalog_skip_tracking")
    )
```

**Versión 18.2-marin (modificada):**
```python
# Método eliminado - lógica simplificada en _track_finalize()
```

**Impacto:**
- Método eliminado
- Lógica simplificada directamente en `_track_finalize()`

---

### 51. **Eliminación de método _should_be_locked()**

**Versión 18.2 (original):**
```python
def _should_be_locked(self):
    self.ensure_one()
    user = self[:1].create_uid
    return user and user.sudo().has_group("sale.group_auto_done_setting")
```

**Versión 18.2-marin (modificada):**
```python
# Método eliminado - lógica integrada en action_confirm()
```

**Impacto:**
- Lógica movida a `action_confirm()`
- Cambio de grupo: `group_auto_done_setting` → `group_order_auto_lock`

---

### 52. **Eliminación de métodos relacionados con catálogo de productos**

**Versión 18.2 (original):**
```python
def _get_action_add_from_catalog_extra_context(self):
    return {
        **super()._get_action_add_from_catalog_extra_context(),
        "product_catalog_currency_id": self.currency_id.id,
        "product_catalog_digits": self.line_ids._fields["price_unit"].get_digits(
            self.env
        ),
    }

def _get_product_catalog_domain(self):
    return expression.AND(
        [super()._get_product_catalog_domain(), [("sale_ok", "=", True)]]
    )

def _get_product_catalog_order_data(self, products, **kwargs):
    # [implementación completa]

def _get_product_catalog_record_lines(self, product_ids, **kwargs):
    # [implementación completa]

def _default_line_ids_values(self, child_field=False):
    default_data = super()._default_line_ids_values(child_field)
    new_default_data = self.env["sale.order.line"]._get_product_catalog_lines_data()
    return {**default_data, **new_default_data}

def _update_line_ids_info(self, product_id, quantity, **kwargs):
    """Update sale order line information for a given product or create a
    new one if none exists yet.
    # [implementación completa - ~70 líneas]
```

**Versión 18.2-marin (modificada):**
```python
# Todos estos métodos han sido completamente eliminados
```

**Impacto:**
- **ELIMINADOS**: Toda la funcionalidad del catálogo de productos integrado
- Ya no hay integración con product.catalog.mixin
- Ya no se pueden agregar productos desde catálogo
- Severidad: **Muy Alta** - Funcionalidad completa eliminada

---

### 55. **Eliminación de método _validate_order()**

**Versión 18.2 (original):**
```python
def _validate_order(self):
    """
    Confirm the sale order and send a confirmation email.

    :return: None
    """
    self.with_context(send_email=True).action_confirm()
```

**Versión 18.2-marin (modificada):**
```python
# Método completamente eliminado
```

**Impacto:**
- Método auxiliar eliminado
- Funcionalidad puede lograrse directamente con `action_confirm()`

---

### 56. **Eliminación de property _rec_names_search**

**Versión 18.2 (original):**
```python
@property
def _rec_names_search(self):
    if self._context.get("sale_show_partner_name"):
        return ["name", "partner_id.name"]
    return ["name"]
```

**Versión 18.2-marin (modificada):**
```python
# Propiedad completamente eliminada
```

**Impacto:**
- Ya no permite búsqueda por nombre de partner
- Solo búsqueda por nombre de orden
- Severidad: **Media** - Afecta búsquedas

---

### 57. **Eliminación de herencia de product.catalog.mixin**

**Versión 18.2 (original):**
```python
_inherit = [
    "portal.mixin",
    "product.catalog.mixin",
    "mail.thread",
    "mail.activity.mixin",
    "utm.mixin",
]
```

**Versión 18.2-marin (modificada):**
```python
_inherit = ["mail.activity.mixin", "mail.thread", "portal.mixin", "utm.mixin"]
```

**Impacto:**
- **ELIMINADO**: `product.catalog.mixin`
- Ya no hereda funcionalidad de catálogo de productos
- Severidad: **Muy Alta** - Cambio estructural en modelo

---

### 58. **Cambio en onchange de contexto**

**Versión 18.2 (original):**
```python
def onchange(self, values, field_names, fields_spec):
    self_with_context = self
    if not field_names:
        self_with_context = self.with_context(
            sale_onchange_first_call=True, res_partner_search_mode="customer"
        )
    return super(SaleOrder, self_with_context).onchange(
        values, field_names, fields_spec
    )
```

**Versión 18.2-marin (modificada):**
```python
def onchange(self, values, field_names, fields_spec):
    self_with_context = self
    if not field_names:
        self_with_context = self.with_context(sale_onchange_first_call=True)
    return super(SaleOrder, self_with_context).onchange(
        values, field_names, fields_spec
    )
```

**Impacto:**
- Ya no establece `res_partner_search_mode="customer"` en contexto
- Puede afectar búsqueda de partners en formularios

---

---

## ⚙️ Resumen de impactos funcionales

| # | Cambio | Impacto | Severidad |
|---|--------|---------|-----------|
| 1 | Eliminación del estado "sent" del workflow | Simplifica workflow, elimina paso intermedio entre draft y sale | **Muy Alta** |
| 2 | Nuevo conjunto de estados de facturación (INVOICE_STATE) | Mayor granularidad: "partially", "over done", "to do" vs "to invoice" | **Muy Alta** |
| 7 | Sistema de aprobaciones integrado (approval_state) | Nueva funcionalidad completa de aprobaciones | **Muy Alta** |
| 8 | Cambio de campo: expected_date → date_planned | Renombrado de campo clave de fechas | **Alta** |
| 14 | Refactorización completa de _compute_invoice_state | Lógica mucho más compleja con nuevos estados | **Muy Alta** |
| 21 | Refactorización de action_cancel() | Nueva arquitectura con métodos de validación | **Muy Alta** |
| 22 | Refactorización de action_confirm() con aprobaciones | Integración completa de flujo de aprobaciones | **Muy Alta** |
| 24 | Eliminación de action_quotation_sent() | Ya no existe forma de marcar como "sent" | **Alta** |
| 26 | action_view_approval_request() ahora abre solicitud de aprobación | Cambio completo de funcionalidad | **Alta** |
| 38 | Estado "sent" convertido a campo booleano | Cambio fundamental en modelo de datos | **Muy Alta** |
| 39 | Eliminación de importación EDI/attachments | Funcionalidad completa eliminada | **Muy Alta** |
| 40 | Eliminación de detección de duplicados | Validación eliminada | **Alta** |
| 45 | 7 nuevos métodos de validación (_can_*) | Nueva arquitectura de validaciones | **Alta** |
| 52 | Eliminación de catálogo de productos | Funcionalidad completa eliminada | **Muy Alta** |
| 57 | Eliminación de herencia product.catalog.mixin | Cambio estructural en modelo | **Muy Alta** |
| 6 | _compute_amount_invoiced calcula 2 campos | Cálculo de facturación modificado | **Alta** |
| 12 | Campo user_id → sale_user_id en partner | Más específico para ventas | **Media** |
| 3-5, 11, 15, 17, 31, 35, 42-43 | Eliminación de referencias a estado "sent" en múltiples métodos | Consistente con eliminación del estado | **Media** |
| 10, 13, 30, 32, 41, 47, 53-54 | Renombrados de métodos/campos | Mejoras de nomenclatura, sin cambio funcional | **Baja** |

---

## 📌 Conclusión

### Cambios de Alto Impacto (Muy Alta Severidad)

1. **Eliminación del estado "sent"**: El workflow ahora es draft → sale (o cancel), eliminando el paso intermedio de "cotización enviada". Este cambio afecta a todo el ciclo de vida de las órdenes de venta y se ha reemplazado por un campo booleano `sent`.

2. **Nuevos estados de facturación**: Se introduce mayor granularidad con estados "partially", "over done" y "to do", permitiendo un mejor seguimiento del proceso de facturación.

3. **Sistema de aprobaciones completo**: Se integra un flujo de aprobaciones automático en `action_confirm()`, con nuevos campos, métodos y validaciones relacionadas con `approval_request_id`.

4. **Refactorización de lógica de facturación**: El método `_compute_invoice_state()` fue completamente reescrito con lógica más compleja para manejar los nuevos estados.

5. **Refactorización de cancelación y confirmación**: Los métodos `action_cancel()` y `action_confirm()` fueron completamente reescritos con nueva arquitectura de validaciones.

6. **Eliminación de funcionalidades completas**:
   - Catálogo de productos integrado (product.catalog.mixin)
   - Importación EDI/archivos adjuntos
   - Detección de órdenes duplicadas

### Cambios Funcionales Clave

- El campo `expected_date` se renombra a `date_planned`
- El campo `note` se renombra a `notes` (plural)
- El campo `partner.user_id` se reemplaza por `partner.sale_user_id`
- Se eliminan múltiples métodos auxiliares y se simplifica la arquitectura

### Impacto en Integraciones

Cualquier módulo que:
- Dependa del estado "sent"
- Use los métodos del catálogo de productos
- Importe órdenes desde archivos EDI
- Dependa de los nombres de campos antiguos (expected_date, note, etc.)
- Use INVOICE_STATUS en lugar de INVOICE_STATE

**Requerirá actualización significativa** para ser compatible con esta versión.

### Compatibilidad hacia atrás

Este cambio **NO es compatible hacia atrás**. La eliminación del estado "sent", los cambios en estados de facturación, y la eliminación de funcionalidades completas requieren migración de datos y actualización de código personalizado.
