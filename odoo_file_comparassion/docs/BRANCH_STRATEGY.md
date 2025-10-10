# Estrategia de Branches - AgroMarin Odoo

## 🎯 Objetivo

Definir una estructura de branches clara que permita:
- Desarrollo paralelo sin conflictos
- Testing adecuado antes de producción
- Rollback rápido si algo falla
- Trazabilidad completa de cambios
- Facilitar futuras migraciones

---

## 📊 Situación Actual vs Propuesta

### Estado Actual

```
odoo-core/
├── 19.0           # Vanilla Odoo (nunca se toca)
└── 19.0-marin     # Producción (push directo, caótico)

odoo-addons/
└── [sin estructura clara]
```

**Problemas:**
- ❌ Push directo a producción (riesgoso)
- ❌ No hay ambiente de testing/staging
- ❌ Difícil hacer rollback
- ❌ No hay espacio para desarrollo sin afectar producción

### Propuesta Nueva

```
odoo-core/
├── 19.0                    # Vanilla Odoo (NUNCA tocar)
├── 19.0-marin-develop      # Integración de features (NUEVO)
├── 19.0-marin-staging      # Pre-producción (NUEVO)
└── 19.0-marin-production   # Producción (renombrar 19.0-marin)

odoo-addons/
├── 19.0-develop           # Integración de features
├── 19.0-staging           # Pre-producción
└── 19.0-production        # Producción

feature branches (temporales):
├── feature/TASK-XXX-descripcion
├── bugfix/TASK-XXX-descripcion
└── hotfix/TASK-XXX-descripcion
```

**Beneficios:**
- ✅ Desarrollo aislado de producción
- ✅ Testing en ambiente staging antes de producción
- ✅ Rollback fácil (revertir merge)
- ✅ Historial limpio y trazable

---

## 🌳 Estructura Detallada de Branches

### 1. Branch Vanilla: `19.0` (Solo Core)

**Propósito:**
- Mantener copia exacta de Odoo Community vanilla
- Referencia para comparaciones y migraciones
- Base para crear customizaciones

**Características:**
- 🔒 **Protegido:** Solo lectura
- 🔄 **Actualización:** Manual cuando Odoo publica updates
- 👤 **Responsable:** Tech Lead
- 📝 **Commits:** Solo merges desde odoo/odoo upstream

**Flujo de actualización:**

```bash
# Cuando Odoo publica una actualización (ej: 19.0.1.2)
cd odoo-core
git checkout 19.0
git remote add upstream https://github.com/odoo/odoo.git  # Solo primera vez
git fetch upstream
git merge upstream/19.0
git tag vanilla-19.0.1.2  # Tag para referencia
git push origin 19.0
git push origin vanilla-19.0.1.2
```

**⚠️ NUNCA:**
- Hacer commits directos
- Modificar código
- Hacer merge desde otros branches

**✅ SÍ:**
- Pull desde upstream de Odoo
- Crear tags para cada versión de Odoo
- Usar como base de comparación

---

### 2. Branch Develop: `19.0-marin-develop` (Core) / `19.0-develop` (Addons)

**Propósito:**
- **Integración continua** de features en desarrollo
- Ambiente de **desarrollo compartido**
- Base para crear **feature branches**
- Testing **inicial** de integración

**Características:**
- 🔒 **Protegido:** No push directo, solo PRs aprobados
- 🔄 **Actualización:** Múltiple diaria (cada merge de feature)
- 👥 **Usuarios:** Todos los developers
- 🧪 **Testing:** CI automático en cada PR
- 🌍 **Ambiente:** Desarrollo compartido (opcional)

**Flujo típico:**

```
┌─────────────────────────────────────────────────────┐
│           DEVELOP (Integración)                     │
│                                                     │
│  feature-1 ──┐                                     │
│              ├──► Merge ──► CI Tests ──► Deploy Dev│
│  feature-2 ──┤                                     │
│              │                                      │
│  bugfix-1  ──┘                                     │
└─────────────────────────────────────────────────────┘
```

