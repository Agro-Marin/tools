# Field Method Renaming Tool

## Descripción General

El módulo `field_method_renaming` es una herramienta complementaria a `field_method_detector` que aplica automáticamente los cambios de nombres de campos y métodos detectados en repositorios Odoo.

## Características Principales

- **Aplicación automática de cambios**: Procesa archivos CSV con cambios detectados
- **Cobertura completa**: Modifica archivos Python (modelos, controllers) y XML (vistas, data, demo, templates, reports, security)
- **Convenciones OCA**: Sigue las convenciones de naming de la OCA para localizar archivos
- **Respaldos automáticos**: Crea copias de seguridad antes de modificar archivos
- **Validación**: Verifica sintaxis y consistencia post-cambios
- **Modo interactivo**: Permite revisar cambios antes de aplicarlos

## Estructura del Módulo

```
field_method_renaming/
├── __init__.py
├── apply_field_method_changes.py      # Script principal
├── docs/                              # Documentación
│   ├── README.md                     # Este archivo
│   ├── USAGE.md                      # Guía de uso
│   ├── ARCHITECTURE.md               # Arquitectura técnica
│   └── EXAMPLES.md                   # Ejemplos de uso
├── processors/
│   ├── __init__.py
│   ├── python_processor.py           # Procesa archivos .py
│   ├── xml_processor.py              # Procesa archivos .xml
│   └── base_processor.py             # Clase base común
├── config/
│   ├── __init__.py
│   └── renaming_settings.py          # Configuraciones
├── utils/
│   ├── __init__.py
│   ├── csv_reader.py                 # Lee CSV de entrada
│   ├── file_finder.py                # Localiza archivos (OCA)
│   └── backup_manager.py             # Gestiona respaldos
└── interactive/
    ├── __init__.py
    └── confirmation_ui.py            # UI para confirmación
```

## Instalación y Uso Rápido

### Requisitos
- Python 3.8+
- Repositorio Odoo con módulos siguiendo convenciones OCA

### Uso Básico
```bash
# Aplicar cambios desde CSV
python apply_field_method_changes.py --csv-file odoo_field_changes_detected.csv --repo-path /path/to/odoo

# Modo interactivo (revisar cada cambio)
python apply_field_method_changes.py --csv-file changes.csv --repo-path /path/to/odoo --interactive

# Solo simular cambios (dry-run)
python apply_field_method_changes.py --csv-file changes.csv --repo-path /path/to/odoo --dry-run
```

## Tipos de Cambios Soportados

### Archivos Python
- **Modelos y Wizards**: Archivos en `models/`, `controllers/`, `wizards/`, `wizard/`
- **Campos**: `field_name = fields.Char()` → `new_field = fields.Char()`
- **Métodos**: `def method_name(self):` → `def new_method(self):`
- **Referencias**: Strings con nombres de campos/métodos
- **Decoradores**: `@api.depends('field_name')` → `@api.depends('new_field')`

### Archivos XML
- **Vistas**: `<field name="old_name">` → `<field name="new_name">`
- **Botones**: `<button name="old_method">` → `<button name="new_method">`
- **Data/Demo**: Referencias en datos maestros y demostración
- **Templates**: `t-field="record.field_name"` → `t-field="record.new_field"`
- **Reports**: Referencias en reportes QWeb
- **Security**: Reglas de acceso a campos

## Convenciones OCA Soportadas

Para un modelo `sale.order`, busca archivos en:

**Python:**
- `models/sale_order.py`
- `controllers/sale_order.py`
- `wizards/sale_order.py`
- `wizard/sale_order.py`

**XML:**
- `views/sale_order_views.xml`
- `data/sale_order_data.xml`
- `demo/sale_order_demo.xml`
- `templates/sale_order_templates.xml`
- `reports/sale_order_reports.xml`
- `security/sale_order_security.xml`

## Ejemplo de CSV de Entrada

```csv
old_name,new_name,module,model
quotations_count,count_quotations,sale,crm.team
action_quotation_send,action_send_quotation,sale,sale.order
validity_date,date_validity,sale,sale.order
```

## Seguridad y Respaldos

- **Respaldos automáticos**: Crea copias con timestamp antes de modificar
- **Validación de sintaxis**: Verifica que los archivos modificados mantengan sintaxis válida
- **Modo dry-run**: Permite simular cambios sin aplicarlos
- **Logs detallados**: Registra todos los cambios aplicados

## Documentación Adicional

- [Guía de Uso Detallada](USAGE.md)
- [Arquitectura Técnica](ARCHITECTURE.md)
- [Ejemplos Prácticos](EXAMPLES.md)

## Contribuciones

Este módulo sigue las convenciones de desarrollo de AgroMarin y es compatible con las prácticas de la OCA.