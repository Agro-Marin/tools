# Guía de Estructura CSV Enhanced - field_method_detector

## 🎯 Propósito

Este documento describe la estructura del CSV enhanced generado por `field_method_detector`, diseñado para alimentar la herramienta `field_method_renaming` con información completa sobre cambios de nombres y sus referencias cruzadas.

## 📊 Estructura del CSV Enhanced

### **Archivo de Entrada**: `odoo_field_changes_detected.csv`
- **Total de registros**: 497 cambios detectados (vs ~43 del formato anterior)
- **Cambios primarios**: 191 declaraciones principales  
- **Referencias cruzadas**: 224 referencias entre modelos
- **Aumento de detección**: 1,155% más información de impacto

### **Columnas del CSV (12 campos)**

```csv
change_id,old_name,new_name,item_type,module,model,change_scope,impact_type,context,confidence,parent_change_id,validation_status
```

## 📋 Descripción Detallada de Campos

> **Nota importante**: Esta estructura CSV clasifica con precisión los modelos de extensión de Odoo (aquellos que usan `_name` y `_inherit` con el mismo valor). Las siguientes descripciones incluyen la lógica actualizada que trata las definiciones en módulos de extensión como un tipo especial de herencia vinculada a la declaración original del módulo base.

### **1. `change_id`** 
- **Tipo**: String (entero secuencial)
- **Ejemplo**: `"1"`, `"2"`, `"202"`
- **Propósito**: Identificador único para cada fila/cambio
- **Uso**: Permite trazabilidad y referencia específica

### **2. `old_name`**
- **Tipo**: String  
- **Ejemplo**: `"supplier_invoice_count"`, `"_get_display_price"`
- **Propósito**: Nombre actual del campo o método
- **Uso**: Identificar qué elemento renombrar

### **3. `new_name`**
- **Tipo**: String
- **Ejemplo**: `"count_supplier_invoice"`, `"_get_price_display"`  
- **Propósito**: Nombre sugerido para el campo/método
- **Uso**: Target del renaming para la herramienta ejecutora

### **4. `item_type`**
- **Tipo**: String (enum)
- **Valores posibles**:
  - `"field"`: Campo de modelo Odoo
  - `"method"`: Método de clase Python
- **Ejemplo**: `"field"`, `"method"`
- **Propósito**: Clasificar el tipo de elemento a renombrar

### **5. `module`**
- **Tipo**: String
- **Ejemplo**: `"account"`, `"sale"`, `"product"`
- **Propósito**: Módulo Odoo donde se localiza el cambio
- **Uso**: Scoping y organización por módulo

### **6. `model`**
- **Tipo**: String (nombre de modelo Odoo)
- **Ejemplo**: `"res.partner"`, `"sale.order"`, `"product.template"`
- **Propósito**: Modelo específico donde ocurre el cambio
- **Uso**: Localización exacta dentro del módulo

### **7. `change_scope`**
- **Tipo**: String (enum)
- **Valores posibles**:
  - `"declaration"`: La definición de un campo o método. Ocurre en el módulo base (donde es `impact_type: "primary"`) y también en módulos de extensión que heredan y redefinen el mismo elemento (donde es `impact_type: "inheritance"`)
  - `"reference"`: Referencia al elemento en código Python
  - `"call"`: Llamada a método
  - `"super_call"`: Llamada explícita a un método de la clase padre usando `super()`. Este scope se utiliza cuando un método en un modelo hijo **llama** a su versión padre
- **Ejemplo**: `"declaration"`, `"reference"`, `"super_call"`
- **Propósito**: Clasificar sintácticamente cómo se usa el elemento
- **Nota**: No confundir `change_scope: "super_call"` (una llamada a método padre) con `change_scope: "declaration"` + `impact_type: "inheritance"` (una definición en módulo de extensión)

### **8. `impact_type`**
- **Tipo**: String (enum)
- **Valores posibles**:
  - `"primary"`: Cambio principal (la declaración original en el módulo base)
  - `"self_reference"`: Referencia dentro del mismo modelo
  - `"self_call"`: Llamada dentro del mismo modelo
  - `"cross_model"`: Referencia desde modelo diferente
  - `"cross_model_call"`: Llamada desde modelo diferente
  - `"inheritance"`: Identifica un cambio en un modelo heredado. Puede ser una **declaración** en un módulo de extensión (que extiende un modelo base y redefine el mismo elemento) o una **referencia/llamada** dentro de un modelo hijo
  - `"decorator"`: Uso en decorador (ej: @api.depends)
- **Ejemplo**: `"primary"`, `"cross_model"`, `"inheritance"`
- **Propósito**: Clasificar semánticamente el impacto del cambio
- **Nota especial**: `impact_type: "inheritance"` + `change_scope: "declaration"` indica una definición en un módulo de extensión de Odoo

### **9. `context`**
- **Tipo**: String (opcional)
- **Ejemplo**: `"_compute_field_value"`, `"action_create_invoice"`
- **Propósito**: Información contextual sobre dónde se encontró la referencia
- **Uso**: Ayudar al desarrollador a localizar el código específico

### **10. `confidence`**
- **Tipo**: String (float formateado)
- **Rango**: `"0.000"` a `"1.000"`
- **Ejemplo**: `"0.900"`, `"1.000"`, `"0.784"`
- **Propósito**: Nivel de confianza en la detección automática
- **Uso**: Priorización de revisión y auto-aprobación

### **11. `parent_change_id`**
- **Tipo**: String (referencia a change_id) o vacío
- **Ejemplo**: `""` (para primarios), `"10"` (para referencias)
- **Propósito**: Establece jerarquía padre-hijo entre declaración y referencias
- **Uso**: Agrupación y procesamiento en lotes

### **12. `validation_status`**
- **Tipo**: String (enum)
- **Valores posibles**:
  - `"pending"`: Pendiente de revisión manual
  - `"approved"`: Aprobado manualmente por el usuario
  - `"rejected"`: Rechazado manualmente por el usuario  
  - `"auto_approved"`: Aprobado automáticamente (confianza ≥ 90%)
- **Ejemplo**: `"auto_approved"`, `"pending"`
- **Propósito**: Estado de la decisión de aplicar el cambio
- **Uso**: Control de flujo para herramienta de renaming

## 🔗 Relación Jerárquica (parent_change_id)

### **Caso Especial: Modelos de Extensión de Odoo**

Cuando un modelo en Odoo usa `_inherit = 'some.model'` y `_name = 'some.model'`, no está creando un nuevo modelo, sino extendiendo el original. El detector clasifica con precisión este patrón:

**Código de ejemplo:**
```python
# En el módulo 'sale' (modelo base)
class SaleOrder(models.Model):
    _name = 'sale.order'
    order_line = fields.One2many(...)  # Declaración original

# En el módulo 'sale_stock' (modelo de extensión)
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'
    order_line = fields.One2many(string="Líneas extendidas")  # Re-declaración
```

**Clasificación en CSV:**

1. **Definición en el módulo base**:
   - `change_scope`: `"declaration"`
   - `impact_type`: `"primary"`
   - `parent_change_id`: `""` (vacío)

2. **Definición en el módulo de extensión**:
   - `change_scope`: `"declaration"` (porque es una definición `def` o `field = ...`)
   - `impact_type`: `"inheritance"` (porque ocurre en un contexto de herencia)
   - `parent_change_id`: (ID de la declaración `primary` en el módulo base)

Esto permite que la herramienta de refactoring entienda que ambas declaraciones están vinculadas y deben ser renombradas juntas.

### **Estructura de Datos**
El CSV implementa una relación padre-hijo donde:

1. **Cambios Primarios** (`impact_type: "primary"`):
   - `parent_change_id` = vacío (`""`)
   - `change_scope` = `"declaration"`
   - Representan la definición original del campo/método

2. **Referencias** (todos los demás `impact_type`):
   - `parent_change_id` = `change_id` del cambio primario
   - `change_scope` = `"reference"`, `"call"`, etc.
   - Representan usos/referencias del elemento primario

### **Ejemplo de Jerarquía**

