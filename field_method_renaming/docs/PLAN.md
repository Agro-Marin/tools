# Plan para crear el módulo field_method_renaming

## Objetivo
Crear un módulo complementario que tome el CSV generado por `field_method_detector` y aplique automáticamente los cambios de nombres en el repositorio objetivo, cubriendo todos los tipos de archivos Odoo.

## Estructura del módulo
```
field_method_renaming/
├── __init__.py
├── apply_field_method_changes.py      # Script principal
├── processors/
│   ├── __init__.py
│   ├── python_processor.py           # Procesa archivos .py (modelos, controllers)
│   ├── xml_processor.py              # Procesa todos los tipos de XML
│   └── base_processor.py             # Clase base común
├── config/
│   ├── __init__.py
│   └── renaming_settings.py          # Configuraciones específicas
├── utils/
│   ├── __init__.py
│   ├── csv_reader.py                 # Lee y valida CSV de entrada
│   ├── file_finder.py                # Localiza archivos usando convenciones OCA
│   └── backup_manager.py             # Gestiona respaldos
└── interactive/
    ├── __init__.py
    └── confirmation_ui.py            # UI para confirmación de cambios
```

## Cobertura completa de archivos según convenciones OCA

### FileFinder - Búsqueda exhaustiva
Para un modelo `sale.order`, buscará archivos en este orden:

**Archivos Python:**
- `models/sale_order.py` (modelo principal)
- `models/sale.py` (modelo agrupado)
- `controllers/sale_order.py`
- `controllers/sale.py`
- `wizards/sale_order.py` (wizards principales)
- `wizard/sale_order.py` (directorio wizard singular)

**Archivos XML - Todos los tipos:**
- `views/sale_order_views.xml` (vistas: form, tree, search, etc.)
- `data/sale_order_data.xml` (datos maestros, configuraciones)
- `demo/sale_order_demo.xml` (datos de demostración)
- `templates/sale_order_templates.xml` (templates web/QWeb)
- `security/sale_order_security.xml` (reglas de seguridad)
- `reports/sale_order_reports.xml` (reportes QWeb)

## Procesadores especializados

### PythonProcessor
**Objetivo**: Renombrar en código Python
- **Campos**: `field_name = fields.Char()` → `new_field = fields.Char()`
- **Métodos**: `def method_name(self):` → `def new_method(self):`
- **Referencias en strings**: `'field_name'` → `'new_field'`
- **Computados/Related**: `@api.depends('field_name')` → `@api.depends('new_field')`

### XMLProcessor - Cobertura completa
**Objetivo**: Actualizar referencias XML en todos los tipos de archivos

#### 1. Views (views/*.xml)
- `<field name="old_name">` → `<field name="new_name">`
- `<button name="old_method">` → `<button name="new_method">`
- Atributos: `invisible`, `readonly`, `required` con referencias a campos
- Context y domain con referencias

#### 2. Data (data/*.xml)
- `<field name="field_name">value</field>` → `<field name="new_field">value</field>`
- Referencias en `ir.config_parameter`
- Configuraciones con nombres de campos/métodos

#### 3. Demo (demo/*.xml)
- Datos de demostración con referencias a campos
- `<field name="field_name">demo_value</field>` → `<field name="new_field">demo_value</field>`

#### 4. Templates (templates/*.xml)
- Templates QWeb con `t-field="record.field_name"` → `t-field="record.new_field"`
- Expresiones: `<span t-esc="doc.field_name"/>` → `<span t-esc="doc.new_field"/>`
- Condicionales: `t-if="record.field_name"` → `t-if="record.new_field"`

#### 5. Reports (reports/*.xml)
- Reportes QWeb similares a templates
- Referencias en `<field name="">` dentro de reportes

#### 6. Security (security/*.xml)
- Reglas de acceso a campos específicos
- `<field name="field_id" ref="field_model_field_name"/>` → referencias actualizadas

## Algoritmo de procesamiento

### 1. Fase de descubrimiento
```python
def discover_files(self, module: str, model: str) -> dict[str, list[Path]]:
    """
    Descubre TODOS los archivos que pueden contener referencias
    """
    return {
        'python': [...],  # models, controllers, wizards/wizard
        'views': [...],   # views/*.xml
        'data': [...],    # data/*.xml
        'demo': [...],    # demo/*.xml
        'templates': [...], # templates/*.xml
        'reports': [...],  # reports/*.xml
        'security': [...]  # security/*.xml
    }
```

### 2. Procesamiento por tipo
- **Python**: AST parsing para cambios precisos
- **XML**: ElementTree + regex para diferentes patrones de referencia

### 3. Patrones de búsqueda XML
```python
XML_PATTERNS = {
    'field_reference': [
        r'<field\s+name=["\']({old_name})["\']',  # <field name="field">
        r't-field=["\'][^"\']*\.({old_name})["\']',  # t-field="record.field"
        r't-esc=["\'][^"\']*\.({old_name})["\']',   # t-esc="doc.field"
        r'field_id.*field_[^_]*_({old_name})',      # security references
    ],
    'method_reference': [
        r'<button\s+name=["\']({old_name})["\']',   # <button name="method">
        r'action=["\']({old_name})["\']',           # action="method"
        r't-call=["\']({old_name})["\']',           # t-call="method"
    ]
}
```

## Casos de uso específicos

### Ejemplo 1: Campo quotations_count → count_quotations
**Archivos afectados:**
- `models/crm_team.py`: Definición del campo
- `views/crm_team_views.xml`: `<field name="quotations_count">`
- `data/crm_team_data.xml`: Datos iniciales del campo
- `demo/crm_team_demo.xml`: Datos demo del campo
- `security/ir.model.access.csv`: Permisos de campo (si aplica)

### Ejemplo 2: Método action_quotation_send → action_send_quotation
**Archivos afectados:**
- `models/sale_order.py`: `def action_quotation_send(self):`
- `views/sale_order_views.xml`: `<button name="action_quotation_send">`
- `templates/sale_order_templates.xml`: Referencias en QWeb
- `data/sale_order_data.xml`: Actions o configuraciones

## Características del módulo

### Modo de ejecución
- **--dry-run**: Simular cambios sin aplicar
- **--interactive**: Confirmar cada archivo antes de modificar
- **--backup**: Crear respaldos automáticos (por defecto: activado)
- **--file-types**: Filtrar tipos específicos (python, views, data, demo, templates, etc.)

### Validaciones
- **Pre-cambio**: Verificar sintaxis válida de archivos
- **Post-cambio**: Validar que los cambios no rompan sintaxis
- **Consistencia**: Verificar que todos los archivos relacionados se actualicen

### Reportes
- Log detallado de archivos modificados
- Estadísticas por tipo de archivo
- Lista de archivos respaldados
- Errores y advertencias encontrados