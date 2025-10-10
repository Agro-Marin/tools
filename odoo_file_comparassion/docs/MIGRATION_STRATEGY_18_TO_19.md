# Estrategia de Migración Odoo 18.2-marin → 19.0-marin

## Contexto

Este documento describe la estrategia para migrar desde Odoo 18.2-marin a 19.0-marin, considerando que:

- Tenemos ~30 módulos modificados en el core, siendo 6 críticos: purchase, sale, stock, purchase_stock, sale_stock, product
- Las modificaciones incluyen cambios lógicos (nuevos flujos, validaciones) y cambios de nomenclatura (renombres de campos/métodos)
- Enterprise también tiene renombres de campos/métodos
- Los módulos add-ons dependen de las modificaciones del core
- No tenemos trazabilidad completa de los cambios más allá del código

---

## 📊 Diagrama de Flujo del Proceso de Migración

### Vista General del Proceso

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MIGRACIÓN ODOO 18.2 → 19.0                          │
│                              (8-10 semanas)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: INVENTARIO Y DOCUMENTACIÓN (2-3 semanas)                           │
│                                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐             │
│  │  Extraer     │      │   Igualar    │      │  Analizar    │             │
│  │  Código      │  →   │ Nomenclatura │  →   │    Diff      │             │
│  │ 18.2 vs -marin│     │ con Renaming │      │   con IA     │             │
│  └──────────────┘      └──────────────┘      └──────────────┘             │
│         │                      │                      │                     │
│         │                      │                      ▼                     │
│         │                      │          ┌──────────────────┐             │
│         │                      │          │  Inventario de   │             │
│         │                      │          │ ~30 Cambios      │             │
│         │                      │          │  Documentados    │             │
│         │                      │          └──────────────────┘             │
│         │                      │                      │                     │
│         │                      ▼                      ▼                     │
│         │          ┌────────────────────────────────────────┐              │
│         │          │  CSV de Renombres                      │              │
│         │          │  (campos y métodos)                    │              │
│         │          └────────────────────────────────────────┘              │
│         │                      │                      │                     │
│         └──────────────────────┴──────────────────────┘                     │
│                                │                                             │
│                                ▼                                             │
│                   ┌──────────────────────┐                                  │
│                   │  Verificar en v19.0  │                                  │
│                   │  ¿Ya está resuelto?  │                                  │
│                   └──────────────────────┘                                  │
│                                │                                             │
│          ┌─────────────────────┼─────────────────────┐                     │
│          ▼                     ▼                     ▼                      │
│    ✅ Resuelto          ⚠️ Adaptar           🔴 Necesario                   │
│     (Descartar)         (Modificar)         (Aplicar)                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: PREPARACIÓN BRANCH 19.0-MARIN (1 semana)                           │
│                                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐             │
│  │ Crear Branch │      │   Aplicar    │      │   Aplicar    │             │
│  │ 19.0-marin   │  →   │  Renombres   │  →   │   Cambios    │             │
│  │ desde 19.0   │      │ (CSV + Tool) │      │   Lógicos    │             │
│  └──────────────┘      └──────────────┘      └──────────────┘             │
│         │                      │                      │                     │
│         │                      │                      ▼                     │
│         │                      │          ┌──────────────────┐             │
│         │                      │          │ Core 19.0-marin  │             │
│         │                      │          │   Funcionando    │             │
│         │                      │          └──────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 3: ADAPTACIÓN ADD-ONS (2-3 semanas)                                   │
│                                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐             │
│  │  Identificar │      │   Aplicar    │      │  Reparar     │             │
│  │ Dependencias │  →   │  Renombres   │  →   │    Tests     │             │
│  │  del Core    │      │  a Add-ons   │      │   (80%+)     │             │
│  └──────────────┘      └──────────────┘      └──────────────┘             │
│         │                      │                      │                     │
│         │                      ▼                      │                     │
│         │          ┌──────────────────┐              │                     │
│         │          │ Adaptar imports  │              │                     │
│         │          │  y manifiestos   │              │                     │
│         │          └──────────────────┘              │                     │
│         └──────────────────┬────────────────────────┘                      │
│                            ▼                                                 │
│                ┌─────────────────────┐                                      │
│                │  Add-ons Migrados   │                                      │
│                │  Tests Funcionando  │                                      │
│                └─────────────────────┘                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 4: QA Y VALIDACIÓN (2 semanas)                                        │
│                                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐             │
│  │  Preparar    │      │   Testing    │      │  Corrección  │             │
│  │ Ambiente QA  │  →   │  Equipo +    │  →   │     de       │             │
│  │ + Migrar BD  │      │   Usuarios   │      │     Bugs     │             │
│  └──────────────┘      └──────────────┘      └──────────────┘             │
│         │                      │                      │                     │
│         ▼                      ▼                      ▼                     │
│  ┌──────────────┐   ┌─────────────────┐   ┌──────────────────┐            │
│  │ BD Clonada   │   │ Semana 1:       │   │ Bugs Críticos    │            │
│  │ + Sanitizada │   │ Técnicos        │   │ Corregidos       │            │
│  └──────────────┘   │                 │   └──────────────────┘            │
│                     │ Semana 2:       │            │                        │
│                     │ 5-7 Usuarios    │            │                        │
│                     └─────────────────┘            │                        │
│                              │                     │                        │
│                              └─────────┬───────────┘                        │
│                                        ▼                                     │
│                              ┌──────────────────┐                           │
│                              │  ¿Aprobado?      │                           │
│                              └──────────────────┘                           │
│                                        │                                     │
│                       ┌────────────────┼────────────────┐                  │
│                       ▼                                  ▼                  │
│                  ✅ SÍ                               ❌ NO                   │
│            (Ir a Fase 5)              (Volver a corrección)                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 5: MIGRACIÓN A PRODUCCIÓN (1 día)                                     │
│                                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐             │
│  │   Backup     │      │   Migrar     │      │  Validar y   │             │
│  │  Completo    │  →   │     BD       │  →   │   Activar    │             │
│  │ BD + Files   │      │ 18.2 → 19.0  │      │   Sistema    │             │
│  └──────────────┘      └──────────────┘      └──────────────┘             │
│         │                      │                      │                     │
│         │                      │                      ▼                     │
│         │                      │          ┌──────────────────┐             │
│         │                      │          │ Tests de humo    │             │
│         │                      │          │ + Verificación   │             │
│         │                      │          └──────────────────┘             │
│         │                      │                      │                     │
│         │                      │         ┌────────────┴────────────┐       │
│         │                      │         ▼                         ▼       │
│         │                      │    ✅ ÉXITO                  ❌ FALLO     │
│         │                      │  (Producción)            (Ejecutar Rollback)│
│         │                      │         │                         │       │
│         │                      │         ▼                         ▼       │
│         │                      │  ┌─────────────┐      ┌──────────────┐   │
│         │                      │  │ Monitoreo   │      │  Restaurar   │   │
│         │                      │  │   48 hs     │      │  BD + Código │   │
│         │                      │  └─────────────┘      │   (~2 horas) │   │
│         │                      │                       └──────────────┘   │
│         └──────────────────────┴────────────┬──────────────┘              │
│                                              │                              │
│                                              ▼                              │
│                                   ┌────────────────────┐                   │
│                                   │ Sistema Operacional│                   │
│                                   │   en Producción    │                   │
│                                   └────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Diagrama de Decisiones Críticas

