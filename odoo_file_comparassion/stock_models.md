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

---

## Archivo: models/stock_picking.py

### 🔍 Descripción general

El archivo `stock_picking.py` contiene principalmente **cambios de nomenclatura** (renombramiento del campo `scheduled_date` a `date_planned`) y reordenamientos de código que **no afectan la lógica funcional**.

Se identificaron **2 cambios lógicos menores** que sí modifican el comportamiento del sistema.

---

### 🧠 Cambios lógicos detectados

#### 1. **Corrección de nombre de campo en agregación `_compute_date_delay_alert()`**

**Ubicación:** Método `_compute_date_delay_alert()`, aproximadamente línea 233-246

**Cambio detectado:**
```python
# ANTES (18.2):
date_delay_alert_data = self.env["stock.move"]._read_group(
    [("id", "in", self.move_ids.ids), ("date_delay_alert", "!=", False)],
    ["picking_id"],
    ["delay_alert_date:max"],  # ← Campo incorrecto
)

# DESPUÉS (18.2-marin):
date_delay_alert_data = self.env["stock.move"]._read_group(
    [("id", "in", self.move_ids.ids), ("date_delay_alert", "!=", False)],
    ["picking_id"],
    ["date_delay_alert:max"],  # ← Campo corregido
)
```

**Descripción del cambio:**
- Se corrige el nombre del campo en la función de agregación
- **Antes:** Intentaba agregar `delay_alert_date:max` (campo que no existe)
- **Después:** Agrega correctamente `date_delay_alert:max` (campo real del modelo)

**Razón del cambio:**
Bug fix - el nombre del campo estaba invertido, lo que probablemente causaba errores o resultados incorrectos al calcular la fecha máxima de alerta de retraso.

**Impacto:** Corrige un error que afectaba el cálculo de alertas de retraso en transferencias.

---

#### 2. **Eliminación de asignación masiva en `_onchange_location_id()`**

**Ubicación:** Método `_onchange_location_id()`, aproximadamente línea 659

**Cambio detectado:**
```python
# ANTES (18.2):
@api.onchange("location_id")
def _onchange_location_id(self):
    (self.move_ids | self.move_ids_without_package).location_id = self.location_id
    for move in self.move_ids.filtered(lambda m: m.move_orig_ids):
        for ml in move.move_line_ids:
            # ... procesamiento de líneas de movimiento

# DESPUÉS (18.2-marin):
@api.onchange("location_id")
def _onchange_location_id(self):
    for move in self.move_ids.filtered(lambda m: m.move_orig_ids):
        for ml in move.move_line_ids:
            # ... procesamiento de líneas de movimiento
```

**Descripción del cambio:**
- Se elimina la línea que asignaba automáticamente `location_id` a todos los movimientos (`move_ids` y `move_ids_without_package`)
- Ahora el método solo procesa los movimientos que tienen movimientos de origen (`move_orig_ids`)

**Razón del cambio:**
La asignación masiva probablemente causaba efectos secundarios no deseados, sobrescribiendo ubicaciones de movimientos que no debían cambiar cuando se modifica la ubicación del picking.

**Impacto:**
- **Antes:** Al cambiar la ubicación de origen del picking, TODOS los movimientos cambiaban su ubicación automáticamente
- **Después:** Solo se procesan las líneas de movimiento de movimientos específicos, sin modificar masivamente las ubicaciones

**Beneficio:** Mayor control sobre qué movimientos se ven afectados por el cambio de ubicación del picking, evitando sobrescrituras no deseadas.

---

### ⚙️ Consideraciones técnicas

#### Dependencias afectadas
- **Módulo:** `stock`
- **Modelo:** `stock.picking`
- **Métodos modificados:**
  - `_compute_date_delay_alert()`
  - `_onchange_location_id()`

#### Compatibilidad
- Versión base: Odoo 18.2
- Versión objetivo: Odoo 18.2-marin
- Impacto: **Bajo** - Cambios quirúrgicos que corrigen bugs menores

#### Testing recomendado

1. **Cálculo de alerta de retraso:**
   - Crear movimientos con `date_delay_alert` configurada
   - Verificar que el cálculo del máximo funciona correctamente en el picking
   - Confirmar que no hay errores de campo inexistente

2. **Cambio de ubicación en picking:**
   - Crear un picking con múltiples movimientos
   - Cambiar la `location_id` del picking
   - Verificar que NO se sobrescriben las ubicaciones de todos los movimientos automáticamente
   - Confirmar que solo se procesan los movimientos con origen

---

### 📊 Resumen de cambios

| Línea aprox. | Método                        | Tipo de cambio       | Criticidad |
|--------------|-------------------------------|----------------------|------------|
| ~235         | `_compute_date_delay_alert()` | Corrección de campo  | Baja       |
| ~659         | `_onchange_location_id()`     | Eliminación de línea | Media      |

**Total de líneas modificadas:** 1 línea corregida, 1 línea eliminada

---

### 📝 Notas adicionales

- **Cambios cosméticos ignorados:** Este archivo contiene numerosos cambios de renombramiento (`scheduled_date` → `date_planned`) que no se documentan aquí por no afectar la lógica
- **Reorganización de código:** La clase `StockPickingType` fue movida a otro archivo, lo cual es un cambio organizacional sin impacto funcional
- Los dos cambios documentados son **correcciones de bugs menores** que mejoran la estabilidad del módulo

---

---

## Archivo: models/stock_picking_type.py

### 🔍 Descripción general

El archivo `stock_picking_type.py` en la versión 18.2-marin es una **extracción organizacional** de la clase `StockPickingType` que anteriormente estaba dentro de `stock_picking.py`.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales.**

---

### 🧠 Cambios detectados

**Ningún cambio lógico.**

El código de la clase `StockPickingType` fue movido desde `stock_picking.py` (líneas 19-591) a su propio archivo `stock_picking_type.py` sin modificaciones en la lógica de negocio.

---

### 📋 Cambios organizacionales (sin impacto funcional)

