# Estrategia de Branches - Versión Simplificada

## 🎯 Tu Situación Actual vs Propuesta

### ACTUAL (2 branches)

```
odoo-core/
├── 19.0          # Vanilla Odoo (referencia)
└── 19.0-marin    # ⚠️ Producción + Desarrollo mezclados
```

**Problema:** Desarrollo y producción en el mismo branch = riesgoso

---

### OPCIÓN 1: Mínima (3 branches) - RECOMENDADA PARA EMPEZAR

```
odoo-core/
├── 19.0                      # Vanilla Odoo (solo lectura)
├── 19.0-marin-develop        # NUEVO - Trabajo diario
└── 19.0-marin-production     # Renombrar de 19.0-marin
```

**Flujo simple:**
```
Developer → feature branch → PR → develop → production
                                      ↓           ↑
                                    (Tests)  (Release semanal)
```

**Ventajas:**
- ✅ Desarrollo aislado de producción
- ✅ Fácil de entender
- ✅ Permite PRs y code review
- ✅ Producción protegida

**Cuando usar:**
- Estás empezando con control de cambios
- Equipo pequeño (3-4 personas)
- Quieres simplicidad

---

### OPCIÓN 2: Completa (4 branches) - IDEAL A LARGO PLAZO

```
odoo-core/
├── 19.0                      # Vanilla Odoo (solo lectura)
├── 19.0-marin-develop        # Trabajo diario
├── 19.0-marin-staging        # NUEVO - Testing/QA
└── 19.0-marin-production     # Producción
```

**Flujo completo:**
```
Developer → feature → PR → develop → staging (QA) → production
                              ↓          ↓              ↑
                          (Tests)   (Users test)  (Release)
```

**Ventajas adicionales:**
- ✅ Todo lo de Opción 1 +
- ✅ QA en ambiente seguro
- ✅ Usuarios pueden probar antes de producción
- ✅ Detectar bugs antes

**Cuando usar:**
- Después de 1-2 meses con Opción 1
- Quieres máxima seguridad
- Tienes servidor staging disponible

---

## 🚀 Recomendación por Fase

### FASE 1 (Primeros 2 meses): Opción 1 (3 branches)

**Estructura:**
```
├── 19.0                     # Vanilla
├── 19.0-marin-develop       # Development
└── 19.0-marin-production    # Production
```

**Workflow:**
1. Developer crea `feature/TASK-XXX` desde develop
2. Hace PR a develop
3. 2 aprobaciones → merge
4. Cada semana: Tech Lead merge develop → production

**Setup rápido (1 día):**
```bash
# Renombrar branch actual
git branch -m 19.0-marin 19.0-marin-production
git push origin 19.0-marin-production

# Crear develop
git checkout -b 19.0-marin-develop
git push origin 19.0-marin-develop

# Proteger branches en GitHub
# Settings → Branches → Add rule
```

---

### FASE 2 (Después de 2 meses): Opción 2 (4 branches)

Cuando ya dominas Opción 1, agregar staging:

```bash
# Crear staging desde production
git checkout 19.0-marin-production
git checkout -b 19.0-marin-staging
git push origin 19.0-marin-staging
```

**Nuevo workflow:**
1. Developer: feature → develop (igual que antes)
2. Semanal: develop → staging
3. QA valida en staging (2-3 días)
4. Si OK: staging → production

---

## 📊 Comparación Visual

### Workflow ACTUAL (caótico)

```
┌────────────────────────────────────────┐
│         19.0-marin                     │
│  (Producción + Desarrollo mezclados)   │
│                                        │
│  Dev1 push ──┐                        │
│              ├──► ⚠️ Afecta producción│
│  Dev2 push ──┤      inmediatamente    │
│              │                         │
│  Dev3 push ──┘                        │
└────────────────────────────────────────┘
     ↓
❌ Bugs en producción
❌ Conflictos constantes
❌ No hay testing
```

### Workflow OPCIÓN 1 (seguro)

```
┌────────────────────────────────────────┐
│        19.0-marin-develop              │
│     (Desarrollo seguro)                │
│                                        │
│  feature-1 ──┐                        │
│              ├──► PR + Review         │
│  feature-2 ──┤      ↓                 │
│              │   Merge               │
└──────────────┴────────┬───────────────┘
                        │
                        │ Semanal
                        ▼
┌────────────────────────────────────────┐
│      19.0-marin-production             │
│         (Producción protegida)         │
└────────────────────────────────────────┘
     ↓
✅ Desarrollo aislado
✅ Code review
✅ Menos bugs
```

### Workflow OPCIÓN 2 (ideal)

```
┌────────────────────────────────────────┐
│        19.0-marin-develop              │
│          (Desarrollo)                  │
└──────────────────┬─────────────────────┘
                   │ Semanal
                   ▼
┌────────────────────────────────────────┐
│        19.0-marin-staging              │
│      (Testing/QA 2-3 días)            │
└──────────────────┬─────────────────────┘
                   │ Si QA OK
                   ▼
┌────────────────────────────────────────┐
│      19.0-marin-production             │
│      (Usuarios reales)                 │
└────────────────────────────────────────┘
     ↓
✅ Todo lo anterior +
✅ Bugs detectados antes
✅ QA apropiado
```

---

## 🛠️ Setup Paso a Paso (OPCIÓN 1)

### Paso 1: Preparación (5 min)

**Comunicar al equipo:**
```
📢 IMPORTANTE: Cambio en estructura de branches

A partir de hoy:
- 19.0-marin → se renombra a 19.0-marin-production
- Nuevo branch: 19.0-marin-develop
- ⛔ NO push directo a production
- ✅ Desarrollo en feature branches → PR a develop

Workshop: Viernes 10am (obligatorio)
```

### Paso 2: Crear branches (10 min)

```bash
cd /path/to/odoo-core

# 1. Renombrar production
git branch -m 19.0-marin 19.0-marin-production
git push origin 19.0-marin-production
git push origin --delete 19.0-marin

# 2. Crear develop
git checkout 19.0-marin-production
git checkout -b 19.0-marin-develop
git push origin 19.0-marin-develop

# 3. Verificar
git branch -a
# Debe mostrar:
#   19.0
#   19.0-marin-develop
#   19.0-marin-production
```

### Paso 3: Proteger branches en GitHub (15 min)

**GitHub → Settings → Branches → Add rule**

**Para `19.0-marin-production`:**
```
Branch name pattern: 19.0-marin-production

✅ Require a pull request before merging
   ✅ Require approvals: 2
   ✅ Dismiss stale pull request approvals

✅ Require status checks to pass before merging
   ✅ Require branches to be up to date before merging

✅ Do not allow bypassing the above settings

❌ Allow force pushes
❌ Allow deletions
```

**Para `19.0-marin-develop`:**
```
Branch name pattern: 19.0-marin-develop

✅ Require a pull request before merging
   ✅ Require approvals: 2

✅ Require status checks to pass before merging

❌ Allow force pushes
❌ Allow deletions
```

### Paso 4: Actualizar README (5 min)

```markdown
# Odoo Core - AgroMarin

## Branches

- `19.0` - Vanilla Odoo (referencia)
- `19.0-marin-develop` - Development (base para features)
- `19.0-marin-production` - Production (código en producción)

## Workflow

1. Crear feature: `git checkout -b feature/TASK-XXX-descripcion`
2. Desarrollar y commit
3. Push: `git push origin feature/TASK-XXX-descripcion`
4. Crear PR a `19.0-marin-develop`
5. Esperar 2 aprobaciones
6. Merge automático

Documentación completa: BRANCH_STRATEGY.md
```

### Paso 5: Primera feature con nuevo workflow (30 min)

**Práctica con el equipo:**

```bash
# Developer 1
git checkout 19.0-marin-develop
git pull
git checkout -b feature/TASK-TEST-001-practica

# Hacer cambio simple
echo "# Test" >> README.md
git add README.md
git commit -m "[TEST] Practice feature branch workflow

This is a test commit to practice the new workflow.

Task: TASK-TEST-001
"

# Push y PR
git push origin feature/TASK-TEST-001-practica
# Ir a GitHub → Create Pull Request

# Developer 2 y 3: Revisar y aprobar

# Developer 1: Merge cuando esté aprobado
```

---

## 📋 Checklist de Implementación

### Semana 1: Setup

```
□ Día 1: Comunicar cambio al equipo
□ Día 1: Renombrar y crear branches
□ Día 1: Proteger branches en GitHub
□ Día 2: Workshop (2 horas)
  □ Explicar nueva estructura
  □ Demo: crear feature branch
  □ Demo: hacer PR
  □ Práctica: cada dev hace 1 PR
□ Día 3-5: Primera semana con nuevo workflow
```

### Semana 2-4: Refinamiento

```
□ Ajustar proceso según feedback
□ Configurar CI/CD (si no existe)
□ Documentar casos edge (hotfixes, etc.)
□ Primer release con nuevo proceso
```

### Semana 5-8: Evaluación

```
□ Medir métricas:
  □ Bugs en producción
  □ Tiempo de merge
  □ Satisfacción del equipo
□ Decidir si agregar staging (Opción 2)
```

---

## 🤔 Preguntas Frecuentes

### "¿Necesito 3 o 4 branches?"

**Respuesta:**
- **Empieza con 3** (develop + production)
- Después de 1-2 meses, evalúa si necesitas staging
- Si tienes < 5 developers → 3 branches suficiente
- Si tienes servidor staging disponible → 4 branches mejor

### "¿Qué pasa con el branch 19.0-marin actual?"

**Respuesta:**
- Se renombra a `19.0-marin-production`
- Todo sigue funcionando igual
- Solo cambia el nombre
- GitHub mantiene todo el historial

### "¿Todos los developers necesitan aprender esto?"

**Respuesta:**
- Sí, pero es simple:
  - Antes: push a 19.0-marin
  - Ahora: PR a 19.0-marin-develop
- Solo 1 paso adicional (PR)
- Después de 3-4 PRs se vuelve automático

### "¿Cuánto tiempo toma implementar?"

**Respuesta:**
- Setup técnico: 30 minutos
- Workshop: 2 horas
- Adaptación del equipo: 1-2 semanas
- Total efectivo: 2 semanas

### "¿Puedo volver atrás si no funciona?"

**Respuesta:**
- Sí, solo renombrar branches de vuelta
- Pero después de 2 semanas, no querrás volver
- Los beneficios son obvios rápidamente

---

## 🎯 Decisión Rápida

### Empieza con OPCIÓN 1 si:
- ✅ Equipo pequeño (3-4 devs)
- ✅ Primera vez con control de cambios
- ✅ Quieres simplicidad
- ✅ No tienes servidor staging listo

### Salta a OPCIÓN 2 si:
- ✅ Ya tienes servidor staging
- ✅ Equipo tiene experiencia con Git Flow
- ✅ Quieres máxima seguridad desde día 1
- ✅ Tienes tiempo para setup completo

---

## 📊 Estructura Final Recomendada

Para tu caso específico, **recomiendo OPCIÓN 1** para empezar:

```
odoo-core/
├── 19.0                      # Vanilla (ya existe)
├── 19.0-marin-develop        # CREAR AHORA
└── 19.0-marin-production     # RENOMBRAR 19.0-marin

odoo-enterprise/
├── 19.0                      # Vanilla (ya existe)
├── 19.0-marin-develop        # CREAR AHORA
└── 19.0-marin-production     # RENOMBRAR 19.0-marin

odoo-addons/ (custom)
├── 19.0-develop              # CREAR AHORA
└── 19.0-production           # Renombrar main/master
```

**Workflow diario:**
```
1. feature/TASK-XXX → PR → develop (diario)
2. develop → production (semanal, viernes)
```

**En 2 meses, si funciona bien, agregar staging:**
```
1. feature/TASK-XXX → PR → develop (diario)
2. develop → staging (semanal, lunes)
3. QA valida staging (martes-miércoles)
4. staging → production (jueves, si QA OK)
```

---

## 🚀 Próximos Pasos Inmediatos

### Esta Semana:

**Lunes:**
```bash
# 30 minutos
./scripts/setup_new_branches.sh  # Crear script siguiente
```

**Martes:**
```
# 2 horas
Workshop con equipo:
- Presentar nueva estructura (30 min)
- Demo en vivo (30 min)
- Práctica (1 hora)
```

**Miércoles-Viernes:**
```
# Trabajo normal
Usar nuevo workflow:
- Cada feature = PR
- Minimum 2 reviews
- Merge a develop
```

**Siguiente Lunes:**
```
# Release
Merge develop → production
Deploy en producción
```

---

## 📝 Script de Setup Automatizado

**Archivo: `scripts/setup_new_branches.sh`**

```bash
#!/bin/bash
# Setup de nueva estructura de branches
# Uso: bash scripts/setup_new_branches.sh

set -e

echo "🚀 Configurando nueva estructura de branches..."

# 1. Verificar que estamos en odoo-core
if [ ! -d ".git" ]; then
    echo "❌ Error: Ejecutar desde raíz del repositorio"
    exit 1
fi

# 2. Verificar que existe 19.0-marin
if ! git show-ref --verify --quiet refs/heads/19.0-marin; then
    echo "❌ Error: Branch 19.0-marin no existe"
    exit 1
fi

# 3. Confirmar con usuario
echo ""
echo "Este script hará lo siguiente:"
echo "1. Renombrar 19.0-marin → 19.0-marin-production"
echo "2. Crear 19.0-marin-develop desde production"
echo ""
read -p "¿Continuar? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelado"
    exit 1
fi

# 4. Hacer backup (por si acaso)
echo "📦 Creando backup de branches..."
git branch backup-19.0-marin-$(date +%Y%m%d)

# 5. Renombrar 19.0-marin → 19.0-marin-production
echo "🔄 Renombrando 19.0-marin → 19.0-marin-production..."
git branch -m 19.0-marin 19.0-marin-production
git push origin 19.0-marin-production
git push origin --delete 19.0-marin

# 6. Crear 19.0-marin-develop
echo "✨ Creando 19.0-marin-develop..."
git checkout 19.0-marin-production
git checkout -b 19.0-marin-develop
git push origin 19.0-marin-develop

# 7. Verificar
echo ""
echo "✅ Setup completo!"
echo ""
echo "Branches actuales:"
git branch -a | grep "19.0"
echo ""
echo "Próximos pasos:"
echo "1. Ir a GitHub → Settings → Branches → Proteger branches"
echo "2. Actualizar README.md con nueva estructura"
echo "3. Comunicar cambio al equipo"
echo "4. Hacer workshop de capacitación"
```

**Ejecutar:**
```bash
chmod +x scripts/setup_new_branches.sh
bash scripts/setup_new_branches.sh
```

---

**¿Te ayudo con alguno de estos puntos?**
1. ✅ Crear el script de setup
2. ✅ Template de comunicación al equipo
3. ✅ Slides para el workshop
4. ✅ Configuración exacta de GitHub
5. ✅ Plan de la primera semana día por día

**O prefieres empezar directamente con la implementación?**