```
                    ┌─────────────────────────┐
                    │  ¿Cambio resuelto       │
                    │  en Odoo 19.0?          │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
        ✅ Resuelto       ⚠️ Adaptar        🔴 Necesario
              │                 │                 │
              ▼                 ▼                 ▼
        [Descartar]    [Modificar código]  [Aplicar tal cual]
              │                 │                 │
              └─────────────────┴─────────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │  Tests en QA            │
                    └───────────┬─────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
              ✅ Pasan                 ❌ Fallan
                    │                       │
                    ▼                       ▼
            [Ir a Producción]      [Corregir bugs]
                    │                       │
                    │                       └──► [Volver a QA]
                    │
                    ▼
        ┌─────────────────────────┐
        │  Migración Producción   │
        └───────────┬─────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
  ✅ Exitosa              ❌ Falla
        │                       │
        ▼                       ▼
  [Monitoreo]           [ROLLBACK]
                              │
                              ▼
                    ┌──────────────────┐
                    │ Restaurar v18.2  │
                    │   (~2 horas)     │
                    └──────────────────┘
```

### Flujo de Herramientas

```
┌──────────────────────────────────────────────────────────────────┐
│                   HERRAMIENTAS DEL PROYECTO                      │
└──────────────────────────────────────────────────────────────────┘

Fase 1: Documentación
┌────────────┐    ┌────────────────┐    ┌────────────┐
│   Código   │ → │ field_method_  │ → │    CSV     │
│ 18.2-marin │   │   renaming     │   │  Renombres │
└────────────┘   └────────────────┘   └────────────┘
      │                                      │
      ▼                                      │
┌────────────┐    ┌────────────────┐       │
│  Código    │ → │ code_ordering  │ →      │
│   18.2     │   │                │        │
└────────────┘   └────────────────┘        │
      │                  │                  │
      └──────────┬───────┘                 │
                 ▼                          │
         ┌──────────────┐                  │
         │  diff limpio │                  │
         └──────────────┘                  │
                 │                          │
                 ▼                          │
         ┌──────────────┐                  │
         │  Análisis IA │                  │
         └──────────────┘                  │
                 │                          │
                 ▼                          │
         ┌──────────────┐                  │
         │  Inventario  │                  │
         │   Cambios    │                  │
         └──────────────┘                  │
                                            │
Fase 2-3: Aplicación                       │
                                            │
┌────────────┐    ┌────────────────┐      │
│  Código    │ ← │ field_method_  │ ←────┘
│   19.0     │   │   renaming     │
└────────────┘   └────────────────┘
      │
      ▼
┌────────────┐
│  19.0-marin│
└────────────┘
```