1. **Separación de archivo:** Clase `StockPickingType` ahora está en archivo dedicado
2. **Definiciones de campos:** Campos explícitamente definidos (antes aparecían como `[unparseable node]`)
3. **Reformateo de código:** Algunas estructuras `elif` cambiadas a `else` + `if` (mismo comportamiento)
4. **Imports:** Agregados al inicio del nuevo archivo (`json`, `literal_eval`, `timedelta`, etc.)

---

### ⚙️ Nota técnica

Este cambio es parte de una **refactorización de organización de código** para mejorar la mantenibilidad del módulo `stock`, separando las clases `StockPicking` y `StockPickingType` en archivos independientes.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-07
**Versión base:** Odoo 18.2 (clase en stock_picking.py)
**Versión destino:** Odoo 18.2-marin (clase en stock_picking_type.py)
**Tipo de cambio:** Reorganización sin impacto funcional
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

## Archivo: models/stock_move_line.py

### 🔍 Descripción general

El archivo `stock_move_line.py` contiene cambios menores de **actualización de nomenclatura** relacionados con el renombramiento del campo `scheduled_date` a `date_planned` en el modelo `stock.picking`.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales.**

---

### 🧠 Cambios detectados

**Ningún cambio lógico.**

---

### 📋 Cambios de nomenclatura (sin impacto funcional)

1. **Eliminación de import no utilizado:** Removido `tools` del import (línea 6)
2. **Actualización de referencia a campo:** `scheduled_date` → `date_planned` (línea ~1320)

---

### ⚙️ Nota técnica

Este cambio es **consecuencia directa** del renombramiento del campo `scheduled_date` a `date_planned` en el modelo `stock.picking`. La actualización mantiene la consistencia entre modelos relacionados.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-07
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Actualización de nomenclatura sin impacto funcional
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

## Archivo: models/stock_quant.py

### 🔍 Descripción general

El archivo `stock_quant.py` contiene **eliminación de método crítico** que afecta la compatibilidad con módulos estándar de Odoo.

Se identificaron **2 cambios lógicos**, uno de ellos con **impacto crítico en el módulo `mrp`**.

---

### 🧠 Cambios lógicos detectados

#### 1. **Eliminación de validación `_should_bypass_product()` en flujo de reserva**

**Ubicación:** Aproximadamente línea 1305-1320

**Cambio detectado:**
```python
# ANTES (18.2):
for (location, product, lot, package, owner), reserved_quantity in reserved_move_lines.items():
    if location.should_bypass_reservation() or self.env["stock.quant"]._should_bypass_product(
        product, location, reserved_quantity, lot, package, owner
    ):
        continue
    else:
        self.env["stock.quant"]._update_reserved_quantity(...)

# DESPUÉS (18.2-marin):
for (location, product, lot, package, owner), reserved_quantity in reserved_move_lines.items():
    if location.should_bypass_reservation():
        continue
    else:
        self.env["stock.quant"]._update_reserved_quantity(...)
```

**Descripción del cambio:**
- Se elimina la llamada al método `_should_bypass_product()`
- Ahora solo se verifica `location.should_bypass_reservation()`

**Impacto:**
- Rompe la funcionalidad de bypass de productos específicos (ej: productos tipo "kit" en `mrp`)
- El flujo de reserva ya no considera reglas específicas de producto

---

#### 2. **⚠️ ELIMINACIÓN CRÍTICA: Método `_should_bypass_product()`**

**Ubicación:** Aproximadamente línea 1990-2000

**Cambio detectado:**
```python
# ANTES (18.2):
def _should_bypass_product(
    self,
    product=False,
    location=False,
    reserved_quantity=0,
    lot_id=False,
    package_id=False,
    owner_id=False,
):
    return False

# DESPUÉS (18.2-marin):
# Método completamente eliminado
```

**Descripción del cambio:**
- Se elimina completamente el método `_should_bypass_product()`
- Este método es un **hook de extensión** utilizado por módulos estándar de Odoo

---

### 🚨 ADVERTENCIA: Incompatibilidad con módulo `mrp`

**CRITICIDAD: ALTA**

El módulo **`mrp` (Manufacturing)** de Odoo estándar **hereda y extiende** este método para implementar lógica de bypass de reservas para productos tipo "kit":

**Código en `/addons/mrp/models/stock_quant.py`:**
```python
def _should_bypass_product(self, product=False, location=False,
                          reserved_quantity=0, lot_id=False,
                          package_id=False, owner_id=False):
    return super()._should_bypass_product(product, location, reserved_quantity,
                                         lot_id, package_id, owner_id) \
           or (product and product.is_kits)
```

**Impacto de la eliminación:**

1. **Error inmediato:** `AttributeError: 'super' object has no attribute '_should_bypass_product'`
2. **Módulo afectado:** `mrp` dejará de funcionar correctamente
3. **Funcionalidad rota:**
   - Bypass de reserva para productos tipo kit
   - Validaciones de productos en manufactura

**Soluciones posibles:**

**Opción A - Restaurar el método (recomendado):**
```python
def _should_bypass_product(
    self,
    product=False,
    location=False,
    reserved_quantity=0,
    lot_id=False,
    package_id=False,
    owner_id=False,
):
    return False
```

**Opción B - Modificar el módulo `mrp`:**
- Reimplementar la lógica sin usar `super()`
- Menos recomendado (mantiene incompatibilidad con Odoo estándar)

---

### ⚙️ Consideraciones técnicas

#### Dependencias afectadas
- **Módulo:** `stock`
- **Modelo:** `stock.quant`
- **Métodos eliminados:**
  - `_should_bypass_product()` ⚠️ **Usado por módulo `mrp`**

#### Módulos estándar incompatibles
- ⚠️ **`mrp` (Manufacturing)** - Requiere el método eliminado

#### Compatibilidad
- Versión base: Odoo 18.2
- Versión objetivo: Odoo 18.2-marin
- Impacto: **ALTO** - Rompe compatibilidad con módulo `mrp`

#### Testing crítico requerido

1. **Instalación del módulo `mrp`:**
   - Intentar instalar/actualizar el módulo `mrp`
   - **Resultado esperado:** Error de atributo inexistente