**Reglas:**
- ✅ **Solo acepta PRs** con:
  - 2 aprobaciones mínimo
  - CI pasando (lint + tests)
  - Commits siguiendo convenciones
  - Conflicts resueltos
- ✅ **Merge strategy:** Squash and merge (commits limpios)
- ✅ **Protecciones GitHub:**
  ```yaml
  require_pull_request: true
  required_approvals: 2
  require_code_owner_review: false
  require_status_checks: true
  required_status_checks:
    - lint
    - tests
  require_up_to_date_branch: true
  ```

**Cuándo usar:**
- Base para **crear** feature/bugfix branches
- Target de **merge** de features terminadas
- **No usar directamente** para desarrollar

**Comandos comunes:**

```bash
# Crear feature desde develop
git checkout 19.0-marin-develop  # o 19.0-develop para addons
git pull origin 19.0-marin-develop
git checkout -b feature/TASK-123-nueva-validacion

# Actualizar feature con cambios de develop (si hay conflictos)
git checkout feature/TASK-123-nueva-validacion
git fetch origin
git merge origin/19.0-marin-develop
# Resolver conflictos si hay
git commit -m "Merge develop into feature branch"
git push
```

---

### 3. Branch Staging: `19.0-marin-staging` (Core) / `19.0-staging` (Addons)

**Propósito:**
- **Pre-producción:** Réplica exacta de producción
- **QA exhaustivo:** Testing por usuarios finales
- **Validación final:** Antes de pasar a producción
- **Ambiente seguro:** Para probar sin riesgo

**Características:**
- 🔒 **Protegido:** Solo merges desde develop (aprobado por Tech Lead)
- 🔄 **Actualización:** Semanal o por release
- 👥 **Usuarios:** QA team + usuarios finales
- 🧪 **Testing:** Manual + automatizado
- 🌍 **Ambiente:** Servidor staging (clone de producción)
- 📊 **Data:** Copia sanitizada de producción

**Flujo de promoción:**

```
┌──────────────────────────────────────────────────────┐
│         DEVELOP (Features integradas)                │
└────────────────┬─────────────────────────────────────┘
                 │
                 │ PR semanal (Tech Lead aprueba)
                 ▼
┌──────────────────────────────────────────────────────┐
│         STAGING (Pre-producción)                     │
│                                                      │
│  1. Deploy automático a servidor staging            │
│  2. QA team valida (2-3 días)                       │
│  3. Usuarios finales validan (2-3 días)             │
│  4. Si todo OK → Promoción a production             │
│  5. Si hay bugs → Fix en develop → Re-deploy        │
└──────────────────────────────────────────────────────┘
```

**Reglas:**
- ✅ **Solo acepta merges desde:** develop (no desde features directamente)
- ✅ **Frecuencia:** 1 vez por semana (o cada sprint)
- ✅ **Criterio:** Develop debe estar estable (sin bugs conocidos)
- ✅ **Aprobación:** Tech Lead + QA Lead
- ✅ **Rollback:** Revert merge si QA falla

**Proceso de promoción develop → staging:**

```bash
# 1. Tech Lead verifica que develop está estable
git checkout 19.0-marin-develop
git pull
git log --oneline -10  # Revisar últimos cambios

# 2. Crear PR de develop → staging en GitHub
# Base: 19.0-marin-staging
# Compare: 19.0-marin-develop
# Título: "Weekly release YYYY-MM-DD"
# Descripción: Lista de features/fixes incluidos

# 3. Esperar aprobación de Tech Lead + QA Lead

# 4. Merge (automático o manual)
git checkout 19.0-marin-staging
git pull
git merge 19.0-marin-develop --no-ff  # Keep merge commit
git push origin 19.0-marin-staging

# 5. CI/CD automáticamente deploya a servidor staging

# 6. Notificar a QA team por Slack
```