### Timeline Visual

```
Semana →  1   2   3   4   5   6   7   8   9   10  11
          │═══════════│═══│═══════════│═══════│══│
          │  FASE 1   │ 2 │  FASE 3   │ FASE 4│5 │
          │Inventario │Prep│  Add-ons  │  QA   │P │
          │           │   │           │       │r │
          │           │   │           │       │o │
          │           │   │           │       │d │
          └───────────┴───┴───────────┴───────┴──┘

Hitos:
  Semana 3  ✓ Inventario completo
  Semana 4  ✓ Core 19.0-marin listo
  Semana 7  ✓ Add-ons migrados + Tests 80%
  Semana 9  ✓ QA aprobado
  Semana 10 ✓ Go-live producción
  Semana 11 ✓ Estabilización
```

### Recursos por Fase

```
PERSONAS ASIGNADAS POR FASE

Fase 1 (Inventario)         Fase 2 (Core)           Fase 3 (Add-ons)
┌────────────┐              ┌────────────┐          ┌────────────┐
│ Dev 1: Doc │              │ Dev 1: Core│          │ Dev 1: Mod1│
│ Dev 2: Doc │              │ Dev 2: Core│          │ Dev 2: Mod2│
│            │              │            │          │ Dev 3: Mod3│
│            │              │            │          │ Dev 4: Tests│
└────────────┘              └────────────┘          └────────────┘

Fase 4 (QA)                 Fase 5 (Prod)
┌────────────┐              ┌────────────┐
│ Dev 1-4    │              │ Dev 1-4    │
│ QA Lead    │              │ DevOps     │
│ 5-7 Users  │              │ DBA        │
└────────────┘              └────────────┘
```

---

## Fase 1: Inventario y Documentación de Cambios (2-3 semanas)

### 1.1 Documentar cambios lógicos del core (6 módulos críticos)

