# Sistema de Limpieza y Resecuenciación BDD Odoo v3.2

Sistema automatizado para sanitizar y optimizar bases de datos Odoo mediante procesamiento directo con arquitectura modular.

## 📋 Tabla de Contenidos

- [Requisitos](#requisitos)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Arquitectura](#arquitectura)
- [Seguridad](#seguridad)
- [Logs y Reportes](#logs-y-reportes)
- [Solución de Problemas](#solución-de-problemas)

---

## 🔧 Requisitos

### Software
- Python 3.8+
- PostgreSQL 12+
- psycopg2

### Instalación de dependencias

```bash
# Instalar psycopg2
sudo apt install python3-psycopg2 -y

# Verificar instalación
python3 -c "import psycopg2; print('✓ psycopg2 instalado')"
```

---

## 📁 Estructura del Proyecto

```
desarrolloProyectoR/
│
├── config/
│   └── db_credentials.json          # Credenciales BDD (chmod 600)
│
├── utils/
│   └── acciones_servidor/
│       ├── res.parthner.py          # 30+ archivos con queries SQL
│       ├── account_account.py
│       ├── product.py
│       └── ...
│
├── convertJSON.py                   # Generador de configuración
├── Run.py                           # Script principal de ejecución
│
├── models_config.json               # JSON generado (auto)
│
├── output/
│   ├── statistics/
│   │   ├── processing_report_YYYYMMDD_HHMMSS.json
│   │   └── processing_summary_YYYYMMDD_HHMMSS.csv
│   └── logs/
│       └── execution_YYYYMMDD_HHMMSS.log
|
|
|
|-- Document/
│
└── README.md
```

---

## ⚙️ Configuración

### 1. Configurar credenciales de base de datos

Editar `config/db_credentials.json`:

```json
{
  "host": "localhost",
  "port": 5432,
  "database": "marin_testing",
  "user": "odoo18",
  "password": "tu_password",
  "sslmode": "prefer"
}
```

**⚠️ IMPORTANTE:** Asegurar permisos restrictivos:
```bash
chmod 600 config/db_credentials.json
```

### 2. Generar configuración JSON

```bash
python3 convertJSON.py
```

**Esto generará:** `models_config.json` con:
- Orden de ejecución de modelos
- Reglas CASCADE extraídas
- Reglas de limpieza (DELETE)
- Reglas de nombres
- Configuración de resecuenciación

**Salida esperada:**
```
╔══════════════════════════════════════════════════════════╗
║  convertJSON.py - Generador de Configuración            ║
║  Versión 3.2                                             ║
╚══════════════════════════════════════════════════════════╝

📄 Procesando [01]: account_account.py
📄 Procesando [02]: res.parthner.py
...

✅ JSON generado: models_config.json
   📊 Modelos procesados: 29
   📋 Orden de ejecución: 29 modelos
   📌 CASCADE rules extraídas: 214
   📌 DELETE rules extraídas: 8
```

---

## 🚀 Uso

### Ejecución completa

```bash
python3 Run.py
```

### ⚠️ ANTES de ejecutar:

1. **Hacer backup de la base de datos:**
   ```bash
   pg_dump -h localhost -U odoo18 -d marin_testing > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Verificar credenciales:**
   ```bash
   cat config/db_credentials.json
   ```

3. **Revisar configuración generada:**
   ```bash
   head -50 models_config.json
   ```

### Salida del script

```
╔══════════════════════════════════════════════════════════╗
║  Sistema de Limpieza y Resecuenciación BDD Odoo         ║
║  Versión 3.2                                             ║
╚══════════════════════════════════════════════════════════╝

📋 Cargando credenciales...
🔌 Conectando a base de datos...
✓ Conectado a: marin_testing @ localhost
📄 Cargando configuración de modelos...
📦 Total de modelos a procesar: 29

============================================================
Modelo 1/29: res.company
============================================================

▶ Procesando: res.company (res_company)
  ✓ CASCADE aplicado: 12/12 reglas
  ✓ Resecuenciado: 3 cambios (FKs actualizados por CASCADE)
  ✓ Nombres actualizados: 3 registros (res_company_id)
  ✓ Sin gaps detectados
  ⊘ Sin DELETE rules
  ✓ Completado: 3 registros finales

...

📊 Reportes generados:
   JSON: output/statistics/processing_report_20251003_153045.json
   CSV:  output/statistics/processing_summary_20251003_153045.csv

✅ Proceso completado exitosamente
📋 Log guardado en: output/logs/execution_20251003_153045.log
```

---

## 🏗️ Arquitectura

### Flujo de Ejecución

```
┌─────────────────┐
│  convertJSON.py │  Lee archivos .py → Genera models_config.json
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Run.py      │  Lee JSON → Ejecuta operaciones en BDD
└────────┬────────┘
         │
         ▼
    Para cada modelo (en orden):

    1. CASCADE      → Configurar FKs con ON UPDATE CASCADE
    2. RESECUENCIAR → Cambiar IDs (CASCADE actualiza FKs auto)
    3. NOMBRES      → Actualizar según patrón modelo_{id}
    4. GAPS         → Eliminar huecos en secuencias
    5. DELETE       → Limpieza segura con WHERE
```

### Orden de Operaciones por Modelo

**⚠️ CRÍTICO:** El orden es fundamental para evitar errores de referencia.

1. **CASCADE primero:** Configurar `ON UPDATE CASCADE` en foreign keys
2. **Resecuenciar IDs:** Los FKs se actualizan automáticamente
3. **Actualizar nombres:** Después de tener IDs nuevos
4. **Eliminar gaps:** CASCADE mantiene integridad
5. **DELETE seguro:** Limpieza final con WHERE obligatorio

### Reglas de Nombres

**Estándar general:**
- Formato: `{modelo}_{id}` con `.` → `_`
- Ejemplo: `res.partner` → `res_partner_8590`

**Excepción account.account:**
- NO usa ID en el nombre
- Usa código contable
- SÍ reemplaza `.` por `_`
- Ejemplo: `1.1.01.001` → `1_1_01_001`

---

## 🔒 Seguridad

### 1. DELETE siempre con WHERE

❌ **PROHIBIDO:**
```sql
DELETE FROM res_partner;
```

✅ **CORRECTO:**
```sql
DELETE FROM res_partner
WHERE id IN (SELECT res_id FROM ir_model_data WHERE module = '__export__');
```

### 2. NO usar DISABLE TRIGGER

❌ **NO HACER:**
```sql
ALTER TABLE res_partner DISABLE TRIGGER ALL;
```

✅ **USAR CASCADE:**
```sql
ALTER TABLE res_partner
ADD CONSTRAINT fk_parent
FOREIGN KEY (parent_id) REFERENCES res_partner(id)
ON DELETE CASCADE
ON UPDATE CASCADE;
```

### 3. Transacciones por modelo

- Cada modelo se procesa en su propia transacción
- `COMMIT` si todo OK
- `ROLLBACK` si hay error
- Continúa con el siguiente modelo

### 4. Protección de credenciales

```bash
# Asegurar permisos restrictivos
chmod 600 config/db_credentials.json

# Verificar
ls -la config/db_credentials.json
# Salida esperada: -rw------- (600)
```

---

## 📊 Logs y Reportes

### Archivo JSON detallado

`output/statistics/processing_report_{timestamp}.json`

```json
{
  "execution_info": {
    "timestamp": "2025-10-03T15:30:00",
    "database": "marin_testing",
    "log_file": "output/logs/execution_20251003_153000.log"
  },
  "models_processed": {
    "res.partner": {
      "status": "SUCCESS",
      "records_before": 3761,
      "records_after": 3450,
      "changes": [
        "CASCADE aplicado",
        "IDs resecuenciados desde 8590",
        "Nombres actualizados",
        "45 gaps eliminados",
        "311 registros eliminados"
      ]
    }
  }
}
```

### Archivo CSV resumido

`output/statistics/processing_summary_{timestamp}.csv`

```csv
model,records_before,records_after,status
res.partner,3761,3450,SUCCESS
account.account,856,856,SUCCESS
product.template,900,850,SUCCESS
```

### Logs de ejecución

`output/logs/execution_{timestamp}.log`

- Registro detallado de todas las operaciones
- Errores y advertencias
- Queries SQL ejecutadas
- Tiempos de ejecución

---

##  Solución de Problemas

### Error: "Credenciales no encontradas"

```bash
# Verificar que existe el archivo
ls -la config/db_credentials.json

# Verificar contenido
cat config/db_credentials.json
```

### Error: "No module named 'psycopg2'"

```bash
# Instalar psycopg2
sudo apt install python3-psycopg2 -y

# Verificar
python3 -c "import psycopg2; print('OK')"
```

### Error: "FK constraint violation"

**Causa:** Orden de ejecución incorrecto

**Solución:**
1. Verificar `execution_order` en `models_config.json`
2. Asegurar que tablas padre se procesan primero
3. Re-generar JSON: `python3 convertJSON.py`

### Error: "DELETE sin WHERE no permitido"

**Causa:** Regla de seguridad activada

**Esto es correcto:** El sistema rechaza DELETE sin WHERE por seguridad

**Solución:** Agregar WHERE clause en el archivo `.py` correspondiente

### Transacción fallida en un modelo

**El script continúa:** Hace ROLLBACK y sigue con el siguiente modelo

**Revisar:**
1. Log de ejecución: `output/logs/execution_*.log`
2. Reporte JSON: buscar `"status": "FAILED"`
3. Mensaje de error específico

### Verificar integridad después de ejecución

```sql
-- Verificar res.partner → res.company
SELECT COUNT(*) FROM res_partner p
LEFT JOIN res_company c ON p.company_id = c.id
WHERE p.company_id IS NOT NULL AND c.id IS NULL;

-- Verificar product.template → product.category
SELECT COUNT(*) FROM product_template pt
LEFT JOIN product_category pc ON pt.categ_id = pc.id
WHERE pt.categ_id IS NOT NULL AND pc.id IS NULL;
```

**Resultado esperado:** `0` (cero registros huérfanos)

---

## 📝 Notas Importantes

### Backup OBLIGATORIO

⚠️ **SIEMPRE hacer backup antes de ejecutar:**

```bash
# Backup completo
pg_dump -h localhost -U odoo18 -d marin_testing > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar si es necesario
psql -h localhost -U odoo18 -d marin_testing < backup_20251003_153000.sql
```

### Orden de ejecución NO es arbitrario

El orden en `models_config.json` respeta dependencias FK:
1. `res.company` (primero - base)
2. `res.partner` (depende de company)
3. `product.category` (base de productos)
4. `product.template` (depende de category)
5. ... etc.

### CASCADE automático

- `ON UPDATE CASCADE` actualiza FKs automáticamente
- NO se requiere UPDATE manual de foreign keys
- Reduce queries y mejora performance

### Casos especiales

1. **account.account:** Usa código contable, no ID
2. **Tablas relacionales (_rel):** Se actualizan vía CASCADE
3. **Wizards y temporales:** Se procesan al final

---

## 🔄 Workflow Completo

```bash
# 1. Backup
pg_dump -h localhost -U odoo18 -d marin_testing > backup.sql

# 2. Configurar credenciales
nano config/db_credentials.json
chmod 600 config/db_credentials.json

# 3. Generar configuración
python3 convertJSON.py

# 4. Revisar configuración
head -100 models_config.json

# 5. Ejecutar procesamiento
python3 Run.py

# 6. Revisar resultados
cat output/statistics/processing_summary_*.csv
cat output/logs/execution_*.log

# 7. Verificar integridad (SQL)
# ... queries de verificación ...

# 8. Si hay error, restaurar backup
# psql -h localhost -U odoo18 -d marin_testing < backup.sql
```

 consultar el Plan de Desarrollo v3.2.

**Versión:** 3.2
**Fecha:** 2025-10-03
**Autor:** Josue Gonzalez
