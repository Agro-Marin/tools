# Stock

## Archivo: models/stock_move.py

### 🔍 Descripción general

El archivo `stock_move.py` contiene la lógica principal del modelo `stock.move` que gestiona los movimientos de inventario en Odoo. Las modificaciones detectadas entre la versión base (18.2) y la versión customizada (18.2-marin) son **3 cambios puntuales** que ajustan el comportamiento de:

1. La cancelación de movimientos de destino (línea ~1865)
2. El filtro de confirmación de movimientos al marcar como "hecho" (línea ~2014)
3. La eliminación de una validación de contexto en el recálculo de estado (línea ~2734)

Estos cambios parecen orientados a **corregir bugs de referencia incorrecta** y **ampliar la lógica de confirmación automática** en escenarios específicos.

---

### 🧠 Instrucciones de actualización

#### 1. **Corregir referencia en cancelación de movimientos destino**

**Ubicación:** Método `_action_cancel()`, aproximadamente línea 1863-1866

**Cambio detectado:**
```python
# ANTES (18.2):
move.move_dest_ids.filtered(
    lambda m: m.state != "done"
    and move.location_dest_id == m.location_id
)._action_cancel()

# DESPUÉS (18.2-marin):
move.move_dest_ids.filtered(
    lambda m: m.state != "done"
    and m.location_dest_id == m.move_dest_ids.location_id
)._action_cancel()
```

**Descripción del cambio:**
- Se corrige la comparación de ubicaciones en el filtro de movimientos de destino a cancelar
- **Antes:** Comparaba `move.location_dest_id` (ubicación destino del movimiento actual) con `m.location_id` (ubicación origen del movimiento destino)
- **Después:** Compara `m.location_dest_id` (ubicación destino del movimiento destino) con `m.move_dest_ids.location_id` (ubicación origen de los siguientes movimientos en la cadena)

**Razón del cambio:**
Aparentemente la lógica original tenía una referencia incorrecta que no permitía identificar correctamente qué movimientos destino debían cancelarse en cadena cuando se propaga la cancelación.

**Instrucciones de aplicación:**
1. Localizar el método `_action_cancel()` en `stock.move`
2. Buscar la sección donde se filtran `move.move_dest_ids` dentro del bloque `if move.propagate_cancel:`
3. Modificar la condición del lambda dentro de `.filtered()`:
   - Cambiar: `move.location_dest_id == m.location_id`
   - Por: `m.location_dest_id == m.move_dest_ids.location_id`

---

#### 2. **Ampliar filtro de confirmación automática en `_action_done()`**

**Ubicación:** Método `_action_done()`, aproximadamente línea 2013-2016

**Cambio detectado:**
```python
# ANTES (18.2):
moves = self.filtered(lambda move: move.state == "draft")._action_confirm(
    merge=False
)

# DESPUÉS (18.2-marin):
moves = self.filtered(
    lambda move: move.state == "draft"
    or float_is_zero(
        move.product_uom_qty, precision_rounding=move.product_uom.rounding
    )
)._action_confirm(merge=False)
```

**Descripción del cambio:**
- Se amplía el criterio de selección de movimientos a confirmar antes de marcarlos como "hechos"
- **Antes:** Solo se confirmaban automáticamente los movimientos en estado `draft`
- **Después:** Se confirman movimientos en `draft` **O** movimientos cuya cantidad sea cero (considerando el redondeo de la unidad de medida)

**Razón del cambio:**
Permite manejar casos especiales donde movimientos con cantidad cero (por redondeo) necesitan ser confirmados para completar correctamente el flujo de validación.

**Instrucciones de aplicación:**
1. Localizar el método `_action_done(self, cancel_backorder=False)` en `stock.move`
2. Buscar la línea donde se filtran movimientos con `self.filtered(lambda move: move.state == "draft")`
3. Reemplazar el filtro completo por:
   ```python
   moves = self.filtered(
       lambda move: move.state == "draft"
       or float_is_zero(
           move.product_uom_qty, precision_rounding=move.product_uom.rounding
       )
   )._action_confirm(merge=False)
   ```