**Módulos prioritarios:** purchase, sale, stock, purchase_stock, sale_stock, product

**Proceso por módulo:**

1. Extraer código vanilla 18.2 → directorio `18.2/`
2. Extraer código customizado 18.2-marin → directorio `18.2-marin/`
3. Aplicar herramienta de renaming para igualar nomenclatura
4. Aplicar herramienta de reordenamiento
5. Generar diff limpio y documentar cambios lógicos con IA
6. **Categorizar cada cambio:**
   - **Bug fix:** Corrección de bugs de Odoo
   - **Business logic:** Lógica específica del negocio
   - **Enhancement:** Mejora de buenas prácticas

**Herramientas:**
- `field_method_renaming/` para igualar nomenclatura
- `code_ordering/` para ordenamiento de código
- Modelo de IA para análisis de diff

**Resultado:** Inventario completo de ~30 cambios lógicos documentados

### 1.2 Verificar cambios en Odoo 19.0 vanilla

Para cada cambio documentado:

1. Comparar con el código equivalente en Odoo 19.0 vanilla
2. Clasificar:
   - ✅ **Ya resuelto en v19:** Descartar (el bug ya fue corregido por Odoo)
   - ⚠️ **Requiere adaptación:** Modificar para v19 (la estructura cambió)
   - 🔴 **Aún necesario:** Aplicar tal cual (el cambio sigue siendo válido)
   - ❓ **Dudoso:** Validar con equipo/usuarios (no está claro si sigue siendo necesario)

**Proceso:**
```bash
# Para cada módulo
git checkout 19.0  # vanilla
# Revisar si el cambio ya existe o si el contexto cambió
# Documentar decisión en el inventario
```

### 1.3 Documentar renombres de campos/métodos

1. Generar CSV con todos los renombres aplicados en 18.2-marin
2. Formato del CSV debe ser compatible con `field_method_renaming/`
3. Este CSV será input para aplicar los mismos renombres en 19.0

**Estructura del CSV:**
```csv
change_id,old_name,new_name,item_type,module,model,change_scope,impact_type,context,confidence
1,scheduled_date,date_planned,field,stock,stock.picking,declaration,primary,,0.900
2,delay_alert_date,date_delay_alert,field,stock,stock.move,declaration,primary,,0.900
```

---

## Fase 2: Preparación del Branch 19.0-marin (1 semana)

### 2.1 Crear branch base

```bash
# Partir desde vanilla 19.0
git checkout 19.0
git checkout -b 19.0-marin
```

### 2.2 Aplicar cambios de nomenclatura

**Para Core:**
```bash
cd /path/to/odoo/core
python /path/to/field_method_renaming/apply_field_method_changes.py \
  --csv-file renombres_18_2_marin.csv \
  --repo-path . \
  --verbose
```

**Para Enterprise:**
```bash
cd /path/to/odoo/enterprise
python /path/to/field_method_renaming/apply_field_method_changes.py \
  --csv-file renombres_18_2_marin_enterprise.csv \
  --repo-path . \
  --verbose
```

**Verificación:**
```bash
# Buscar referencias a nombres antiguos
grep -r "scheduled_date" addons/stock/
grep -r "delay_alert_date" addons/stock/
```

### 2.3 Aplicar cambios lógicos validados

Para cada cambio del inventario marcado como 🔴 **Aún necesario** o ⚠️ **Requiere adaptación**:

1. Localizar el archivo correspondiente en 19.0-marin
2. Aplicar el cambio manualmente siguiendo la documentación generada
3. **Importante:** Adaptar a la estructura de v19 (puede haber refactorizaciones)
4. Documentar el cambio aplicado (commit descriptivo)

**Ejemplo de commit:**
```
[MIG][stock] Apply custom cancellation logic from 18.2-marin

In 18.2-marin we added validation to prevent cancellation when:
- Move is in state 'done'
- Move has related production orders

This logic is still needed in 19.0 and has been adapted to the
new structure of _action_cancel() method.

Ref: Inventario de cambios, ID #23
```

---