#### **Ejemplo 1: Declaración primaria con referencias cruzadas**
```csv
change_id,old_name,new_name,item_type,module,model,change_scope,impact_type,context,confidence,parent_change_id,validation_status
10,invoice_status,invoice_state,field,point_of_sale,portal.mixin,declaration,primary,,0.900,,auto_approved
202,invoice_status,invoice_state,field,sale,sale.order,reference,cross_model,_compute_field_value,0.784,10,pending
203,invoice_status,invoice_state,field,sale,sale.order,reference,cross_model,_get_prepaid_service_lines_to_upsell,0.784,10,pending
204,invoice_status,invoice_state,field,project,project.create.invoice,reference,cross_model,_compute_candidate_orders,0.784,10,pending
```

En este ejemplo:
- **Cambio 10**: Declaración principal en `portal.mixin`
- **Cambios 202-204**: Referencias desde otros modelos que usan `invoice_status`

#### **Ejemplo 2: Modelo de extensión con declaración heredada**
```csv
change_id,old_name,new_name,item_type,module,model,change_scope,impact_type,context,confidence,parent_change_id,validation_status
50,order_line,order_line_ids,field,sale,sale.order,declaration,primary,,0.950,,auto_approved
51,order_line,order_line_ids,field,sale_stock,sale.order,declaration,inheritance,,0.900,50,auto_approved
52,order_line,order_line_ids,field,sale_margin,sale.order,declaration,inheritance,,0.900,50,auto_approved
78,order_line,order_line_ids,field,sale,sale.order,reference,self_reference,_prepare_invoice_line,0.850,50,auto_approved
```

En este ejemplo:
- **Cambio 50**: Declaración principal en módulo base `sale`
- **Cambios 51-52**: Declaraciones en módulos de extensión (`sale_stock`, `sale_margin`) que redefinen el mismo campo
- **Cambio 78**: Referencia dentro del mismo modelo base

## 📈 Análisis de Confianza y Auto-Aprobación

### **Sistema de Confianza**
- **Confianza alta (≥ 0.90)**: Auto-aprobado automáticamente
- **Confianza media (0.70-0.89)**: Requiere revisión manual  
- **Confianza baja (< 0.70)**: Requiere revisión cuidadosa

### **Distribución Actual**
- **Auto-aprobados**: ~191 cambios primarios (alta confianza)
- **Pendientes**: ~224 referencias cruzadas (requieren validación)
- **Ratio**: 46% auto-aprobados, 54% requieren revisión

## 🎯 Flujo de Validación

### **Estados del Ciclo de Vida**
1. **Generación**: Todas las filas inician como `"pending"` o `"auto_approved"`
2. **Revisión**: Usuario interactúa con ValidationUI para aprobar/rechazar
3. **Aplicación**: Herramienta de renaming procesa solo `"approved"` y `"auto_approved"`

### **Acciones Disponibles**
- **Aprobar todo**: Cambiar estado de grupo completo (primario + referencias)
- **Granular**: Revisar cada referencia individualmente
- **Solo primario**: Aprobar solo declaración, rechazar referencias
- **Rechazar todo**: Marcar grupo completo como rechazado
- **Editar**: Modificar `new_name` durante validación

## 🔧 Integración con field_method_renaming

### **Campos Críticos para Renaming**
```python
# Campos mínimos requeridos para field_method_renaming:
essential_fields = [
    "old_name",           # Qué renombrar
    "new_name",           # A qué renombrar  
    "item_type",          # field vs method
    "module",             # Dónde buscar
    "model",              # Modelo específico
    "validation_status"   # Si aplicar o no
]
```

### **Filtro de Procesamiento**
```python
# Solo procesar cambios aprobados:
approved_changes = csv_data[
    (csv_data['validation_status'].isin(['approved', 'auto_approved']))
]
```

### **Agrupación por Parent ID**
```python
# Agrupar referencias por cambio primario:
primary_changes = approved_changes[approved_changes['impact_type'] == 'primary']
references = approved_changes[approved_changes['impact_type'] != 'primary']

# Relacionar references con su primary via parent_change_id
for primary in primary_changes:
    related_refs = references[references['parent_change_id'] == primary['change_id']]
```