4. Asegurar que `float_is_zero` esté importado desde `odoo.tools.float_utils` al inicio del archivo

---

#### 3. **Eliminar validación de contexto en `_recompute_state()`**

**Ubicación:** Método `_recompute_state()`, aproximadamente línea 2733-2735

**Cambio detectado:**
```python
# ANTES (18.2):
def _recompute_state(self):
    if self._context.get("preserve_state"):
        return
    moves_state_to_write = defaultdict(set)
    ...

# DESPUÉS (18.2-marin):
def _recompute_state(self):
    moves_state_to_write = defaultdict(set)
    ...
```

**Descripción del cambio:**
- Se eliminan las líneas que verificaban si el contexto contiene `preserve_state` y detenían la ejecución
- El método ahora **siempre ejecuta** el recálculo de estado, sin importar el contexto

**Razón del cambio:**
Aparentemente el flag `preserve_state` en el contexto causaba que estados no se actualizaran correctamente en ciertos flujos, provocando inconsistencias. Al eliminar esta validación, se garantiza que el estado siempre se recalcule cuando se invoca el método.

**Instrucciones de aplicación:**
1. Localizar el método `_recompute_state(self)` en `stock.move`
2. Eliminar las siguientes líneas al inicio del método (generalmente líneas 2-3 después de la definición):
   ```python
   if self._context.get("preserve_state"):
       return
   ```
3. Mantener el resto del método sin cambios

---

### ⚙️ Consideraciones técnicas

#### Dependencias afectadas
- **Módulo:** `stock`
- **Modelo:** `stock.move`
- **Métodos modificados:**
  - `_action_cancel()`
  - `_action_done()`
  - `_recompute_state()`

#### Imports requeridos
Verificar que estén presentes al inicio del archivo:
```python
from odoo.tools.float_utils import float_is_zero, float_compare
```

#### Compatibilidad
- Versión base: Odoo 18.2 (Community/Enterprise)
- Versión objetivo: Odoo 18.2-marin (Customizada)
- Impacto: **Bajo** - Cambios quirúrgicos sin afectación a la estructura general

#### Testing recomendado
Después de aplicar los cambios, validar:

1. **Cancelación en cadena de movimientos:**
   - Crear una cadena de movimientos (ej: recepción → almacén → envío)
   - Cancelar el movimiento intermedio con `propagate_cancel=True`
   - Verificar que los movimientos descendientes se cancelen correctamente

2. **Confirmación de movimientos con cantidad cero:**
   - Crear un movimiento con `product_uom_qty = 0.0`
   - Ejecutar `_action_done()`
   - Verificar que el movimiento se confirma y completa sin errores

3. **Recálculo de estado sin contexto preserve:**
   - Ejecutar `_recompute_state()` con y sin el flag `preserve_state` en contexto
   - Verificar que el estado se recalcula en ambos casos

---

### 📊 Resumen de cambios

| Línea aprox. | Método              | Tipo de cambio        | Criticidad |
|--------------|---------------------|-----------------------|------------|
| ~1865        | `_action_cancel()`  | Corrección de lógica  | Media      |
| ~2014        | `_action_done()`    | Ampliación de filtro  | Media      |
| ~2734        | `_recompute_state()`| Eliminación de código | Baja       |

**Total de líneas modificadas:** 7 líneas añadidas, 4 líneas eliminadas

---

### 📝 Notas adicionales

- Los cambios son **quirúrgicos y focalizados**, no afectan la arquitectura general del módulo
- Se recomienda revisar casos de uso específicos de AgroMarin que puedan haber motivado estos ajustes
- Considerar documentar en el código los motivos específicos mediante comentarios inline
- Al migrar a versiones superiores de Odoo (19.0+), verificar que estos cambios siguen siendo necesarios o si ya fueron corregidos upstream

---

**Generado:** 2025-10-07
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA
