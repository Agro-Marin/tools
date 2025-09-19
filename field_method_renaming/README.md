# Field Method Renaming Tool

[![OCA](https://img.shields.io/badge/OCA-Compatible-green.svg)](https://odoo-community.org/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

## Descripción

La herramienta **Field Method Renaming** es una utilidad para aplicar automáticamente cambios de nombres de campos y métodos en repositorios Odoo. Está diseñada para trabajar en conjunto con [`field_method_detector`](../field_method_detector/) y sigue las convenciones de la Odoo Community Association (OCA).

### Características Principales

- 🔄 **Renombramiento automático** de campos y métodos en archivos Python y XML
- 🎯 **Preservación de formato** - mantiene intacta la estructura y estilo original de los archivos
- 🛡️ **Respaldos automáticos** con timestamp antes de modificar archivos
- 🔍 **Validación de sintaxis** post-modificación
- 🎮 **Modo interactivo** para revisar cambios antes de aplicarlos
- 🔧 **Compatible con convenciones OCA** para estructura de módulos

## Instalación

### Requisitos

- Python 3.8 o superior
- Repositorio Odoo siguiendo convenciones OCA
- Archivo CSV con cambios detectados (generado por `field_method_detector`)

### Configuración

```bash
# Clonar el repositorio de herramientas
git clone <repository-url>
cd agromarin-tools/field_method_renaming

# No requiere instalación adicional - usa librerías estándar de Python
```

## Uso Básico

### Comando Principal

```bash
python apply_field_method_changes.py --csv-file <archivo_csv> --repo-path <ruta_odoo> [opciones]
```

### Ejemplos de Uso

```bash
# Aplicar todos los cambios automáticamente
python apply_field_method_changes.py \
    --csv-file odoo_field_changes_detected.csv \
    --repo-path /home/user/odoo-project

# Modo interactivo para revisar cada cambio
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /home/user/odoo-project \
    --interactive

# Simulación sin aplicar cambios (dry-run)
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /home/user/odoo-project \
    --dry-run

# Aplicar solo a módulos específicos
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /home/user/odoo-project \
    --modules sale purchase stock
```

### Opciones Disponibles

| Opción | Descripción |
|--------|-------------|
| `--csv-file` | Archivo CSV con los cambios a aplicar (requerido) |
| `--repo-path` | Ruta al repositorio Odoo (requerido) |
| `--interactive` | Modo interactivo para confirmar cada cambio |
| `--dry-run` | Simular cambios sin modificar archivos |
| `--modules` | Lista de módulos específicos a procesar |
| `--backup-dir` | Directorio personalizado para respaldos |
| `--output-report` | Generar reporte detallado en JSON |
| `--verbose` | Logging detallado para debugging |

## Formato del Archivo CSV

El archivo CSV debe tener el siguiente formato:

```csv
old_name,new_name,item_type,module,model
quotations_count,count_quotations,field,sale,crm.team
action_quotation_send,action_send_quotation,method,sale,sale.order
validity_date,date_validity,field,sale,sale.order
```

### Columnas

- **old_name**: Nombre original del campo/método
- **new_name**: Nuevo nombre del campo/método  
- **item_type**: Tipo de elemento (`field` o `method`)
- **module**: Nombre del módulo Odoo
- **model**: Modelo donde se encuentra el elemento

## Tipos de Archivos Soportados

### Archivos Python (.py)

Procesa archivos en las siguientes ubicaciones siguiendo convenciones OCA:

- `models/` - Modelos de datos
- `wizards/`, `wizard/` - Asistentes
- `controllers/` - Controladores web
- `tests/` - Pruebas unitarias

**Patrones de renombramiento:**

```python
# Campos
old_field = fields.Char()  →  new_field = fields.Char()

# Métodos  
def old_method(self):      →  def new_method(self):

# Referencias en strings
'old_field'                →  'new_field'

# Decoradores
@api.depends('old_field')  →  @api.depends('new_field')
```

### Archivos XML (.xml)

Procesa archivos en las siguientes ubicaciones:

- `views/` - Vistas de usuario
- `data/` - Datos maestros
- `demo/` - Datos de demostración
- `templates/` - Plantillas QWeb
- `reports/` - Reportes
- `security/` - Reglas de seguridad

**Patrones de renombramiento:**

```xml
<!-- Campos en vistas -->
<field name="old_field"/>  →  <field name="new_field"/>

<!-- Métodos en botones -->
<button name="old_method"/> →  <button name="new_method"/>

<!-- Acciones -->
action="old_method"        →  action="new_method"
```

## Convenciones OCA Soportadas

Para un modelo `sale.order` en el módulo `sale`, la herramienta busca archivos en:

### Archivos Python
- `models/sale_order.py`
- `controllers/sale_order.py` 
- `wizards/sale_order.py` o `wizard/sale_order.py`

### Archivos XML
- `views/sale_order_views.xml`
- `data/sale_order_data.xml`
- `demo/sale_order_demo.xml`
- `templates/sale_order_templates.xml`
- `reports/sale_order_reports.xml`
- `security/sale_order_security.xml`

## Preservación de Formato

La herramienta utiliza **reemplazos de texto quirúrgicos** que preservan:

- ✅ Indentación original
- ✅ Saltos de línea y espaciado
- ✅ Comentarios y documentación
- ✅ Orden de atributos XML
- ✅ Estilo de codificación manual

**Antes:**
```xml
<field name="old_field" 
       required="True"
       help="Campo personalizado"/>
```

**Después:**
```xml
<field name="new_field" 
       required="True"
       help="Campo personalizado"/>
```

## Seguridad y Respaldos

### Sistema de Respaldos

- **Automático**: Crea respaldos antes de cada modificación
- **Timestamp**: `archivo.py.backup_20231201_143022`
- **Directorio personalizable**: `--backup-dir /path/to/backups`
- **Compresión**: Respaldos comprimidos para ahorrar espacio

### Validación

- **Sintaxis Python**: Verifica que el código Python sea válido
- **Sintaxis XML**: Valida estructura XML post-modificación
- **Rollback automático**: Restaura desde respaldo si falla la validación

## Estructura del Proyecto

```
field_method_renaming/
├── apply_field_method_changes.py      # Script principal
├── README.md                          # Este archivo
├── docs/                              # Documentación adicional
│   ├── ARCHITECTURE.md               # Arquitectura técnica
│   ├── EXAMPLES.md                   # Ejemplos detallados
│   └── USAGE.md                      # Guía de uso avanzada
├── processors/                       # Procesadores de archivos
│   ├── base_processor.py             # Clase base
│   ├── python_processor.py           # Procesador Python
│   └── xml_processor.py              # Procesador XML
├── utils/                            # Utilidades
│   ├── csv_reader.py                 # Lector de CSV
│   ├── file_finder.py                # Localizador de archivos
│   └── backup_manager.py             # Gestor de respaldos
├── config/                           # Configuración
│   └── renaming_settings.py          # Configuraciones
└── interactive/                      # Modo interactivo
    └── confirmation_ui.py            # Interfaz de confirmación
```

## Integración con field_method_detector

```bash
# 1. Detectar cambios con field_method_detector
cd ../field_method_detector
python detect_field_method_changes.py \
    --json-file modified_modules.json \
    --repo-path /path/to/odoo \
    --interactive

# 2. Aplicar cambios con field_method_renaming  
cd ../field_method_renaming
python apply_field_method_changes.py \
    --csv-file ../field_method_detector/odoo_field_changes_detected.csv \
    --repo-path /path/to/odoo \
    --interactive
```

## Casos de Uso

### 1. Migración de Versiones Odoo

```bash
# Aplicar cambios de naming de v15 a v16
python apply_field_method_changes.py \
    --csv-file odoo_v15_to_v16_changes.csv \
    --repo-path /path/to/odoo-v16 \
    --backup-dir ./migration-backups
```

### 2. Adopción de Convenciones OCA

```bash
# Renombrar campos para seguir convenciones OCA
python apply_field_method_changes.py \
    --csv-file oca_naming_changes.csv \
    --repo-path /path/to/custom-addons \
    --interactive
```

### 3. Refactoring de Módulos

```bash
# Aplicar cambios solo a módulos específicos
python apply_field_method_changes.py \
    --csv-file refactoring_changes.csv \
    --repo-path /path/to/odoo \
    --modules sale purchase stock \
    --verbose
```

## Solución de Problemas

### Errores Comunes

**Error: "No changes found in CSV file"**
- Verificar que el archivo CSV existe y tiene el formato correcto
- Asegurar que las columnas required estén presentes

**Error: "Repository path not found"**
- Verificar que la ruta al repositorio Odoo sea correcta
- Asegurar que el directorio contiene módulos de Odoo

**Error: "Syntax validation failed"**
- Los archivos modificados tienen errores de sintaxis
- Usar `--dry-run` para ver qué cambios se aplicarían
- Revisar los logs detallados con `--verbose`

### Debugging

```bash
# Ejecutar con logging detallado
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /path/to/odoo \
    --verbose \
    --dry-run
```

## Contribución

### Directrices de Desarrollo

1. **Seguir PEP 8** para código Python
2. **Documentar funciones** con docstrings
3. **Agregar tests** para nueva funcionalidad
4. **Mantener compatibilidad** con convenciones OCA

### Reportar Issues

Para reportar bugs o solicitar funcionalidades:

1. Crear un issue en el repositorio del proyecto
2. Incluir ejemplo de CSV problemático
3. Proporcionar logs de error completos
4. Especificar versión de Python y Odoo

## Licencia

Este proyecto está licenciado bajo LGPL-3 - ver el archivo [LICENSE](LICENSE) para detalles.

## Soporte

- **Documentación**: Ver archivos en `/docs/`
- **Issues**: Crear issue en el repositorio del proyecto
- **Contribuciones**: Pull requests bienvenidos

---

Desarrollado siguiendo las mejores prácticas de la **Odoo Community Association (OCA)**.