**Servidor staging:**

- **URL:** https://staging.agromarin.com
- **Base de datos:** Clone de producción (sanitizada)
- **Filestore:** Clone de producción
- **Actualización:** Automática en cada push a staging branch
- **Usuarios:** Solo equipo interno (QA + developers)

**Criterios de aprobación QA:**

- [ ] Todos los casos de uso críticos funcionan
- [ ] No hay errores en logs
- [ ] Performance es aceptable
- [ ] Usuarios finales aprobaron (5-7 usuarios)
- [ ] No hay bugs bloqueantes
- [ ] Documentación actualizada

**Si QA falla:**

```bash
# Opción 1: Revertir merge en staging
git checkout 19.0-marin-staging
git revert -m 1 HEAD  # Revertir último merge
git push

# Opción 2: Fix urgente
# Crear hotfix desde staging
git checkout -b hotfix/TASK-XXX-fix-staging
# Fix
# PR a staging (fast-track)
# Backport a develop
```

---

### 4. Branch Production: `19.0-marin-production` (Core) / `19.0-production` (Addons)

**Propósito:**
- **Producción:** Código que está corriendo en producción
- **Estabilidad máxima:** Solo código probado en staging
- **Fuente de verdad:** Código que sirve a usuarios reales
- **Base para hotfixes:** Si algo falla en producción

**Características:**
- 🔒 **Protegido:** Solo merges desde staging (Tech Lead + DevOps)
- 🔄 **Actualización:** Cada 1-2 semanas (después de QA en staging)
- 👥 **Usuarios:** Usuarios finales en producción
- 🧪 **Testing:** Smoke tests post-deploy
- 🌍 **Ambiente:** Servidor producción
- 📊 **Data:** Data real de clientes

**Flujo de promoción:**

```
┌──────────────────────────────────────────────────────┐
│         STAGING (QA aprobado)                        │
└────────────────┬─────────────────────────────────────┘
                 │
                 │ PR de release (Tech Lead + DevOps)
                 ▼
┌──────────────────────────────────────────────────────┐
│         PRODUCTION                                   │
│                                                      │
│  1. Tag de release (ej: v19.0.5)                    │
│  2. Deploy a producción (ventana de mantenimiento)  │
│  3. Smoke tests automáticos                         │
│  4. Monitoreo 48h                                   │
│  5. Rollback si es necesario                        │
└──────────────────────────────────────────────────────┘
```

**Reglas:**
- ✅ **Solo acepta merges desde:** staging (nunca desde develop o features)
- ✅ **Frecuencia:** Cada 1-2 semanas (o releases planificados)
- ✅ **Criterio:** Staging aprobado por QA + sin bugs críticos
- ✅ **Aprobación:** Tech Lead + DevOps + Stakeholder
- ✅ **Tags:** Cada merge es un tag de versión

**Proceso de promoción staging → production:**

```bash
# ========================================
# DÍA ANTES DEL DEPLOY
# ========================================

# 1. Verificar que staging está estable (mínimo 3 días sin cambios)
# 2. Verificar que QA aprobó
# 3. Comunicar ventana de mantenimiento a usuarios
# 4. Preparar plan de rollback

# ========================================
# DÍA DEL DEPLOY
# ========================================

# 1. Backup completo de producción
ssh producción
cd /opt/odoo
./scripts/backup_full.sh

# 2. Crear PR de staging → production en GitHub
# Base: 19.0-marin-production
# Compare: 19.0-marin-staging
# Título: "Release v19.0.5 - YYYY-MM-DD"
# Descripción: Release notes

# 3. Esperar aprobaciones (Tech Lead + DevOps)

# 4. Activar modo mantenimiento
ssh producción
systemctl stop odoo

# 5. Merge
git checkout 19.0-marin-production
git pull
git merge 19.0-marin-staging --no-ff
git tag -a v19.0.5 -m "Release v19.0.5 - Features: X, Y, Z"
git push origin 19.0-marin-production
git push origin v19.0.5

# 6. Deploy en producción
cd /opt/odoo
git pull
odoo -d production_db -u all --stop-after-init
systemctl start odoo

# 7. Smoke tests
./scripts/smoke_tests.sh

# 8. Desactivar modo mantenimiento

# 9. Monitoreo intensivo 48h
tail -f /var/log/odoo/odoo.log
```

**Versionado (Semantic Versioning adaptado):**

```
vMAJOR.MINOR.PATCH

Ejemplos:
v19.0.1  - Primera release después de migración a 19.0
v19.0.2  - Segunda release (nuevas features)
v19.0.3  - Tercera release
v19.1.0  - Cambio significativo (nueva versión de Odoo upstream)
```

**Protecciones GitHub:**

```yaml
branch: 19.0-marin-production
protection_rules:
  require_pull_request: true
  required_approvals: 2  # Tech Lead + DevOps
  require_code_owner_review: true  # CODEOWNERS file
  require_status_checks: true
  required_status_checks:
    - smoke-tests
  require_up_to_date_branch: true
  enforce_admins: true  # Ni admins pueden saltarse reglas
  allow_force_pushes: false
  allow_deletions: false
```

**Si algo falla en producción (Hotfix):**

Ver sección 5 (Hotfix branches)

---

### 5. Feature/Bugfix/Hotfix Branches (Temporales)

Estos branches son **temporales** y se eliminan después de merge.

#### 5.1 Feature Branches

**Nomenclatura:** `feature/TASK-XXX-descripcion-corta`

**Propósito:**
- Desarrollar **nueva funcionalidad**
- Aislado del resto del equipo
- Se puede experimentar sin afectar a nadie

**Características:**
- ⏱️ **Vida útil:** 1-5 días (máximo 1 semana)
- 🔀 **Origen:** develop
- 🎯 **Destino:** develop (via PR)
- 👤 **Owner:** 1 developer (puede colaborar con otros)
- 🗑️ **Eliminación:** Automática después de merge

**Ciclo de vida:**

```bash
# 1. CREAR (desde develop)
git checkout 19.0-develop
git pull
git checkout -b feature/TASK-123-vip-discount

# 2. DESARROLLAR
# ... código ...
git add .
git commit -m "[ADD][sale] Add VIP discount - TASK-123"

# 3. MANTENER ACTUALIZADO (si develop avanza)
git fetch origin
git merge origin/19.0-develop

# 4. PUSH Y PR
git push origin feature/TASK-123-vip-discount
# Crear PR en GitHub

# 5. MERGE (después de aprobación)
# Squash and merge desde GitHub UI

# 6. DELETE (automático en GitHub)
# Limpiar local:
git checkout 19.0-develop
git pull
git branch -d feature/TASK-123-vip-discount
```

**Reglas:**
- ✅ Máximo **1 semana de vida** (si toma más, dividir en sub-features)
- ✅ Sincronizar con develop **al menos 1 vez al día**
- ✅ Commits frecuentes (no esperar a terminar todo)
- ✅ Push diario (backup)

#### 5.2 Bugfix Branches

**Nomenclatura:** `bugfix/TASK-XXX-descripcion-bug`

**Propósito:**
- Corregir **bugs no críticos** encontrados en develop/staging
- Similar a feature pero para fixes

**Características:**
- ⏱️ **Vida útil:** 1-3 días
- 🔀 **Origen:** develop
- 🎯 **Destino:** develop (via PR)
- 👤 **Owner:** 1 developer
- 🗑️ **Eliminación:** Automática después de merge

**Proceso:** Idéntico a feature branch, solo cambia el prefijo

```bash
git checkout 19.0-develop
git pull
git checkout -b bugfix/TASK-456-stock-calculation
# ... fix ...
git commit -m "[FIX][stock] Fix negative stock calculation - TASK-456"
# PR y merge
```

#### 5.3 Hotfix Branches (Críticos)

**Nomenclatura:** `hotfix/TASK-XXX-descripcion-critica`

**Propósito:**
- Corregir **bugs CRÍTICOS en producción**
- Deploy inmediato sin esperar release normal
- Bypass del proceso normal (excepción)

**Características:**
- ⏱️ **Vida útil:** Horas (máximo 1 día)
- 🔀 **Origen:** **production** (no develop!)
- 🎯 **Destino:** production (PR urgente) + backport a develop/staging
- 👤 **Owner:** Senior/Tech Lead
- 🚨 **Urgencia:** Máxima

**Criterios para hotfix:**

- 🔴 **Sistema caído** (no pueden trabajar)
- 🔴 **Pérdida de dinero** (facturación bloqueada)
- 🔴 **Pérdida de datos** (información crítica)
- 🔴 **Vulnerabilidad de seguridad**

**Proceso de hotfix:**

```bash
# ========================================
# PASO 1: Crear hotfix desde PRODUCTION
# ========================================
git checkout 19.0-marin-production
git pull
git checkout -b hotfix/TASK-789-invoice-crash

# ========================================
# PASO 2: Fix (mínimo cambio posible)
# ========================================
vim addons/account/models/account_move.py
# ... fix crítico ...
git add .
git commit -m "[HOTFIX][account] Fix invoice generation crash

Critical: Invoice crashes when partner has no email
Fix: Add null check before email send

Task: TASK-789
Severity: Critical
Affects: All users
"

# ========================================
# PASO 3: Push y PR URGENTE a production
# ========================================
git push origin hotfix/TASK-789-invoice-crash

# Crear PR:
# Base: 19.0-marin-production
# Compare: hotfix/TASK-789-invoice-crash
# Título: "[HOTFIX] Fix invoice crash - CRITICAL"
# Labels: hotfix, critical, priority-urgent
# Reviewers: Tech Lead + DevOps
# Notificar por Slack/WhatsApp

# ========================================
# PASO 4: Fast-track review (30 min max)
# ========================================
# Tech Lead revisa
# DevOps revisa
# Aprobación acelerada

# ========================================
# PASO 5: Merge y deploy a PRODUCTION
# ========================================
git checkout 19.0-marin-production
git merge hotfix/TASK-789-invoice-crash --no-ff
git tag v19.0.5-hotfix1
git push origin 19.0-marin-production
git push origin v19.0.5-hotfix1

# Deploy inmediato
ssh producción
cd /opt/odoo
git pull
systemctl restart odoo

# Verificar fix
./scripts/smoke_tests.sh

# ========================================
# PASO 6: Backport a staging y develop
# ========================================
git checkout 19.0-marin-staging
git merge hotfix/TASK-789-invoice-crash
git push

git checkout 19.0-marin-develop
git merge hotfix/TASK-789-invoice-crash
git push

# ========================================
# PASO 7: Cleanup
# ========================================
git branch -d hotfix/TASK-789-invoice-crash
git push origin --delete hotfix/TASK-789-invoice-crash

# ========================================
# PASO 8: Post-mortem (siguientes 24h)
# ========================================
# Documentar:
# - Qué pasó
# - Por qué pasó
# - Cómo se arregló
# - Cómo prevenir en el futuro
# - Agregar tests (si no se agregaron en el hotfix)
```

**⚠️ Importante:**
- Hotfix debe ser **mínimo cambio posible** para arreglar el issue
- Tests pueden agregarse después (en siguientes 24h) si es muy urgente
- Siempre hacer backport a develop/staging para mantener sincronización
- Documentar en post-mortem

---

## 📊 Diagrama de Flujo Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VANILLA (19.0)                               │
│                  (Solo lectura, referencia)                         │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ Fork inicial / Comparaciones
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                        DEVELOP                                      │
│              (Integración diaria de features)                       │
│                                                                     │
│  feature-1 ────┐                                                   │
│                ├──► Merge (PR + 2 approvals) ──► CI Tests          │
│  feature-2 ────┤                                                   │
│                │                                                    │
│  bugfix-1  ────┘                                                   │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ Semanal (cuando develop está estable)
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                        STAGING                                      │
│                  (Pre-producción / QA)                              │
│                                                                     │
│  Deploy automático ──► QA Team valida ──► Usuarios validan         │
│                                                                     │
│  ┌──────────────────────────────────────────────────┐              │
│  │ Si QA falla: Revert o fix urgente                │              │
│  └──────────────────────────────────────────────────┘              │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ Cada 1-2 semanas (después QA OK)
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                       PRODUCTION                                    │
│                   (Usuarios reales)                                 │
│                                                                     │
│  Tag release ──► Deploy ──► Smoke tests ──► Monitoreo 48h          │
│                                                                     │
│  ┌──────────────────────────────────────────────────┐              │
│  │ Si falla: Hotfix desde production                │              │
│  └──────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘

                            ▲
                            │
                            │ Solo en emergencia
                            │
                   ┌────────┴────────┐
                   │   HOTFIX        │
                   │  (desde prod)   │
                   └─────────────────┘
```

---

## 🔄 Flujos Comunes

### Flujo 1: Feature Normal (90% de los casos)

```
Developer:
1. Crear tarea en Odoo (TASK-123)
2. git checkout 19.0-develop && git pull
3. git checkout -b feature/TASK-123-nueva-validacion
4. Desarrollar + commits + tests
5. git push origin feature/TASK-123-nueva-validacion
6. Crear PR a develop
7. Esperar 2 aprobaciones
8. Merge (squash) - automático delete branch

Cada semana (Tech Lead):
9. Merge develop → staging
10. QA valida en staging
11. Si OK: Merge staging → production (release)
```

### Flujo 2: Bugfix en Staging (encontrado por QA)

```
QA encuentra bug en staging:
1. Reportar en Odoo (TASK-456 - Bug en cálculo)
2. Developer: git checkout 19.0-develop && git pull
3. git checkout -b bugfix/TASK-456-calculo-incorrecto
4. Fix + tests + commit
5. PR a develop
6. Merge a develop
7. Merge develop → staging (actualizar staging)
8. QA re-valida
```

### Flujo 3: Hotfix Crítico en Producción

```
Bug crítico en producción (sistema caído):
1. Crear tarea urgente (TASK-789)
2. git checkout 19.0-marin-production
3. git checkout -b hotfix/TASK-789-critical-crash
4. Fix mínimo (sin tests si es muy urgente)
5. PR urgente a production
6. Fast-track review (30 min)
7. Merge a production + tag (v19.0.X-hotfix1)
8. Deploy inmediato
9. Verificar que funciona
10. Backport a staging y develop
11. Agregar tests en siguiente PR
```

### Flujo 4: Actualización de Odoo Vanilla (ej: 19.0.1.2)

```
Odoo publica nueva versión:
1. git checkout 19.0
2. git fetch upstream (odoo/odoo)
3. git merge upstream/19.0
4. git tag vanilla-19.0.1.2
5. git push origin 19.0
6. Analizar diff: git diff vanilla-19.0.1.1..vanilla-19.0.1.2
7. Verificar si afecta customizaciones (revisar CORE_CUSTOMIZATIONS.md)
8. Si hay conflictos con customizaciones:
   - Crear tarea (TASK-XXX)
   - Adaptar customizaciones en develop
   - Merge a develop → staging → production
```

---

## 🚀 Migración desde Estructura Actual

### Plan de Transición (Hacer ahora, antes de la migración a v19)

#### Paso 1: Renombrar branches existentes

```bash
# En repositorio odoo-core
cd odoo-core

# Renombrar 19.0-marin → 19.0-marin-production
git branch -m 19.0-marin 19.0-marin-production
git push origin 19.0-marin-production
git push origin --delete 19.0-marin

# Actualizar branch por defecto en GitHub a 19.0-marin-production
```

#### Paso 2: Crear nuevos branches

```bash
# Crear develop desde production
git checkout 19.0-marin-production
git pull
git checkout -b 19.0-marin-develop
git push origin 19.0-marin-develop

# Crear staging desde production
git checkout 19.0-marin-production
git checkout -b 19.0-marin-staging
git push origin 19.0-marin-staging
```

#### Paso 3: Proteger branches en GitHub

```
GitHub → Settings → Branches → Add rule

Para 19.0-marin-production:
✅ Require pull request before merging
✅ Require approvals (2)
✅ Require status checks to pass
✅ Require branches to be up to date
✅ Do not allow bypassing
❌ Allow force pushes
❌ Allow deletions

Repetir para:
- 19.0-marin-staging
- 19.0-marin-develop
```

#### Paso 4: Actualizar CI/CD

```yaml
# .github/workflows/odoo-ci.yml
on:
  pull_request:
    branches:
      - 19.0-marin-develop   # CI en PRs a develop
      - 19.0-marin-staging   # CI en PRs a staging
      - 19.0-marin-production # CI en PRs a production
  push:
    branches:
      - 19.0-marin-develop   # Deploy a dev después de merge
      - 19.0-marin-staging   # Deploy a staging después de merge
```

#### Paso 5: Comunicar al equipo

**Mensaje a enviar:**

```
📢 Nueva estructura de branches - Efectivo HOY

Cambios:
1. ❌ PROHIBIDO push directo a production
2. ✅ Desarrollo en feature branches → PR a develop
3. ✅ Testing en staging antes de producción

Nuevo flujo:
feature/bugfix → develop → staging → production

Documentación completa:
https://github.com/empresa/odoo-core/BRANCH_STRATEGY.md

Workshop: Viernes 10am (obligatorio)
```

#### Paso 6: Primer release con nuevo flujo

```bash
# Semana 1: Desarrollar features normalmente en develop
# Semana 2: Promover a staging y validar
# Semana 3: Promover a production con nuevo proceso
```

---

## 📋 Configuración de GitHub

### CODEOWNERS File

**Archivo: `.github/CODEOWNERS`**

```
# Tech Lead debe aprobar TODOS los PRs a production
**/19.0-marin-production @tech-lead

# Tech Lead debe aprobar customizaciones del CORE
**/addons/stock/models/** @tech-lead
**/addons/sale/models/** @tech-lead
**/addons/purchase/models/** @tech-lead

# DevOps debe aprobar cambios en CI/CD
.github/workflows/** @devops-lead

# Cualquier senior puede aprobar en develop
**/19.0-marin-develop @senior-dev-1 @senior-dev-2 @tech-lead
```

### Branch Protection Settings (Completo)

**19.0-marin-production:**

```yaml
branch_protection_rules:
  pattern: "19.0-marin-production"

  pull_request_rules:
    required: true
    required_approving_review_count: 2
    require_code_owner_reviews: true
    dismiss_stale_reviews: true
    require_review_from_code_owners: true

  status_checks:
    required: true
    strict: true  # Require branches to be up to date
    contexts:
      - "lint"
      - "security-scan"
      - "tests"
      - "smoke-tests"

  restrictions:
    users: []
    teams: ["tech-leads", "devops"]
    apps: []

  enforce_admins: true
  required_linear_history: true  # No merge commits de features
  allow_force_pushes: false
  allow_deletions: false
  required_conversation_resolution: true  # Resolver todos los comments
```

**19.0-marin-staging:**

```yaml
branch_protection_rules:
  pattern: "19.0-marin-staging"

  pull_request_rules:
    required: true
    required_approving_review_count: 2
    require_code_owner_reviews: false  # Más flexible que production
    dismiss_stale_reviews: false

  status_checks:
    required: true
    strict: true
    contexts:
      - "lint"
      - "tests"

  restrictions:
    users: []
    teams: ["developers"]  # Todos los devs pueden aprobar
    apps: []

  enforce_admins: false  # Admins pueden saltarse si es necesario
  required_linear_history: true
  allow_force_pushes: false
  allow_deletions: false
