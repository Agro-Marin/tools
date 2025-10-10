# Cambios Lógicos: analytic.py

## 🔍 Descripción general
El archivo `analytic.py` fue dividido y refactorizado. La clase `AccountAnalyticLine` con sus campos fue eliminada completamente, y la clase `AccountAnalyticApplicability` fue movida a su propio archivo.

---

## 🧠 Cambios lógicos detectados

### 1. **Eliminación completa de la clase `AccountAnalyticLine`**

**Versión 18.2 (original):**
```python
class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"
    # Contenía definiciones de campos
```

**Versión 18.2-marin:**
- Clase completamente eliminada

**Impacto:**
- La extensión de `account.analytic.line` ha sido removida del módulo sale
- Todos los campos que contenía esta clase fueron eliminados
- **Impacto funcional**: Los campos específicos de ventas que se agregaban al modelo de líneas analíticas ya no están disponibles
- Esta funcionalidad probablemente fue movida a otro modelo o el flujo de integración con analítica cambió en Odoo 18

---

### 2. **Separación de archivo: `analytic.py` → `account_analytic_applicability.py`**

**Versión 18.2:**
- Ambas clases estaban en `analytic.py`

**Versión 18.2-marin:**
- Solo `AccountAnalyticApplicability` permanece, ahora en su propio archivo `account_analytic_applicability.py`
- La clase sigue siendo una herencia vacía (solo contiene campos, sin métodos)

**Impacto:**
- Reorganización de código siguiendo el principio de un modelo por archivo
- **Sin impacto funcional en `AccountAnalyticApplicability`**: Solo reorganización estructural

---

## ⚙️ Resumen de impactos funcionales

| Cambio | Impacto | Severidad |
|--------|---------|-----------|
| Eliminación de clase `AccountAnalyticLine` con campos | Campos de ventas en líneas analíticas eliminados | Alto |
| Separación de archivo | Reorganización estructural | Ninguno |

---

## 📌 Conclusión

La versión 18.2-marin elimina por completo la extensión del modelo `account.analytic.line` que contenía campos relacionados con ventas. Este es un cambio significativo que sugiere que la integración entre el módulo de ventas y las líneas analíticas cambió en Odoo 18, posiblemente moviendo esta funcionalidad a otro modelo o implementándola de forma diferente en el core.

La clase `AccountAnalyticApplicability` fue simplemente reorganizada en su propio archivo sin cambios funcionales.
