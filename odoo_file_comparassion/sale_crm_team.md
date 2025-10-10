# Cambios Lógicos: crm_team.py

## 🔍 Descripción general
Se detectaron cambios importantes en los filtros de cotizaciones y en el nombre de campo computado. Estos cambios afectan el comportamiento de dashboards y la forma en que se calculan las métricas del equipo de ventas.

---

## 🧠 Cambios lógicos detectados

### 1. **Cambio en filtro de estados de cotizaciones en `_compute_quotations_to_invoice`**

**Versión 18.2 (original):**
```python
def _compute_quotations_to_invoice(self):
    query = self.env["sale.order"]._where_cal(
        [("team_id", "in", self.ids), ("state", "in", ["draft", "sent"])]
    )
```

**Versión 18.2-marin (modificada):**
```python
def _compute_quotations_to_invoice(self):
    query = self.env["sale.order"]._where_calc(
        [("team_id", "in", self.ids), ("state", "=", "draft")]
    )
```

**Impacto:**
- El filtro cambió de `("state", "in", ["draft", "sent"])` a `("state", "=", "draft")`
- **Las cotizaciones en estado "sent" ya no se cuentan en el dashboard**
- Versión original: Contaba cotizaciones en estado "draft" y "sent"
- Versión nueva: Solo cuenta cotizaciones en estado "draft"
- **Impacto funcional:** El dashboard mostrará menos cotizaciones pendientes
- **Razón probable:** En Odoo 18, las cotizaciones "sent" podrían considerarse en otro estado o etapa del flujo

---

### 2. **Cambio en nombre de campo computado en `_compute_sales_invoiced`**

**Versión 18.2 (original):**
```python
def _compute_sales_invoiced(self):
    # ... código SQL ...
    for team in self:
        team.invoiced = data_map.get(team._origin.id, 0.0)
```

**Versión 18.2-marin (modificada):**
```python
def _compute_sales_invoiced(self):
    # ... código SQL ...
    for team in self:
        team.amount_invoiced_taxexc = data_map.get(team._origin.id, 0.0)
```

**Impacto:**
- Campo cambió de `invoiced` a `amount_invoiced_taxexc`
- **Cambio de nombre de campo en el modelo**
- El nombre nuevo es más descriptivo: indica que es un monto sin impuestos ("tax excluded")
- **Impacto funcional:** Probablemente el campo fue renombrado en la definición de campos (no visible en el archivo)
- Las vistas y reportes que usen este campo deben actualizarse al nuevo nombre

---

## ⚙️ Resumen de impactos funcionales

| Cambio | Impacto | Severidad |
|--------|---------|-----------|
| Filtro de cotizaciones excluye estado "sent" | Dashboard muestra menos cotizaciones | Medio |
| Renombrado campo `invoiced` → `amount_invoiced_taxexc` | Actualización API Odoo 18 | Medio |

---

## 📌 Conclusión

La versión 18.2-marin introduce dos cambios significativos en el módulo crm_team:

1. **Cambio de comportamiento**: Las cotizaciones "sent" ya no se cuentan en el dashboard de cotizaciones pendientes
2. **Cambio de API**: Renombrado de campo `invoiced` a `amount_invoiced_taxexc` para compatibilidad con Odoo 18

El cambio más significativo desde el punto de vista funcional es la exclusión de cotizaciones "sent" del conteo de cotizaciones pendientes, lo cual puede afectar las métricas mostradas en el dashboard del equipo de ventas. Este cambio sugiere que en Odoo 18, las cotizaciones enviadas podrían tener un tratamiento diferente en el flujo de ventas.