```

**19.0-marin-develop:**

```yaml
branch_protection_rules:
  pattern: "19.0-marin-develop"

  pull_request_rules:
    required: true
    required_approving_review_count: 2
    require_code_owner_reviews: false
    dismiss_stale_reviews: false

  status_checks:
    required: true
    strict: false  # No requiere estar actualizado (más flexible)
    contexts:
      - "lint"
      - "tests"

  restrictions:
    users: []
    teams: ["developers"]
    apps: []

  enforce_admins: false
  required_linear_history: false  # Permitir merge commits
  allow_force_pushes: false
  allow_deletions: false
```

---

## 🎯 Resumen Ejecutivo

### Para Developers

```
Tu día a día:

1. Recibir tarea → Crear feature branch desde develop
2. Desarrollar → Commits frecuentes
3. Push → PR a develop
4. Code review → 2 aprobaciones
5. Merge → Branch se borra automáticamente
6. Repeat

Nunca más:
❌ Push directo a producción
❌ Merge sin PR
❌ Commits sin tests
```

### Para Tech Lead

```
Tu rol:

Diario:
- Revisar PRs críticos
- Aprobar merges a develop

Semanal:
- Merge develop → staging
- Verificar QA en staging
- Merge staging → production (si QA OK)
- Crear tag de release

Emergencias:
- Aprobar hotfixes
- Coordinar rollbacks si es necesario
```

### Para QA Team

```
Tu ambiente:

Staging (https://staging.agromarin.com):
- Se actualiza 1 vez por semana
- Tienes 2-3 días para validar
- Si encuentras bugs, reportar en Odoo
- Aprobar cuando todo funcione

Nunca:
❌ Validar en producción directamente
❌ Aprobar sin testing completo
```

---

## 📊 Métricas de Éxito

Después de implementar esta estructura (3 meses):

| Métrica | Antes | Meta |
|---------|-------|------|
| Bugs en producción | 15/mes | <5/mes |
| Rollbacks en producción | 20% | <5% |
| Tiempo de deploy | Ad-hoc | Predecible (semanal) |
| Tiempo de hotfix | 4+ horas | <2 horas |
| Features bloqueadas | Frecuente | Raro |
| Confianza del equipo | Baja | Alta |

---

## ❓ FAQ

### ¿Por qué no Git Flow estándar (con release branches)?

Git Flow original tiene release branches separados. En nuestro caso, **staging branch cumple el rol de release branch**. Simplificamos porque:
- Equipo pequeño (3-4 devs)
- Releases frecuentes (semanal)
- No necesitamos múltiples releases en paralelo

### ¿Qué pasa si develop y staging divergen mucho?

No debería pasar si seguimos el flujo:
- develop → staging (merge semanal)
- staging → production (merge semanal)

Si pasa, es señal de que no estamos promoviendo a tiempo.

### ¿Puedo saltarme staging para un fix urgente?

Solo con hotfix desde production. **Nunca** mergear develop directamente a production.

### ¿Cómo manejo dependencias entre features?

Si feature B depende de feature A:
1. Mergear feature A a develop primero
2. Crear feature B desde develop actualizado
3. O crear feature B como sub-branch de feature A (avanzado)

### ¿Qué pasa si staging tiene bugs que no se pueden fijar en 1 semana?

Opciones:
1. Revertir el merge en staging
2. Posponer promoción a production
3. Fix urgente en develop → re-merge a staging

**Nunca** pasar a production con bugs conocidos.

---

**Última actualización:** 2025-10-07
**Versión:** 1.0
**Autor:** Tech Lead
**Próxima revisión:** Trimestral
