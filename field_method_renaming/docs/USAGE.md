# Guía de Uso - Field Method Renaming Tool

## Prerrequisitos

1. **Archivo CSV**: Generado por `field_method_detector` con la estructura:
   ```csv
   old_name,new_name,module,model
   quotations_count,count_quotations,sale,crm.team
   action_quotation_send,action_send_quotation,sale,sale.order
   ```

2. **Repositorio Odoo**: Con módulos siguiendo convenciones OCA

## Opciones de Línea de Comandos

### Argumentos Obligatorios

```bash
--csv-file PATH           # Archivo CSV con los cambios a aplicar
--repo-path PATH          # Ruta al repositorio Odoo
```

### Argumentos Opcionales

```bash
--interactive, -i         # Modo interactivo (confirmar cada cambio)
--dry-run                 # Simular cambios sin aplicarlos
--backup / --no-backup    # Crear respaldos (por defecto: activado)
--verbose, -v             # Logging detallado
--module MODULE           # Procesar solo un módulo específico
--modules MODULE1 MODULE2 # Procesar múltiples módulos específicos
--file-types TYPE1 TYPE2  # Tipos de archivo a procesar (python, views, data, demo, templates, reports, security)
--output-report FILE      # Archivo para reporte detallado
--confidence-threshold N  # Umbral de confianza (0.0-1.0)
```

## Modos de Operación

### 1. Modo Automático (Por defecto)
Aplica todos los cambios automáticamente con respaldos.

```bash
python apply_field_method_changes.py \
    --csv-file odoo_field_changes_detected.csv \
    --repo-path /path/to/odoo
```

### 2. Modo Interactivo
Permite revisar cada cambio antes de aplicarlo.

```bash
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /path/to/odoo \
    --interactive
```

**Interfaz interactiva:**
```
📝 Cambio propuesto:
   Archivo: models/sale_order.py
   Tipo: Campo
   Cambio: quotations_count → count_quotations
   Modelo: sale.order
   
   Línea 45: quotations_count = fields.Integer('Quotations')
   
¿Aplicar este cambio? [y/N/s/q] (y=sí, N=no, s=saltar archivo, q=salir)
```

### 3. Modo Dry-Run
Simula los cambios sin aplicarlos realmente.

```bash
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /path/to/odoo \
    --dry-run \
    --verbose
```

### 4. Procesamiento Selectivo

#### Por módulo específico:
```bash
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /path/to/odoo \
    --module sale
```

#### Por múltiples módulos:
```bash
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /path/to/odoo \
    --modules sale purchase account
```

#### Por tipos de archivo:
```bash
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /path/to/odoo \
    --file-types python views  # Solo archivos Python (models, controllers, wizards/wizard) y vistas
```

## Ejemplos Prácticos

### Ejemplo 1: Aplicación Básica
```bash
# Aplicar todos los cambios del CSV con respaldos automáticos
python apply_field_method_changes.py \
    --csv-file /path/to/odoo_field_changes_detected.csv \
    --repo-path /home/user/odoo
```

**Salida esperada:**
```
🔍 Procesando archivo CSV: odoo_field_changes_detected.csv
📊 Total de cambios: 25
📂 Módulos afectados: sale, purchase, account

🔄 Procesando módulo 'sale'...
  ✅ models/sale_order.py - 3 cambios aplicados
  ✅ views/sale_order_views.xml - 2 cambios aplicados
  
💾 Respaldos creados en: /home/user/odoo/.backups/20240117_143052/

✅ Proceso completado exitosamente:
   📝 Total cambios aplicados: 25
   📁 Archivos modificados: 12
   🛡️ Respaldos creados: 12
```

### Ejemplo 2: Revisión Interactiva
```bash
# Revisar cada cambio antes de aplicar
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /home/user/odoo \
    --interactive \
    --module sale
```

### Ejemplo 3: Solo Vistas
```bash
# Aplicar cambios solo en archivos de vistas
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /home/user/odoo \
    --file-types views
```

### Ejemplo 4: Análisis sin Modificar
```bash
# Ver qué archivos serían modificados sin aplicar cambios
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /home/user/odoo \
    --dry-run \
    --output-report analysis_report.json
```

## Gestión de Respaldos

### Ubicación de Respaldos
Los respaldos se crean en: `{repo_path}/.backups/{timestamp}/`

### Estructura de Respaldo
```
.backups/
└── 20240117_143052/
    ├── sale/
    │   ├── models/
    │   │   └── sale_order.py.backup
    │   └── views/
    │       └── sale_order_views.xml.backup
    └── backup_manifest.json
```

### Restaurar desde Respaldo
```bash
# El módulo incluye utilidad de restauración
python restore_backup.py --backup-dir /path/to/odoo/.backups/20240117_143052
```

## Validaciones y Verificaciones

### Pre-validaciones
- ✅ Archivo CSV válido y legible
- ✅ Repositorio Odoo accesible
- ✅ Módulos especificados existen
- ✅ Permisos de escritura en archivos

### Post-validaciones
- ✅ Sintaxis Python válida (usando `ast.parse`)
- ✅ XML bien formado (usando `xml.etree.ElementTree`)
- ✅ Todos los cambios aplicados correctamente
- ✅ No se introdujeron errores de sintaxis

## Manejo de Errores

### Errores Comunes y Soluciones

#### 1. Archivo no encontrado
```
❌ Error: No se pudo encontrar models/sale_order.py para el modelo sale.order
```
**Solución**: Verificar que el módulo siga convenciones OCA o usar `--verbose` para ver búsqueda detallada.

#### 2. Sintaxis inválida post-cambio
```
❌ Error: Sintaxis Python inválida en models/sale_order.py después del cambio
```
**Solución**: Revisar el archivo original, el cambio se revierte automáticamente.

#### 3. Permisos insuficientes
```
❌ Error: Sin permisos de escritura en /path/to/file.py
```
**Solución**: Verificar permisos del usuario en el repositorio.

### Logs de Error
Los errores se registran en: `field_method_renaming.log`

## Configuración Avanzada

### Variables de Entorno
```bash
export FIELD_RENAMING_BACKUP_DIR=/custom/backup/path
export FIELD_RENAMING_LOG_LEVEL=DEBUG
export FIELD_RENAMING_PARALLEL_JOBS=4
```

### Archivo de Configuración
Crear `config/custom_settings.py`:
```python
CUSTOM_FILE_PATTERNS = {
    'python': ['*.py'],
    'xml': ['*.xml'],
    'custom': ['*.yml', '*.yaml']  # Patrones adicionales
}

BACKUP_RETENTION_DAYS = 30  # Días para mantener respaldos
```

## Integración con CI/CD

### Pipeline Example
```yaml
# .github/workflows/field-renaming.yml
- name: Apply Field Renamings
  run: |
    python field_method_renaming/apply_field_method_changes.py \
      --csv-file changes.csv \
      --repo-path . \
      --no-backup \
      --file-types python views
```