## ⚡ Beneficios del Formato Enhanced

### **Vs Formato Anterior**
- **Detección completa**: 497 vs ~43 cambios detectados
- **Trazabilidad**: Jerarquía padre-hijo clara
- **Automatización**: Auto-aprobación basada en confianza
- **Granularidad**: Control por referencia individual
- **Context**: Información para localizar código específico

### **Para field_method_renaming**
- **Precisión**: Sabe exactamente dónde aplicar cada cambio
- **Seguridad**: Solo procesa cambios validados por el usuario
- **Eficiencia**: Puede procesar en lotes por modelo/módulo
- **Rollback**: Información suficiente para revertir cambios si es necesario

## 📊 Estadísticas del CSV Actual

```
Total de cambios detectados: 497
├── Cambios primarios: 191 (38%)
├── Referencias cruzadas: 224 (45%)  
├── Otros impactos: 82 (17%)
│
├── Auto-aprobados: ~191 (38%)
├── Pendientes de revisión: ~306 (62%)
│
├── Campos: ~245 (49%)
└── Métodos: ~252 (51%)
```

## 🎯 Recomendaciones de Uso

### **Para Revisión Manual**
1. **Priorizar** cambios con `confidence < 0.80`
2. **Revisar cuidadosamente** `impact_type: "cross_model"`
3. **Validar contexto** en cambios con `context` específico
4. **Agrupar por** `parent_change_id` para eficiencia

### **Para Automatización**
1. **Confiar** en `auto_approved` con `confidence ≥ 0.90`
2. **Procesar en lotes** por módulo para minimizar riesgo
3. **Validar sintaxis** antes de aplicar cambios masivos
4. **Mantener backup** para rollback en caso de errores

### **Para Debugging**
1. **Usar** `change_id` para trazabilidad específica
2. **Seguir** `parent_change_id` para entender impacto completo
3. **Examinar** `context` para localizar código problemático
4. **Filtrar por** `module` y `model` para scope limitado

## 🔄 Evolución y Extensibilidad

El formato CSV enhanced está diseñado para evolucionar:

- **Nuevos impact_types**: Para XML views, JS code, etc.
- **Más context**: Información de línea de código, git blame, etc.
- **Confidence mejorado**: ML-based scoring, user feedback learning
- **Validation avanzada**: Reglas de negocio personalizadas por módulo

Este formato establece la base para un sistema completo de refactoring automatizado de código Odoo.

## 📄 Ejemplo de Implementación

### **Lectura del CSV en field_method_renaming**
```python
import pandas as pd

# Leer CSV enhanced
def load_enhanced_csv(csv_path):
    df = pd.read_csv(csv_path)
    
    # Filtrar solo cambios aprobados
    approved = df[df['validation_status'].isin(['approved', 'auto_approved'])]
    
    # Separar primarios y referencias
    primaries = approved[approved['impact_type'] == 'primary']
    references = approved[approved['impact_type'] != 'primary']
    
    return primaries, references

# Procesar por grupos jerárquicos
def process_by_groups(primaries, references):
    for _, primary in primaries.iterrows():
        change_id = primary['change_id']
        
        # Encontrar todas las referencias de este primario
        related_refs = references[references['parent_change_id'] == change_id]
        
        # Procesar grupo completo
        yield primary, related_refs
```

### **Aplicación de Cambios**
```python
def apply_renaming_group(primary, references):
    """Aplica renaming para un grupo primario + referencias"""
    
    old_name = primary['old_name']
    new_name = primary['new_name']
    item_type = primary['item_type']
    
    # 1. Aplicar cambio en declaración (archivo del modelo primario)
    apply_primary_change(primary)
    
    # 2. Aplicar cambios en todas las referencias
    for _, ref in references.iterrows():
        if ref['change_scope'] == 'reference':
            apply_reference_change(ref, old_name, new_name)
        elif ref['change_scope'] == 'call':
            apply_method_call_change(ref, old_name, new_name)
```

Este documento proporciona la base completa para integrar el CSV enhanced con la herramienta de renaming, asegurando compatibilidad y eficiencia en el proceso de refactoring automatizado.