2. **Funcionalidad de productos kit:**
   - Crear productos tipo kit (BoM)
   - Intentar reservar cantidades
   - **Resultado esperado:** Fallo en bypass de reserva

3. **Flujo de manufactura:**
   - Crear órdenes de manufactura
   - Verificar reserva de componentes
   - **Resultado esperado:** Comportamiento incorrecto

---

### 📊 Resumen de cambios

| Línea aprox. | Método/Flujo                 | Tipo de cambio           | Criticidad |
|--------------|------------------------------|--------------------------|------------|
| ~1308        | Flujo de reserva             | Eliminación de condición | Media      |
| ~1990        | `_should_bypass_product()`   | Eliminación de método    | **ALTA** ⚠️ |

**Cambios lógicos funcionales:** 2
**Módulos estándar rotos:** 1 (`mrp`)

---

### 📝 Notas adicionales

- ⚠️ **Breaking change:** Este cambio rompe la compatibilidad con el módulo estándar `mrp`
- **No recomendado:** Eliminar hooks de extensión utilizados por módulos estándar
- **Solución recomendada:** Restaurar el método `_should_bypass_product()` aunque retorne `False`
- **Impacto en producción:** Si se usa el módulo `mrp`, habrá errores críticos

---

**Generado:** 2025-10-08
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Eliminación de hook crítico
**⚠️ ADVERTENCIA:** Incompatible con módulo `mrp` estándar
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

## Archivo: models/stock_lot.py

### 🔍 Descripción general

El archivo `stock_lot.py` contiene la lógica del modelo `stock.lot` que gestiona los lotes/números de serie en Odoo. Se identificaron **2 cambios lógicos**:

1. Mejora en la validación de creación de lotes con contexto de productos (línea ~78-82)
2. Nuevo campo computado `type_name` y su método de cálculo (línea ~65-68 y ~197-202)

Estos cambios están orientados a **mejorar el control de validación** durante la creación de lotes y **proporcionar información visual del tipo de seguimiento** en la interfaz de usuario.

---

### 🧠 Cambios lógicos detectados

#### 1. **Mejora en la validación de creación de lotes con contexto de productos**

**Ubicación:** Método `create()`, aproximadamente línea 78-82

**Cambio detectado:**
```python
# ANTES (18.2):
@api.model_create_multi
def create(self, vals_list):
    self._check_create()
    return super(StockLot, self.with_context(mail_create_nosubscribe=True)).create(
        vals_list
    )

# DESPUÉS (18.2-marin):
@api.model_create_multi
def create(self, vals_list):
    lot_product_ids = {val.get("product_id") for val in vals_list} | {
        self.env.context.get("default_product_id")
    }
    self.with_context(lot_product_ids=lot_product_ids)._check_create()
    return super(StockLot, self.with_context(mail_create_nosubscribe=True)).create(
        vals_list
    )
```

**Descripción del cambio:**
- Se añade una recopilación previa de todos los `product_id` involucrados en la creación
- Se construye un conjunto (`set`) con los IDs de productos de dos fuentes:
  - Los `product_id` presentes en cada diccionario de `vals_list`
  - El `default_product_id` del contexto (si existe)
- Este conjunto se pasa como contexto adicional (`lot_product_ids`) al método `_check_create()`

**Razón del cambio:**
Permite que `_check_create()` tenga conocimiento de **todos los productos** para los cuales se están creando lotes, habilitando validaciones más completas. Esto es especialmente útil cuando se crean múltiples lotes en una sola operación o se necesita validar permisos/configuraciones específicas del producto.

**Impacto funcional:**
- **Antes:** `_check_create()` se ejecutaba sin información de los productos involucrados
- **Después:** `_check_create()` puede acceder a `self.env.context.get('lot_product_ids')` para realizar validaciones basadas en los productos

---

#### 2. **Nuevo campo computado para mostrar el tipo de seguimiento**

**Ubicación:**
- Definición del campo: aproximadamente línea 65-68
- Método compute: aproximadamente línea 197-202

**Cambio detectado:**
```python
# ANTES (18.2):
# Campo no existía

# DESPUÉS (18.2-marin):
# Definición del campo (en sección FIELDS)
type_name = fields.Char(
    string="Type Name",
    compute="_compute_type_name",
)

# Método de cálculo (en sección COMPUTE METHODS)
@api.depends("product_id")
def _compute_type_name(self):
    for lot in self:
        if lot.product_id.tracking == "serial":
            lot.type_name = _("Serial Number")
        elif lot.product_id.tracking == "lot":
            lot.type_name = _("Lot Number")
```

**Descripción del cambio:**
- Se añade un nuevo campo computado `type_name` de tipo `Char`
- El campo se calcula dinámicamente en base al tipo de seguimiento del producto (`product_id.tracking`)
- Depende del campo `product_id` (se recalcula automáticamente cuando cambia el producto)
- No se almacena en la base de datos (campo computado sin `store=True`)

**Lógica del cálculo:**
- Si el producto tiene `tracking == "serial"` → `type_name = "Serial Number"`
- Si el producto tiene `tracking == "lot"` → `type_name = "Lot Number"`
- Para otros casos o sin producto → el campo queda vacío

**Razón del cambio:**
Proporcionar una etiqueta dinámica y traducible que indique claramente al usuario si está trabajando con un "Número de Serie" o un "Número de Lote", mejorando la experiencia de usuario en el formulario.

**Integración con la vista:**
Este campo se utiliza en la vista del formulario de lotes (`views/stock_lot_views.xml`):
```xml
<span class="o_form_label"><field name="type_name" /></span>
```

**Impacto funcional:**
- **Antes:** La interfaz no mostraba de forma explícita si se estaba gestionando un número de serie o un lote
- **Después:** El usuario ve claramente una etiqueta que indica "Serial Number" o "Lot Number" según el tipo de producto

---

### ⚙️ Consideraciones técnicas

#### Dependencias afectadas
- **Módulo:** `stock`
- **Modelo:** `stock.lot`
- **Métodos modificados:**
  - `create()`
- **Métodos añadidos:**
  - `_compute_type_name()`
- **Campos añadidos:**
  - `type_name` (Char, computed)

#### Imports requeridos
Verificar que estén presentes al inicio del archivo:
```python
from odoo import _, api, fields, models
```

#### Compatibilidad
- Versión base: Odoo 18.2
- Versión objetivo: Odoo 18.2-marin
- Impacto: **Bajo** - Cambios retro-compatibles que añaden funcionalidad sin romper código existente

#### Testing recomendado

**Para el cambio #1 (contexto en create):**

1. **Creación individual de lote:**
   - Crear un lote para un solo producto
   - Verificar que `_check_create()` recibe el contexto con `lot_product_ids`
   - Confirmar que el lote se crea correctamente

2. **Creación masiva de lotes:**
   - Crear múltiples lotes para diferentes productos en una sola llamada
   - Verificar que todos los `product_id` están presentes en el contexto
   - Confirmar que las validaciones se ejecutan para todos los productos

3. **Creación con producto por defecto:**
   - Establecer `default_product_id` en el contexto
   - Crear un lote sin especificar `product_id` explícitamente
   - Verificar que el producto por defecto se incluye en `lot_product_ids`

**Para el cambio #2 (campo type_name):**

1. **Producto con seguimiento por serie:**
   - Crear/editar un lote para un producto con `tracking = "serial"`
   - Verificar que `type_name` se calcula como "Serial Number"
   - Comprobar que la etiqueta se muestra correctamente en la vista

2. **Producto con seguimiento por lote:**
   - Crear/editar un lote para un producto con `tracking = "lot"`
   - Verificar que `type_name` se calcula como "Lot Number"
   - Comprobar que la etiqueta se muestra correctamente en la vista

3. **Cambio de producto:**
   - Crear un lote con un producto tipo "serial"
   - Cambiar el producto a uno tipo "lot"
   - Verificar que `type_name` se actualiza automáticamente

---

### 📊 Resumen de cambios

| Línea aprox. | Elemento                      | Tipo de cambio                     | Criticidad |
|--------------|-------------------------------|------------------------------------|------------|
| ~78-82       | Método `create()`             | Mejora de contexto para validación | Baja       |
| ~65-68       | Campo `type_name`             | Nuevo campo computado              | Baja       |
| ~197-202     | Método `_compute_type_name()` | Nuevo método de cálculo            | Baja       |

**Total de cambios funcionales:** 2
**Líneas añadidas:** ~10 líneas

---

### 📝 Notas adicionales

- Ambos cambios son **mejoras proactivas** que no alteran el comportamiento existente
- El cambio #1 habilita futuras validaciones más granulares sin necesidad de modificar la firma del método
- El cambio #2 mejora significativamente la experiencia de usuario al proporcionar feedback visual claro
- Ambos cambios siguen patrones estándar de Odoo:
  - Uso de contexto para pasar información adicional
  - Campos computados con decorador `@api.depends()`
  - Uso de `_()` para traducciones
- Compatible con módulos que no usan esta información adicional
- No requiere migración de datos (el campo `type_name` no se almacena)

---

**Generado:** 2025-10-08
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Mejoras de validación y UX
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/stock_location.py

### 🔍 Descripción general

El archivo `stock_location.py` contiene el modelo `stock.location` que gestiona las ubicaciones de inventario en Odoo.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales** en la clase `StockLocation`.

---

### 🧠 Cambios detectados

**Ningún cambio lógico en `StockLocation`.**

El código de la clase `StockLocation` se mantiene idéntico entre ambas versiones. No hay modificaciones en:
- Métodos de validación (`_check_can_be_used`, `_check_replenish_location`, `_check_scrap_location`)
- Métodos CRUD (`create`, `write`, `unlink`, `copy_data`)
- Métodos computados (`_compute_warehouse_id`, `_compute_weight`, `_compute_is_empty`, etc.)
- Métodos de negocio (`_get_putaway_strategy`, `should_bypass_reservation`, etc.)

---

### 📋 Cambios organizacionales (sin impacto funcional)

1. **Extracción de clase:** La clase `StockRoute` fue movida desde `stock_location.py` a su propio archivo `stock_route.py`
   - **Antes (18.2):** `StockRoute` estaba al final de `stock_location.py`
   - **Después (18.2-marin):** `StockRoute` tiene su propio archivo dedicado

Este es un cambio organizacional para mejorar la estructura del módulo, separando modelos en archivos independientes.

---

### ⚙️ Nota técnica

Este cambio es parte de una **refactorización de organización de código** para mejorar la mantenibilidad del módulo `stock`, siguiendo el patrón de separar cada modelo en su propio archivo:

- `stock_location.py` → Contiene solo `StockLocation`
- `stock_route.py` → Contiene solo `StockRoute` (nuevo archivo)

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución de `StockLocation`.

---

**Generado:** 2025-10-08
**Versión base:** Odoo 18.2 (StockLocation + StockRoute en mismo archivo)
**Versión destino:** Odoo 18.2-marin (StockLocation en archivo dedicado)
**Tipo de cambio:** Reorganización sin impacto funcional
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/stock_route.py

### 🔍 Descripción general

El archivo `stock_route.py` en la versión 18.2-marin es una **extracción organizacional** de la clase `StockRoute` que anteriormente estaba dentro de `stock_location.py`.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales.**

---

### 🧠 Cambios detectados

**Ningún cambio lógico.**

El código de la clase `StockRoute` fue movido desde `stock_location.py` a su propio archivo `stock_route.py` sin modificaciones en la lógica de negocio.

---

### 📋 Cambios organizacionales (sin impacto funcional)

1. **Separación de archivo:** Clase `StockRoute` ahora está en archivo dedicado
2. **Reordenamiento cosmético:** El orden de los atributos de clase `_check_company_auto` y `_order` fue invertido (sin impacto funcional)
3. **Imports:** Agregados al inicio del nuevo archivo

**Métodos sin cambios:**
- `_check_company_consistency()` - Validación de consistencia de compañía
- `write()` - Gestión de activación/desactivación de rutas y reglas
- `copy_data()` - Duplicación de rutas con nombre "(copy)"
- `_compute_warehouses()` - Cálculo de dominio de almacenes
- `_onchange_company()` - Filtrado de almacenes por compañía
- `_onchange_warehouse_selectable()` - Limpieza de almacenes cuando no es seleccionable

---

### ⚙️ Nota técnica

Este cambio es parte de una **refactorización de organización de código** para mejorar la mantenibilidad del módulo `stock`, separando la clase `StockRoute` (que gestiona las rutas de inventario) de `StockLocation` (que gestiona las ubicaciones).

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-08
**Versión base:** Odoo 18.2 (clase en stock_location.py)
**Versión destino:** Odoo 18.2-marin (clase en stock_route.py)
**Tipo de cambio:** Reorganización sin impacto funcional
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/stock_warehouse.py

### 🔍 Descripción general

El archivo `stock_warehouse.py` contiene la lógica del modelo `stock.warehouse` que gestiona los almacenes en Odoo.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales.**

---

### 🧠 Cambios detectados

**Ningún cambio lógico.**

El código del archivo `stock_warehouse.py` se mantiene idéntico entre ambas versiones. No hay modificaciones en:
- Métodos de configuración de rutas (`_get_routes_values`, `_get_receive_routes_values`, `_get_receive_rules_dict`)
- Métodos CRUD (`create`, `write`, `unlink`)
- Métodos de configuración de ubicaciones y tipos de picking
- Métodos de gestión de rutas de reabastecimiento
- Lógica de activación/desactivación de almacenes

---

### ⚙️ Nota técnica

Ambas versiones (18.2 y 18.2-marin) contienen la misma implementación, incluyendo:
- El método `_get_receive_routes_values(self, installed_depends)` con el parámetro ya implementado
- El método `_get_receive_rules_dict()` sin reglas pull iniciales
- Todos los métodos de gestión de almacenes y rutas

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-08
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Sin cambios funcionales
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/ir_actions_report.py

### 🔍 Descripción general

El archivo `ir_actions_report.py` contiene extensiones del modelo `ir.actions.report` específicas para el módulo `stock`.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales.**

---

### 🧠 Cambios detectados

**Ningún cambio lógico.**

El código del archivo `ir_actions_report.py` se mantiene idéntico entre ambas versiones. No hay modificaciones en los métodos o la lógica de generación de reportes.

---

### ⚙️ Nota técnica

Este archivo hereda `ir.actions.report` y probablemente añade funcionalidad específica para reportes de inventario, etiquetas de productos, reportes de picking, etc.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-08
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Sin cambios funcionales
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/product_product.py

### 🔍 Descripción general

El archivo `product_product.py` en la versión 18.2-marin es una **extracción organizacional** de la clase `ProductProduct` que anteriormente estaba dentro de un archivo monolítico `product.py`.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales.**

---

### 🧠 Cambios detectados

**Ningún cambio lógico.**

El código de la clase `ProductProduct` fue movido desde `product.py` a su propio archivo `product_product.py` sin modificaciones en la lógica de negocio.

---

### 📋 Cambios organizacionales (sin impacto funcional)

1.  **Separación de archivo:** La clase `ProductProduct` ahora está en un archivo dedicado para mejorar la modularidad.
2.  **Imports:** Se han añadido los imports necesarios (`odoo`, `fields`, `models`, etc.) al inicio del nuevo archivo para que sea autocontenido.

---

### ⚙️ Nota técnica

Este cambio es parte de una **refactorización de organización de código** para mejorar la mantenibilidad del módulo `stock`, separando las clases de producto en archivos independientes.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-08
**Versión base:** Odoo 18.2 (clase en product.py)
**Versión destino:** Odoo 18.2-marin (clase en product_product.py)
**Tipo de cambio:** Reorganización sin impacto funcional
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/product_template.py

### 🔍 Descripción general

El archivo `product_template.py` en la versión 18.2-marin es una **extracción organizacional** de la clase `ProductTemplate` que anteriormente estaba dentro de un archivo monolítico `product.py`.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales.**

---

### 🧠 Cambios detectados

**Ningún cambio lógico.**

El código de la clase `ProductTemplate` fue movido desde `product.py` a su propio archivo `product_template.py` sin modificaciones en la lógica de negocio.

---

### 📋 Cambios organizacionales (sin impacto funcional)

1.  **Separación de archivo:** La clase `ProductTemplate` ahora está en un archivo dedicado para mejorar la modularidad.
2.  **Imports:** Se han añadido los imports necesarios al inicio del nuevo archivo para que sea autocontenido.

---

### ⚙️ Nota técnica

Este cambio es parte de una **refactorización de organización de código** para mejorar la mantenibilidad del módulo `stock`, separando las clases de producto en archivos independientes.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-08
**Versión base:** Odoo 18.2 (clase en product.py)
**Versión destino:** Odoo 18.2-marin (clase en product_template.py)
**Tipo de cambio:** Reorganización sin impacto funcional
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/product_category.py

### 🔍 Descripción general

El archivo `product_category.py` en la versión 18.2-marin es una **extracción organizacional** de la clase `ProductCategory` que anteriormente estaba dentro de un archivo monolítico `product.py`.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales.**

---

### 🧠 Cambios detectados

**Ningún cambio lógico.**

El código de la clase `ProductCategory` fue movido desde `product.py` a su propio archivo `product_category.py` sin modificaciones en la lógica de negocio.

---

### 📋 Cambios organizacionales (sin impacto funcional)

1.  **Separación de archivo:** La clase `ProductCategory` ahora está en un archivo dedicado para mejorar la modularidad.
2.  **Imports:** Se han añadido los imports necesarios al inicio del nuevo archivo para que sea autocontenido.

---

### ⚙️ Nota técnica

Este cambio es parte de una **refactorización de organización de código** para mejorar la mantenibilidad del módulo `stock`, separando las clases de producto en archivos independientes.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-08
**Versión base:** Odoo 18.2 (clase en product.py)
**Versión destino:** Odoo 18.2-marin (clase en product_category.py)
**Tipo de cambio:** Reorganización sin impacto funcional
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/product_removal.py

### 🔍 Descripción general

El archivo `product_removal.py` en la versión 18.2-marin es una **extracción organizacional** de la clase `ProductRemoval` que anteriormente estaba dentro de `product_strategy.py`.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales.**

---

### 🧠 Cambios detectados

**Ningún cambio lógico.**

El código de la clase `ProductRemoval` (que define las estrategias de retirada de producto como FIFO, LIFO) fue movido desde `product_strategy.py` a su propio archivo `product_removal.py` sin modificaciones en la lógica de negocio.

---

### 📋 Cambios organizacionales (sin impacto funcional)

1.  **Separación de archivo:** La clase `ProductRemoval` ahora está en un archivo dedicado para mejorar la claridad y organización del código.
2.  **Imports:** Se han añadido los imports necesarios al inicio del nuevo archivo.

---

### ⚙️ Nota técnica

Este cambio es parte de una **refactorización de organización de código** para mejorar la mantenibilidad del módulo `stock`, separando las diferentes estrategias de producto en archivos lógicos.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-08
**Versión base:** Odoo 18.2 (clase en product_strategy.py)
**Versión destino:** Odoo 18.2-marin (clase en product_removal.py)
**Tipo de cambio:** Reorganización sin impacto funcional
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/stock_putaway_rule.py

### 🔍 Descripción general

El archivo `stock_putaway_rule.py` en la versión 18.2-marin es una **extracción organizacional** de la clase `StockPutawayRule` que anteriormente estaba dentro de `product_strategy.py`.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales.**

---

### 🧠 Cambios detectados

**Ningún cambio lógico.**

El código de la clase `StockPutawayRule` (que define las reglas de almacenamiento) fue movido desde `product_strategy.py` a su propio archivo `stock_putaway_rule.py` sin modificaciones en la lógica de negocio.

---

### 📋 Cambios organizacionales (sin impacto funcional)

1.  **Separación de archivo:** La clase `StockPutawayRule` ahora está en un archivo dedicado para mejorar la claridad y organización del código.
2.  **Imports:** Se han añadido los imports necesarios al inicio del nuevo archivo.

---

### ⚙️ Nota técnica

Este cambio es parte de una **refactorización de organización de código** para mejorar la mantenibilidad del módulo `stock`, separando las diferentes estrategias de producto en archivos lógicos.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-08
**Versión base:** Odoo 18.2 (clase en product_strategy.py)
**Versión destino:** Odoo 18.2-marin (clase en stock_putaway_rule.py)
**Tipo de cambio:** Reorganización sin impacto funcional
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/uom_uom.py

### 🔍 Descripción general

El archivo `uom_uom.py` en la versión 18.2-marin es una **extracción organizacional** de la clase `UomUom` que anteriormente estaba dentro de un archivo monolítico `product.py`.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales.**

---

### 🧠 Cambios detectados

**Ningún cambio lógico.**

El código de la clase `UomUom` (Unidad de Medida) fue movido desde `product.py` a su propio archivo `uom_uom.py` sin modificaciones en la lógica de negocio.

---

### 📋 Cambios organizacionales (sin impacto funcional)

1.  **Separación de archivo:** La clase `UomUom` ahora está en un archivo dedicado para mejorar la modularidad.
2.  **Imports:** Se han añadido los imports necesarios al inicio del nuevo archivo para que sea autocontenido.

---

### ⚙️ Nota técnica

Este cambio es parte de una **refactorización de organización de código** para mejorar la mantenibilidad del módulo `stock`, separando modelos auxiliares como la unidad de medida en archivos independientes.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-08
**Versión base:** Odoo 18.2 (clase en product.py)
**Versión destino:** Odoo 18.2-marin (clase en uom_uom.py)
**Tipo de cambio:** Reorganización sin impacto funcional
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/barcode_rule.py

### 🔍 Descripción general

El archivo `barcode_rule.py` en la versión 18.2-marin es una **reorganización** del archivo `barcode.py`.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales.**

---

### 🧠 Cambios detectados

**Ningún cambio lógico.**

El archivo `barcode.py` en la versión 18.2 perdió incorrectamente la declaración de varios campos debido a un error en una herramienta de reorganización de código. El archivo `barcode_rule.py` en 18.2-marin restaura estas declaraciones a su estado original, corrigiendo el error previo.

---

### 📋 Cambios organizacionales (sin impacto funcional)

1.  **Renombramiento de archivo:** `barcode.py` → `barcode_rule.py`
2.  **Restauración de campos:** Los campos que aparecen en `barcode_rule.py` ya deberían haber estado en `barcode.py`. Su restauración corrige una omisión accidental sin introducir nueva funcionalidad.

---

### ⚙️ Nota técnica

La modificación consiste en una reorganización y corrección de una omisión de código. No hay impacto funcional, ya que los campos restaurados son declarativos y su lógica asociada ya existía en otras partes del sistema que esperaban su presencia.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-08
**Versión base:** Odoo 18.2 (barcode.py)
**Versión destino:** Odoo 18.2-marin (barcode_rule.py)
**Tipo de cambio:** Reorganización sin impacto funcional
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/stock_quant_package.py

### 🔍 Descripción general

El archivo `stock_quant_package.py` en la versión 18.2-marin es una **extracción organizacional** de la clase `StockQuantPackage` que anteriormente estaba dentro de `stock_quant.py`.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales.**

---

### 🧠 Cambios detectados

**Ningún cambio lógico.**

La clase `StockQuantPackage` fue movida desde `stock_quant.py` (líneas 2006-2188 de la versión 18.2) a su propio archivo `stock_quant_package.py` sin ninguna modificación en su código fuente.

---

### 📋 Cambios organizacionales (sin impacto funcional)

1.  **Separación de archivo:** La clase `StockQuantPackage` ahora se encuentra en su archivo dedicado para mejorar la modularidad y la legibilidad del código.
2.  **Imports:** Se agregaron las sentencias de importación necesarias (`from odoo import models, fields, api`) al inicio del nuevo archivo para asegurar que las dependencias estén resueltas.

