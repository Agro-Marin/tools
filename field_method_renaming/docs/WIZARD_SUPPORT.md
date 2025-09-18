# Soporte para Directorios de Wizards

## Convenciones Soportadas

El módulo `field_method_renaming` soporta ambas convenciones para directorios de wizards:

### 1. Directorio `wizards/` (Plural - Estándar OCA)
```
sale_module/
├── models/
│   └── sale_order.py
├── wizards/                    # ✅ Directorio plural (recomendado)
│   ├── __init__.py
│   ├── sale_wizard.py
│   └── sale_order_wizard.py
└── views/
    └── sale_order_views.xml
```

### 2. Directorio `wizard/` (Singular - Alternativo)
```
sale_module/
├── models/
│   └── sale_order.py
├── wizard/                     # ✅ Directorio singular (alternativo)
│   ├── __init__.py
│   ├── sale_wizard.py
│   └── sale_order_wizard.py
└── views/
    └── sale_order_views.xml
```

## Búsqueda de Archivos

Para un modelo `sale.order`, el FileFinder buscará archivos wizard en:

1. **Directorio wizards (plural)**:
   - `wizards/sale_order.py`
   - `wizards/sale_order_wizard.py`
   - `wizards/sale.py`

2. **Directorio wizard (singular)**:
   - `wizard/sale_order.py`
   - `wizard/sale_order_wizard.py`
   - `wizard/sale.py`

## Detección de Tipos de Archivo

El sistema automáticamente detecta archivos wizard basándose en:

- **Ubicación**: Archivos en directorios `wizards/` o `wizard/`
- **Nomenclatura**: Archivos que contienen la palabra "wizard" en el nombre
- **Contenido**: Análisis del código para detectar modelos TransientModel

## Configuración

En `config/renaming_settings.py`, ambos directorios están configurados:

```python
OCA_DIRECTORIES = {
    'python': ['models', 'controllers', 'wizards', 'wizard'],
    'views': ['views'],
    'data': ['data'],
    'demo': ['demo'],
    'templates': ['templates'],
    'reports': ['reports'],
    'security': ['security']
}
```

## Procesamiento

Los archivos wizard se procesan igual que otros archivos Python:

- **Campos de wizard**: `field_name = fields.Char()` → `new_field = fields.Char()`
- **Métodos de wizard**: `def method_name(self):` → `def new_method(self):`
- **Referencias**: Actualizadas en vistas XML correspondientes

## Ejemplo de Uso

```bash
# Aplicar cambios incluyendo wizards
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /path/to/odoo \
    --file-types python views

# Solo procesar archivos Python (incluye wizards)
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /path/to/odoo \
    --file-types python
```

## Notas

- Se recomienda usar `wizards/` (plural) según convenciones OCA
- El sistema funciona con ambas convenciones para máxima compatibilidad
- La búsqueda fallback encuentra archivos wizard independientemente de la estructura