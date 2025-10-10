# Cambios Lógicos: res_partner.py

## 🔍 Descripción general
Se detectaron dos cambios importantes: la adición de un método `unlink` que elimina órdenes de venta en borrador/canceladas, y un cambio en el filtro de estados para determinar si un partner puede editar su nombre. También se agregó un método de cómputo para sincronizar el vendedor.

---

## 🧠 Cambios lógicos detectados

### 1. **Adición de método `unlink` con eliminación en cascada**

**Versión 18.2 (original):**
- No existe método `unlink`

**Versión 18.2-marin (nueva):**
```python
def unlink(self):
    self.env["sale.order"].sudo().search(
        [
            ("state", "in", ["draft", "cancel"]),
            "|",
            "|",
            ("partner_id", "in", self.ids),
            ("partner_invoice_id", "in", self.ids),
            ("partner_shipping_id", "in", self.ids),
        ]
    ).unlink()
    return super().unlink()
```

**Impacto:**
- **Nueva funcionalidad**: Al eliminar un partner, ahora se eliminan automáticamente todas las órdenes de venta en estado "draft" o "cancel" asociadas
- Busca órdenes donde el partner aparece como:
  - Partner principal (`partner_id`)
  - Partner de facturación (`partner_invoice_id`)
  - Partner de envío (`partner_shipping_id`)
- **Impacto funcional**: Limpieza automática de órdenes no confirmadas
- **Riesgo**: Las órdenes en draft podrían contener trabajo en progreso que se perderá
- **Razón probable**: Evitar registros huérfanos y problemas de integridad referencial

---

### 2. **Cambio en filtro de estados en `_has_order`**

**Versión 18.2 (original):**
```python
def _has_order(self, partner_domain):
    self.ensure_one()
    sale_order = (
        self.env["sale.order"]
        .sudo()
        .search(
            expression.AND([partner_domain, [("state", "in", ("sent", "sale"))]]),
            limit=1,
        )
    )
    return bool(sale_order)
```

**Versión 18.2-marin (modificada):**
```python
def _has_order(self, partner_domain):
    self.ensure_one()
    sale_order = (
        self.env["sale.order"]
        .sudo()
        .search(expression.AND([partner_domain, [("state", "=", "sale")]]), limit=1)
    )
    return bool(sale_order)
```

**Impacto:**
- El filtro cambió de `("state", "in", ("sent", "sale"))` a `("state", "=", "sale")`
- **Ahora se permite editar el nombre del partner si solo tiene órdenes en estado "sent"**
- Versión original: Bloqueaba la edición si había órdenes en "sent" o "sale"
- Versión nueva: Solo bloquea la edición si hay órdenes en "sale" (confirmadas)
- **Impacto funcional**: Mayor flexibilidad para editar el nombre del partner cuando solo tiene cotizaciones enviadas pero no confirmadas
- Este cambio es consistente con el tratamiento del estado "sent" en otros archivos

---

### 3. **Adición de método `_compute_sale_user_id`**

**Versión 18.2 (original):**
- No existe método `_compute_sale_user_id`

**Versión 18.2-marin (nueva):**
```python
@api.depends("parent_id")
def _compute_sale_user_id(self):
    """Synchronize sales rep with parent if partner is a person"""
    for partner in self.filtered(
        lambda partner: not partner.sale_user_id
        and partner.company_type == "person"
        and partner.parent_id.sale_user_id
    ):
        partner.sale_user_id = partner.parent_id.sale_user_id
```

**Impacto:**
- **Nueva funcionalidad**: Sincroniza automáticamente el vendedor (sales rep) de personas con su empresa padre
- Solo se aplica cuando:
  - El partner no tiene vendedor asignado
  - El partner es una persona (`company_type == "person"`)
  - El partner padre tiene vendedor asignado
- **Impacto funcional**: Herencia automática del vendedor de la empresa a sus contactos
- **Mejora de UX**: Evita tener que asignar manualmente el vendedor a cada contacto de una empresa

---

## ⚙️ Resumen de impactos funcionales

| Cambio | Impacto | Severidad |
|--------|---------|-----------|
| Adición de método `unlink` con limpieza de órdenes | Eliminación en cascada de órdenes draft/cancel | Alto |
| Cambio de filtro en `_has_order` excluye estado "sent" | Mayor flexibilidad para editar nombre del partner | Medio |
| Adición de `_compute_sale_user_id` | Sincronización automática de vendedor con empresa padre | Medio |

---

## 📌 Conclusión

La versión 18.2-marin introduce tres cambios significativos en el módulo res_partner:

1. **Eliminación en cascada**: Las órdenes draft/cancel ahora se eliminan automáticamente al eliminar un partner
2. **Mayor flexibilidad de edición**: Los partners con solo órdenes "sent" pueden editar su nombre
3. **Herencia de vendedor**: Los contactos heredan automáticamente el vendedor de su empresa padre

El cambio más crítico es la eliminación automática de órdenes draft/cancel, que podría resultar en pérdida de datos si hay cotizaciones en progreso. Los otros cambios mejoran la usabilidad al ser más flexibles con el estado "sent" y automatizar la asignación de vendedor.