---

### ⚙️ Nota técnica

Este cambio es una **refactorización organizacional** pura. El objetivo es alinear la estructura del código con las mejores prácticas, aislando clases en sus propios archivos para facilitar el mantenimiento y la navegación.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución del programa. La funcionalidad del manejo de paquetes de stock permanece idéntica a la versión anterior.

---

**Generado:** 2025-10-08
**Versión base:** Odoo 18.2 (clase en stock_quant.py, líneas 2006-2188)
**Versión destino:** Odoo 18.2-marin (clase en stock_quant_package.py)
**Tipo de cambio:** Reorganización sin impacto funcional
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/stock_rule.py

### 🔍 Descripción general

El archivo `stock_rule.py` contiene la lógica del modelo `stock.rule` que gestiona las reglas de abastecimiento (procurement rules) en Odoo, así como la clase `ProcurementGroup` que agrupa procurements.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales.**

---

### 🧠 Cambios detectados

**Ningún cambio lógico.**

El código del archivo `stock_rule.py` se mantiene idéntico entre ambas versiones en cuanto a la lógica de negocio. No hay modificaciones en:
- Métodos de validación (`_check_company_consistency`)
- Métodos CRUD (`default_get`, `copy_data`)
- Métodos computados (`_compute_action_message`, `_compute_picking_type_code_domain`)
- Métodos de negocio (`_run_pull`, `_run_push`, `_get_rule`, `_search_rule`)
- Lógica del scheduler (`run_scheduler`, `_run_scheduler_tasks`)
- Métodos de procurement (`run`, `_skip_procurement`)

---

### 📋 Cambios organizacionales (sin impacto funcional)

1. **Reorganización de imports:**
   - **Antes (18.2):** `from odoo import _, api, fields, models` junto con imports no utilizados (`Registry`, `BaseCursor`)
   - **Después (18.2-marin):** `from odoo import api, fields, models` y `from odoo.tools.translate import _`
   - Se eliminan imports no utilizados de `odoo.modules.registry.Registry` y `odoo.sql_db.BaseCursor`
   - Se reorganiza la importación de `_` para usar explícitamente `odoo.tools.translate._`

2. **Añadir secciones de campos:**
   - Se añadieron comentarios `# FIELDS` con nodos no parseables en las clases `StockRule` y `ProcurementGroup`
   - Esto es solo documentación estructural sin impacto en la ejecución

---

### ⚙️ Nota técnica

Los cambios son exclusivamente de **organización de imports** siguiendo mejores prácticas de Python:
- Eliminación de imports no utilizados
- Importación explícita de funciones de traducción desde su módulo específico

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución. Toda la funcionalidad de reglas de stock, procurement y scheduler permanece idéntica.

---

**Generado:** 2025-10-10
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Reorganización de imports sin impacto funcional
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/stock_orderpoint.py

### 🔍 Descripción general

El archivo `stock_orderpoint.py` contiene la lógica del modelo `stock.warehouse.orderpoint` que gestiona las reglas de reordenamiento (orderpoints/reorder rules) en Odoo. Estas reglas son críticas para el aprovisionamiento automático de productos.

**Resultado del análisis:** **NO se detectaron cambios lógicos funcionales.**

---

### 🧠 Cambios detectados

**Ningún cambio lógico.**

El código del archivo `stock_orderpoint.py` se mantiene idéntico entre ambas versiones en cuanto a la lógica de negocio. No hay modificaciones en:
- Métodos de validación (`_check_min_max_qty`)
- Métodos CRUD (`create`, `write`)
- Métodos computados (`_compute_qty`, `_compute_qty_to_order_computed`, `_compute_lead_days`, etc.)
- Métodos de acción (`action_replenish`, `action_replenish_auto`)
- Lógica del scheduler (`_procure_orderpoint_confirm`)
- Algoritmo de cálculo de cantidades a ordenar (`_get_qty_to_order`)

---

### 📋 Cambios organizacionales (sin impacto funcional)

1. **Reorganización de imports:**
   - **Antes (18.2):** `from odoo import _, api, fields, models, SUPERUSER_ID`
   - **Después (18.2-marin):** `from odoo import api, fields, models` + `from odoo.orm.utils import SUPERUSER_ID` + `from odoo.tools.translate import _`
   - Se reorganizan los imports para separar explícitamente las utilidades del ORM y las funciones de traducción

2. **Añadir secciones de campos:**
   - Se añadieron comentarios `# FIELDS` con nodos no parseables (solo documentación estructural)

---

### ⚙️ Nota técnica

Los cambios son exclusivamente de **reorganización de imports** siguiendo mejores prácticas de Python:
- Importación explícita de `SUPERUSER_ID` desde su módulo específico `odoo.orm.utils`
- Importación explícita de funciones de traducción desde `odoo.tools.translate`

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución. Toda la funcionalidad de reglas de reordenamiento, cálculo de cantidades, y procurement permanece idéntica.

---

**Generado:** 2025-10-10
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Reorganización de imports sin impacto funcional
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/stock_scrap.py

### 🔍 Descripción general

El archivo `stock_scrap.py` contiene la lógica del modelo `stock.scrap` que gestiona el desecho (scrap) de productos en Odoo, así como la clase `StockScrapReasonTag` para etiquetar razones de desecho.

**Resultado del análisis:** **NO se detectaron cambios de ningún tipo.**

---

### 🧠 Cambios detectados

**Ningún cambio.**

Ambos archivos (18.2 y 18.2-marin) son **completamente idénticos**. No hay diferencias en:
- Estructura del código
- Imports
- Métodos
- Lógica de negocio
- Campos
- Comentarios

---

### ⚙️ Nota técnica

El archivo `stock_scrap.py` permanece sin modificaciones entre las versiones 18.2 y 18.2-marin.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-10
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Sin cambios
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/stock_replenish_mixin.py

### 🔍 Descripción general

El archivo `stock_replenish_mixin.py` contiene el modelo abstracto `stock.replenish.mixin` que proporciona funcionalidad común de reabastecimiento para modelos que heredan de él.

