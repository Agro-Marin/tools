# Cambios Lógicos: product_product.py

## 🔍 Descripción general
Se detectó la eliminación de un método de cómputo que calculaba si un producto está presente en una orden de venta específica. Este cambio elimina funcionalidad del catálogo de productos.

---

## 🧠 Cambios lógicos detectados

### 1. **Eliminación de método `_compute_product_is_in_sale_order`**

**Versión 18.2 (original):**
```python
@api.depends_context("order_id")
def _compute_product_is_in_sale_order(self):
    order_id = self.env.context.get("order_id")
    if not order_id:
        self.product_catalog_product_is_in_sale_order = False
        return
    read_group_data = self.env["sale.order.line"]._read_group(
        domain=[("order_id", "=", order_id)],
        groupby=["product_id"],
        aggregates=["__count"],
    )
    data = {product.id: count for product, count in read_group_data}
    for product in self:
        product.product_catalog_product_is_in_sale_order = bool(
            data.get(product.id, 0)
        )
```

**Versión 18.2-marin:**
- Método completamente eliminado

**Impacto:**
- El cómputo del campo `product_catalog_product_is_in_sale_order` fue removido
- **Funcionalidad eliminada**: Ya no se calcula automáticamente si un producto está en una orden de venta específica
- Este campo probablemente era usado en el catálogo de productos para indicar si un producto ya estaba agregado a la orden actual
- **Razón probable**: Esta funcionalidad se movió a otro módulo o se implementó de forma diferente en Odoo 18

---

## ⚙️ Resumen de impactos funcionales

| Cambio | Impacto | Severidad |
|--------|---------|-----------|
| Eliminación de `_compute_product_is_in_sale_order` | Funcionalidad de catálogo de productos removida | Alto |

---

## 📌 Conclusión

La versión 18.2-marin elimina el método `_compute_product_is_in_sale_order`, que calculaba si un producto está presente en una orden de venta específica basándose en el contexto `order_id`. Esta funcionalidad probablemente se movió a otro módulo especializado en catálogo de productos o se implementó de forma diferente en Odoo 18.