## Fase 3: Adaptación de Módulos Add-ons (2-3 semanas)

### 3.1 Análisis de dependencias

1. Listar todos los módulos add-ons
2. Identificar cuáles dependen de cambios del core:
   - Usan campos/métodos renombrados
   - Heredan de modelos modificados
   - Dependen de lógica customizada
3. Priorizar por criticidad de negocio

**Herramienta para análisis:**
```bash
cd /path/to/addons
grep -r "scheduled_date" . > dependencies_report.txt
grep -r "delay_alert_date" . >> dependencies_report.txt
# Analizar el reporte
```

### 3.2 Migración automática

```bash
cd /path/to/addons
python /path/to/field_method_renaming/apply_field_method_changes.py \
  --csv-file renombres_18_2_marin.csv \
  --repo-path . \
  --verbose

python /path/to/code_ordering/odoo_reorder.py \
  --repo-path . \
  --verbose
```

### 3.3 Adaptación manual

Por cada módulo add-on:

1. **Actualizar manifiestos:**
   ```python
   # __manifest__.py
   {
       'version': '19.0.1.0.0',  # Actualizar versión
       'depends': ['base', 'stock'],  # Verificar dependencias
   }
   ```

2. **Revisar imports:**
   ```python
   # Odoo 19 puede haber movido módulos
   from odoo import fields, models, api
   from odoo.tools import float_compare  # Verificar si cambió
   ```

3. **Verificar campos/métodos deprecados:**
   - Revisar changelog de Odoo 19.0
   - Buscar warnings en logs de Odoo

### 3.4 Reparar tests

1. **Aplicar renombres a tests:**
   ```bash
   cd /path/to/addons/module_name/tests
   python /path/to/field_method_renaming/apply_field_method_changes.py \
     --csv-file renombres_18_2_marin.csv \
     --repo-path . \
     --verbose
   ```

2. **Ejecutar tests:**
   ```bash
   odoo -d test_db -i module_name --test-enable --stop-after-init
   ```

3. **Corregir fallos:**
   - Actualizar assertions
   - Corregir referencias a campos/métodos
   - Adaptar datos de prueba a v19

**Meta:** Al menos 80% de tests pasando antes de QA

---

## Fase 4: Ambiente de QA y Validación (2 semanas)

### 4.1 Preparar ambiente QA

1. **Clonar base de datos de producción:**
   ```bash
   # Sanitizar datos sensibles
   pg_dump production_db | psql qa_db
   # Ejecutar script de sanitización si existe
   ```

2. **Migrar data de v18 a v19:**
   ```bash
   # Usar script oficial de Odoo
   odoo -d qa_db -u all --stop-after-init
   ```

3. **Desplegar código 19.0-marin:**
   ```bash
   git clone -b 19.0-marin /path/to/odoo/core
   git clone -b 19.0-marin /path/to/odoo/enterprise
   git clone -b 19.0-marin /path/to/odoo/addons
   ```

### 4.2 Testing funcional

**Semana 1: Equipo técnico (3-4 personas)**

Validar flujos críticos:

1. **Flujo de ventas:**
   - Crear cotización
   - Confirmar orden
   - **Validar nuevo estado de facturación** (cambio crítico de 18.2-marin)
   - Crear factura
   - Registrar pago

2. **Flujo de compras:**
   - Crear solicitud de cotización
   - Confirmar orden
   - **Validar validaciones de cancelación** (cambio crítico de 18.2-marin)
   - Recibir productos
   - Crear factura de proveedor

3. **Operaciones de inventario:**
   - Movimientos internos
   - Ajustes de inventario
   - Trazabilidad de lotes/series

**Semana 2: Usuarios finales (5-7 usuarios clave)**

1. Seleccionar usuarios representativos de cada área
2. Proporcionar guía de casos de uso a validar
3. Documentar bugs/regresiones encontradas
4. Priorizar por severidad:
   - **Crítico:** Bloquea operación principal
   - **Alto:** Afecta flujo importante
   - **Medio:** Afecta funcionalidad secundaria
   - **Bajo:** Cosmético o edge case

### 4.3 Corrección de bugs encontrados

1. Crear ticket/issue por cada bug
2. Priorizar por severidad
3. Aplicar hotfixes en 19.0-marin
4. Re-validar en QA
5. Repetir hasta que no haya bugs críticos/altos

---

## Fase 5: Migración a Producción (1 día)

### 5.1 Pre-migración (día anterior)

1. **Backup completo:**
   ```bash
   # Base de datos
   pg_dump production_db > backup_pre_migration_$(date +%Y%m%d).sql

   # Filestore
   tar -czf filestore_backup_$(date +%Y%m%d).tar.gz /path/to/filestore
   ```

2. **Comunicar downtime:**
   - Email a usuarios
   - Mensaje en sistema
   - Duración estimada: 4-8 horas

3. **Preparar rollback plan:**
   - Script para restaurar BD
   - Procedimiento para volver a código 18.2-marin
   - Contactos de emergencia

### 5.2 Migración (ventana de 1 día)

**Checklist:**

- [ ] **T-0h: Modo mantenimiento ON**
  ```bash
  # En configuración de Odoo
  # O usando proxy/load balancer
  ```

- [ ] **T+0.5h: Backup final**
  ```bash
  pg_dump production_db > backup_final_pre_migration_$(date +%Y%m%d_%H%M).sql
  ```

- [ ] **T+1h: Ejecutar script de migración**
  ```bash
  odoo -d production_db -u all --stop-after-init --log-level=debug
  ```

- [ ] **T+4h: Actualizar código**
  ```bash
  cd /path/to/odoo
  git checkout 19.0-marin
  systemctl restart odoo
  ```

- [ ] **T+5h: Tests de humo**
  - Login funcional
  - Módulos instalados correctamente
  - Datos visibles

- [ ] **T+6h: Validación manual flujos críticos**
  - Crear venta de prueba
  - Crear compra de prueba
  - Validar inventario

- [ ] **T+7h: Modo mantenimiento OFF**

- [ ] **T+8h: Comunicar finalización**

### 5.3 Monitoreo post-migración

**Primeras 48 horas:**

1. **Monitoreo técnico:**
   - Revisar logs cada 2 horas
   - Monitorear performance (CPU, RAM, queries lentas)
   - Verificar que no hay errores en background jobs

2. **Soporte a usuarios:**
   - Canal directo (Slack/WhatsApp) para reporte de issues
   - Equipo técnico disponible para hotfixes
   - Documentar todos los reportes

3. **Métricas a vigilar:**
   - Tiempo de respuesta de páginas
   - Cantidad de errores 500
   - Quejas de usuarios
   - Transacciones completadas vs día anterior

---

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Cambios lógicos incompatibles con v19 | Media | Alto | Validación exhaustiva en Fase 1.2 + QA con usuarios |
| Tests rotos bloquean QA | Alta | Medio | Reparar tests críticos en Fase 3.4 antes de QA |
| Data migration falla | Baja | Crítico | Múltiples ensayos en QA + backup + rollback plan |
| Usuarios encuentran bugs críticos en producción | Media | Alto | QA con usuarios finales + monitoreo 48h + hotfix rápido |
| Downtime se extiende más de 1 día | Baja | Alto | Ensayo completo en QA + rollback plan probado |
| Pérdida de funcionalidad no documentada | Media | Medio | Inventario exhaustivo Fase 1 + validación usuarios |

---

## Cronograma Estimado

**Total: 8-10 semanas**

| Fase | Duración | Responsables |
|------|----------|--------------|
| Fase 1: Inventario y Documentación | 2-3 semanas | 2 personas |
| Fase 2: Preparación 19.0-marin | 1 semana | 2 personas |
| Fase 3: Adaptación Add-ons | 2-3 semanas | 3-4 personas |
| Fase 4: QA y Validación | 2 semanas | 3-4 personas + 5-7 usuarios |
| Fase 5: Migración Producción | 1 día + 1 semana buffer | Todo el equipo |