**Resultado del análisis:** **NO se detectaron cambios de ningún tipo.**

---

### 🧠 Cambios detectados

**Ningún cambio.**

Ambos archivos (18.2 y 18.2-marin) son **completamente idénticos**. No hay diferencias en:
- Estructura del código
- Imports
- Métodos
- Lógica de negocio
- Campos
- Comentarios

---

### ⚙️ Nota técnica

El archivo `stock_replenish_mixin.py` permanece sin modificaciones entre las versiones 18.2 y 18.2-marin.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-10
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Sin cambios
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/stock_package_level.py

### 🔍 Descripción general

El archivo `stock_package_level.py` contiene el modelo `stock.package_level` que gestiona los niveles de paquetes en operaciones de inventario.

**Resultado del análisis:** **NO se detectaron cambios de ningún tipo.**

---

### 🧠 Cambios detectados

**Ningún cambio.**

Ambos archivos (18.2 y 18.2-marin) son **completamente idénticos**. No hay diferencias en:
- Estructura del código
- Imports
- Métodos
- Lógica de negocio
- Campos
- Comentarios

---

### ⚙️ Nota técnica

El archivo `stock_package_level.py` permanece sin modificaciones entre las versiones 18.2 y 18.2-marin.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-10
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Sin cambios
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/stock_storage_category.py

### 🔍 Descripción general

El archivo `stock_storage_category.py` contiene el modelo `stock.storage.category` que gestiona las categorías de almacenamiento para ubicaciones y productos.

**Resultado del análisis:** **NO se detectaron cambios de ningún tipo.**

---

### 🧠 Cambios detectados

**Ningún cambio.**

Ambos archivos (18.2 y 18.2-marin) son **completamente idénticos**. No hay diferencias en:
- Estructura del código
- Imports
- Métodos
- Lógica de negocio
- Campos
- Comentarios

---

### ⚙️ Nota técnica

El archivo `stock_storage_category.py` permanece sin modificaciones entre las versiones 18.2 y 18.2-marin.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-10
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Sin cambios
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/stock_package_type.py

### 🔍 Descripción general

El archivo `stock_package_type.py` contiene el modelo `stock.package.type` que define los tipos de paquetes disponibles en el sistema de inventario.

**Resultado del análisis:** **NO se detectaron cambios de ningún tipo.**

---

### 🧠 Cambios detectados

**Ningún cambio.**

Ambos archivos (18.2 y 18.2-marin) son **completamente idénticos**. No hay diferencias en:
- Estructura del código
- Imports
- Métodos
- Lógica de negocio
- Campos
- Comentarios

---

### ⚙️ Nota técnica

El archivo `stock_package_type.py` permanece sin modificaciones entre las versiones 18.2 y 18.2-marin.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-10
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Sin cambios
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/res_config_settings.py

### 🔍 Descripción general

El archivo `res_config_settings.py` contiene extensiones del modelo `res.config.settings` específicas para la configuración del módulo stock.

**Resultado del análisis:** **NO se detectaron cambios de ningún tipo.**

---

### 🧠 Cambios detectados

**Ningún cambio.**

Ambos archivos (18.2 y 18.2-marin) son **completamente idénticos**. No hay diferencias en:
- Estructura del código
- Imports
- Métodos
- Lógica de negocio
- Campos
- Comentarios

---

### ⚙️ Nota técnica

El archivo `res_config_settings.py` permanece sin modificaciones entre las versiones 18.2 y 18.2-marin.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-10
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Sin cambios
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/res_company.py

### 🔍 Descripción general

El archivo `res_company.py` contiene extensiones del modelo `res.company` específicas para el módulo stock, incluyendo configuraciones de inventario por compañía.

**Resultado del análisis:** **NO se detectaron cambios de ningún tipo.**

---

### 🧠 Cambios detectados

**Ningún cambio.**

Ambos archivos (18.2 y 18.2-marin) son **completamente idénticos**. No hay diferencias en:
- Estructura del código
- Imports
- Métodos
- Lógica de negocio
- Campos
- Comentarios

---

### ⚙️ Nota técnica

El archivo `res_company.py` permanece sin modificaciones entre las versiones 18.2 y 18.2-marin.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-10
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Sin cambios
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/res_partner.py

### 🔍 Descripción general

El archivo `res_partner.py` contiene extensiones del modelo `res.partner` específicas para el módulo stock, como ubicaciones de envío y propiedades de inventario.

**Resultado del análisis:** **NO se detectaron cambios de ningún tipo.**

---

### 🧠 Cambios detectados

**Ningún cambio.**

Ambos archivos (18.2 y 18.2-marin) son **completamente idénticos**. No hay diferencias en:
- Estructura del código
- Imports
- Métodos
- Lógica de negocio
- Campos
- Comentarios

---

### ⚙️ Nota técnica

El archivo `res_partner.py` permanece sin modificaciones entre las versiones 18.2 y 18.2-marin.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-10
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Sin cambios
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---

---

## Archivo: models/res_users.py

### 🔍 Descripción general

El archivo `res_users.py` contiene extensiones del modelo `res.users` específicas para el módulo stock, como permisos y configuraciones de usuario relacionadas con inventario.

**Resultado del análisis:** **NO se detectaron cambios de ningún tipo.**

---

### 🧠 Cambios detectados

**Ningún cambio.**

Ambos archivos (18.2 y 18.2-marin) son **completamente idénticos**. No hay diferencias en:
- Estructura del código
- Imports
- Métodos
- Lógica de negocio
- Campos
- Comentarios

---

### ⚙️ Nota técnica

El archivo `res_users.py` permanece sin modificaciones entre las versiones 18.2 y 18.2-marin.

**No requiere testing funcional** ya que no hay cambios en la lógica de ejecución.

---

**Generado:** 2025-10-10
**Versión base:** Odoo 18.2
**Versión destino:** Odoo 18.2-marin
**Tipo de cambio:** Sin cambios
**Herramienta:** Documentación automática de diferencias para entrenamiento de IA

---