**Hitos críticos:**
- Semana 3: Inventario completo de cambios
- Semana 5: Branch 19.0-marin con cambios aplicados
- Semana 8: Add-ons migrados y tests al 80%
- Semana 10: QA completo sin bugs críticos
- Semana 11: Go-live en producción

---

## Entregables Clave

1. ✅ **Documento de inventario de cambios lógicos**
   - Formato: Markdown con tabla de cambios
   - Ubicación: `odoo_file_comparassion/inventory_changes.md`
   - Contenido: ~30 cambios categorizados y documentados

2. ✅ **CSV de renombres de campos/métodos**
   - Formato: CSV compatible con `field_method_renaming/`
   - Ubicación: `odoo_file_comparassion/renombres_18_2_marin.csv`
   - Contenido: Todos los renombres aplicados en core y enterprise

3. ✅ **Branch 19.0-marin funcional**
   - Core, Enterprise y Add-ons migrados
   - Cambios lógicos aplicados
   - Renombres aplicados

4. ✅ **Suite de tests reparada (80%+)**
   - Tests críticos funcionando
   - Documentación de tests pendientes

5. ✅ **Plan de rollback documentado**
   - Procedimiento paso a paso
   - Scripts automatizados
   - Tiempo estimado de rollback: 2 horas

6. ✅ **Guía de validación para usuarios QA**
   - Casos de uso a validar
   - Criterios de aceptación
   - Formulario de reporte de bugs

---

## Checklist General de Migración

### Pre-migración
- [ ] Inventario de cambios completo
- [ ] CSV de renombres generado
- [ ] Branch 19.0-marin creado
- [ ] Cambios de nomenclatura aplicados
- [ ] Cambios lógicos aplicados
- [ ] Add-ons migrados
- [ ] Tests críticos reparados (80%+)
- [ ] Ambiente QA configurado
- [ ] QA técnico completado
- [ ] QA con usuarios completado
- [ ] Bugs críticos corregidos
- [ ] Plan de rollback probado
- [ ] Backup strategy definida
- [ ] Comunicación a usuarios enviada

### Migración
- [ ] Backup pre-migración completo
- [ ] Modo mantenimiento activado
- [ ] Script de migración ejecutado
- [ ] Código actualizado a 19.0-marin
- [ ] Tests de humo ejecutados
- [ ] Validación manual de flujos críticos
- [ ] Modo mantenimiento desactivado
- [ ] Comunicación de finalización enviada

### Post-migración
- [ ] Monitoreo 48h completado
- [ ] Sin errores críticos reportados
- [ ] Performance aceptable
- [ ] Usuarios operando normalmente
- [ ] Documentación actualizada
- [ ] Retrospectiva del equipo realizada

---

## Contactos y Responsables

| Rol | Responsable | Contacto |
|-----|-------------|----------|
| Project Lead | [Nombre] | [Email/Phone] |
| Dev Lead | [Nombre] | [Email/Phone] |
| QA Lead | [Nombre] | [Email/Phone] |
| DevOps | [Nombre] | [Email/Phone] |
| Support | [Nombre] | [Email/Phone] |

---

## Referencias

- **Herramientas:**
  - `field_method_renaming/`: Aplicar renombres de campos/métodos
  - `code_ordering/`: Ordenamiento de código para facilitar diff
  - `odoo_file_comparassion/`: Documentación de cambios

- **Documentación Odoo:**
  - [Odoo 19.0 Release Notes](https://www.odoo.com/odoo-19-release-notes)
  - [Odoo Upgrade Guide](https://www.odoo.com/documentation/19.0/developer/reference/upgrades.html)

- **Branches Git:**
  - Vanilla 18.2: `saas-18.2`
  - Custom 18.2: `saas-18.2-marin`
  - Vanilla 19.0: `19.0`
  - Custom 19.0: `19.0-marin`

---

**Última actualización:** 2025-10-07
**Versión:** 1.0
**Autor:** Equipo de Desarrollo AgroMarin
