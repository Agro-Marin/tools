# Protocolo de Control de Cambios - AgroMarin Odoo

## 🎯 Objetivo

Establecer un flujo de trabajo robusto que garantice la estabilidad del sistema Odoo, facilite futuras migraciones y reduzca el tiempo de integración mediante:

- Control de versiones estructurado (Git Flow)
- Tests automatizados obligatorios
- CI/CD pipeline con validaciones
- Documentación obligatoria de cambios
- Trazabilidad completa de modificaciones al core

---

## 📋 Tabla de Contenidos

1. [Estructura de Branches](#estructura-de-branches)
2. [Workflow de Desarrollo](#workflow-de-desarrollo)
3. [Commits y Mensajes](#commits-y-mensajes)
4. [Pull Requests (Obligatorios)](#pull-requests-obligatorios)
5. [Testing Obligatorio](#testing-obligatorio)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Documentación de Cambios al Core](#documentación-de-cambios-al-core)
8. [Code Review](#code-review)
9. [Herramientas y Automatizaciones](#herramientas-y-automatizaciones)
10. [Roles y Responsabilidades](#roles-y-responsabilidades)

---

## 1. Estructura de Branches

### 1.1 Branches Principales (Protected)

```
odoo-core/
├── 19.0                    # Vanilla Odoo (NUNCA modificar directamente)
├── 19.0-marin             # Customizaciones del core (PROTECTED)
├── 19.0-staging           # Pre-producción
└── 19.0-production        # Producción (solo merges aprobados)

odoo-addons/
├── 19.0-develop           # Integración de features
├── 19.0-staging           # Pre-producción
└── 19.0-main              # Producción
```

### 1.2 Branches de Trabajo (Temporales)

**Nomenclatura obligatoria:**

```
feature/TASK-123-descripcion-corta      # Nueva funcionalidad
bugfix/TASK-456-descripcion-bug         # Corrección de bug
hotfix/TASK-789-critical-issue          # Fix urgente en producción
refactor/TASK-321-clean-code            # Refactorización
docs/TASK-654-update-readme             # Solo documentación
```

**Reglas:**
- Siempre partir desde `19.0-develop` (add-ons) o `19.0-marin` (core)
- Incluir número de tarea de Odoo
- Máximo 3 palabras en descripción
- Solo minúsculas y guiones

### 1.3 Protección de Branches

**Configuración en GitHub/GitLab:**

```yaml
# Branches protegidos
protected_branches:
  - 19.0-marin
  - 19.0-production
  - 19.0-staging
  - 19.0-main
  - 19.0-develop

# Reglas obligatorias
rules:
  require_pull_request: true
  require_approvals: 2  # Al menos 2 aprobaciones
  require_ci_pass: true
  require_up_to_date: true
  no_force_push: true
  no_delete_branch: true
```

---

## 2. Workflow de Desarrollo

### 2.1 Flujo Completo (Diagrama)

```
┌─────────────────────────────────────────────────────────────────┐
│                    INICIO DE DESARROLLO                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ Crear tarea en Odoo   │
                  │ Estado: "To Do"       │
                  └───────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ git checkout develop  │
                  │ git pull origin       │
                  └───────────────────────┘
                              │
                              ▼
                  ┌───────────────────────────────┐
                  │ git checkout -b feature/      │
                  │   TASK-123-descripcion        │
                  └───────────────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ Mover tarea a         │
                  │ "In Progress"         │
                  └───────────────────────┘
                              │
                              ▼
          ┌──────────────────────────────────────┐
          │         CICLO DE DESARROLLO          │
          │                                      │
          │  ┌────────────┐                     │
          │  │  Codificar │                     │
          │  └─────┬──────┘                     │
          │        │                             │
          │        ▼                             │
          │  ┌────────────┐                     │
          │  │ Commit     │ ◄──────┐            │
          │  │ (pre-commit│        │            │
          │  │  checks)   │        │            │
          │  └─────┬──────┘        │            │
          │        │                │            │
          │        ▼                │            │
          │  ┌────────────┐        │            │
          │  │ Run tests  │        │            │
          │  │ localmente │        │            │
          │  └─────┬──────┘        │            │
          │        │                │            │
          │        ├─── ❌ Fallan ──┘            │
          │        │                             │
          │        ▼ ✅ Pasan                    │
          │  ┌────────────┐                     │
          │  │ Más código?│─── Sí ──┐           │
          │  └─────┬──────┘          │           │
          │        │ No              │           │
          │        └─────────────────┘           │
          └──────────────────┬───────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ git push origin       │
                  │   feature/TASK-123    │
                  └───────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ Crear Pull Request    │
                  │ a develop             │
                  └───────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ CI/CD Pipeline        │
                  │ ejecuta validaciones  │
                  └───────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
               ❌ Falla           ✅ Pasa
                    │                   │
                    │                   ▼
                    │       ┌───────────────────────┐
                    │       │ Code Review (2 devs)  │
                    │       └───────────────────────┘
                    │                   │
                    │       ┌───────────┴───────────┐
                    │       ▼                       ▼
                    │  ❌ Rechazado            ✅ Aprobado
                    │       │                       │
                    └───────┴───► Corregir          │
                                                    ▼
                                        ┌───────────────────────┐
                                        │ Merge a develop       │
                                        │ (Squash commits)      │
                                        └───────────────────────┘
                                                    │
                                                    ▼
                                        ┌───────────────────────┐
                                        │ Delete feature branch │
                                        └───────────────────────┘
                                                    │
                                                    ▼
                                        ┌───────────────────────┐
                                        │ Mover tarea a "Done"  │
                                        └───────────────────────┘
```

### 2.2 Procedimiento Detallado

#### Paso 1: Crear Tarea en Odoo

**Antes de escribir código:**

1. Ir a Odoo → Proyecto → Tareas
2. Crear nueva tarea con:
   - **Título claro:** "Implementar validación de stock en ventas"
   - **Descripción:** Criterios de aceptación, contexto
   - **Asignado a:** Developer responsable
   - **Etiquetas:** `feature`, `sale`, `v19.0`
   - **Prioridad:** Baja/Media/Alta/Crítica
3. Obtener número de tarea (ej: TASK-123)

#### Paso 2: Crear Branch de Trabajo

```bash
# 1. Actualizar develop
git checkout 19.0-develop
git pull origin 19.0-develop

# 2. Crear branch desde develop
git checkout -b feature/TASK-123-stock-validation

# 3. Actualizar estado en Odoo
# Mover tarea a "In Progress"
```

#### Paso 3: Desarrollo

```bash
# 1. Escribir código
# 2. Pre-commit hooks se ejecutan automáticamente al hacer commit
# 3. Crear commits incrementales

git add sale_stock/models/sale_order.py
git commit -m "[ADD][sale_stock] Add stock validation before confirm

- Validate stock availability before confirming sale order
- Show warning if stock < ordered quantity
- Block confirmation if stock is zero

Task: TASK-123
"

# 4. Escribir/actualizar tests
vim sale_stock/tests/test_stock_validation.py

# 5. Ejecutar tests localmente
odoo -d test_db -i sale_stock --test-enable --stop-after-init

# 6. Si pasan, hacer commit de tests
git add sale_stock/tests/test_stock_validation.py
git commit -m "[TEST][sale_stock] Add tests for stock validation

Task: TASK-123
"
```

#### Paso 4: Push y Pull Request

```bash
# 1. Push a origin
git push origin feature/TASK-123-stock-validation

# 2. En GitHub/GitLab:
#    - Clic en "Create Pull Request"
#    - Base: 19.0-develop
#    - Compare: feature/TASK-123-stock-validation

# 3. Llenar template de PR (ver sección 4)

# 4. Asignar reviewers (mínimo 2)

# 5. Enlazar tarea de Odoo en descripción del PR
```

#### Paso 5: Code Review y Correcciones

```bash
# Si hay cambios solicitados:

# 1. Hacer correcciones en la misma branch
git add .
git commit -m "[FIX][sale_stock] Address review comments

- Improve error message clarity
- Add null check for product_id

Task: TASK-123
"

# 2. Push
git push origin feature/TASK-123-stock-validation

# 3. El PR se actualiza automáticamente
# 4. Notificar a reviewers
```

#### Paso 6: Merge

```bash
# Una vez aprobado (automático o manual):

# 1. Asegurar que develop está actualizado
git checkout 19.0-develop
git pull origin 19.0-develop

# 2. Merge con squash (en GitHub/GitLab UI)
#    - Squash commits en uno solo
#    - Título: "[ADD][sale_stock] Add stock validation - TASK-123"

# 3. Delete branch automáticamente (configuración de GitHub)

# 4. Actualizar local
git checkout 19.0-develop
git pull origin 19.0-develop
git branch -d feature/TASK-123-stock-validation

# 5. Cerrar tarea en Odoo → "Done"
```

---

## 3. Commits y Mensajes

### 3.1 Formato Obligatorio (Conventional Commits + Odoo)

```
[TIPO][módulo] Título corto (máx 72 caracteres)

Descripción detallada del cambio (si es necesario):
- Bullet point 1
- Bullet point 2
- Bullet point 3

Task: TASK-123
Refs: #456 (si aplica, referencia a issue de GitHub)
```

### 3.2 Tipos de Commit

| Tipo | Uso | Ejemplo |
|------|-----|---------|
| `[ADD]` | Nueva funcionalidad | `[ADD][sale] Add discount validation` |
| `[FIX]` | Corrección de bug | `[FIX][stock] Fix negative stock calculation` |
| `[IMP]` | Mejora de funcionalidad existente | `[IMP][purchase] Improve vendor selection UX` |
| `[REF]` | Refactorización sin cambio funcional | `[REF][account] Refactor invoice computation` |
| `[REM]` | Eliminación de código | `[REM][sale] Remove deprecated method` |
| `[TEST]` | Agregar/modificar tests | `[TEST][stock] Add unit tests for picking` |
| `[DOC]` | Solo documentación | `[DOC][README] Update installation guide` |
| `[I18N]` | Traducciones | `[I18N][sale] Add Spanish translations` |
| `[CORE]` | Cambio en core de Odoo | `[CORE][stock] Override _action_cancel` |

### 3.3 Ejemplos de Buenos Commits

✅ **CORRECTO:**

```
[ADD][sale_custom] Add automatic discount for VIP customers

- Apply 10% discount for customers with VIP tag
- Discount applies only on products with discount_allowed=True
- Add configuration parameter for discount percentage
- Add tests for discount calculation

Task: TASK-234
```

```
[CORE][stock] Override _recompute_state to prevent state reset

In Odoo vanilla, _recompute_state respects preserve_state context flag.
This causes issues in our workflow where we need state to always update.

Solution: Remove preserve_state check in overridden method.

This is a CORE customization that must be documented for future migrations.

Task: TASK-567
Related: MIGRATION-DOC-19.0.md
```

❌ **INCORRECTO:**

```
fix
```

```
changes
```

```
updated some files
```

```
WIP - testing stuff
```

### 3.4 Pre-commit Hooks (Validación Automática)

**Archivo: `.pre-commit-config.yaml`**

```yaml
repos:
  # Black - Formateo de Python
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        args: ['--line-length=120']

  # Vauxoo pre-commit hooks
  - repo: https://github.com/Vauxoo/pylint-odoo
    rev: v9.0.4
    hooks:
      - id: pylint-odoo
        args: ['--disable=all', '--enable=odoolint']

  # Flake8
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=120', '--extend-ignore=E203,W503']

  # isort - Ordenar imports
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile=black', '--line-length=120']

  # Validar mensaje de commit
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.0.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: ['--force-scope']  # Requiere módulo

  # Trailing whitespace
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict

  # Validar sintaxis XML de Odoo
  - repo: https://github.com/oca/maintainer-tools
    rev: master
    hooks:
      - id: oca-checks-odoo-module-installed
```

**Instalación:**

```bash
# 1. Instalar pre-commit
pip install pre-commit

# 2. Instalar hooks en el repositorio
cd /path/to/odoo-addons
pre-commit install
pre-commit install --hook-type commit-msg

# 3. (Opcional) Ejecutar en todos los archivos
pre-commit run --all-files
```

---

## 4. Pull Requests (Obligatorios)

### 4.1 Regla de Oro

**🚫 PROHIBIDO pushear directo a:**
- `19.0-marin` (core)
- `19.0-develop` (add-ons)
- `19.0-staging`
- `19.0-production`
- `19.0-main`

**✅ OBLIGATORIO:**
- TODO cambio debe pasar por Pull Request
- Mínimo 2 aprobaciones
- CI/CD debe pasar
- Code review obligatorio

### 4.2 Template de Pull Request

**Archivo: `.github/pull_request_template.md`**

```markdown
## 📋 Información de la Tarea

**Tarea Odoo:** TASK-XXX
**Link:** [Tarea en Odoo](https://odoo.empresa.com/web#id=XXX)
**Tipo:** Feature / Bug Fix / Hotfix / Refactor / Core Customization

---

## 📝 Descripción del Cambio

### ¿Qué hace este PR?
<!-- Descripción breve del cambio -->

### ¿Por qué es necesario?
<!-- Contexto de negocio o técnico -->

### ¿Qué problema resuelve?
<!-- Issue específico, bug reportado, o mejora -->

---

## 🔧 Cambios Técnicos

### Módulos afectados:
- [ ] `sale_custom`
- [ ] `purchase_custom`
- [ ] `stock_custom`
- [ ] Otro: _______________

### Archivos modificados:
- `module/models/model.py` - Descripción breve
- `module/views/view.xml` - Descripción breve
- `module/tests/test.py` - Descripción breve

### ¿Es customización del CORE?
- [ ] ✅ SÍ - **REQUIERE documentación en `CORE_CUSTOMIZATIONS.md`**
- [ ] ❌ NO - Solo add-ons custom

---

## ✅ Tests

### Tests agregados/modificados:
- [ ] Tests unitarios
- [ ] Tests de integración
- [ ] Tests manuales (describir abajo)

### Cobertura:
- Cobertura anterior: __%
- Cobertura nueva: __%

### Instrucciones para testing manual:
1. Paso 1
2. Paso 2
3. Paso 3

**Resultado esperado:**
<!-- Qué debe pasar -->

---

## 📊 Impacto

### ¿Afecta funcionalidad existente?
- [ ] ✅ SÍ - **Explicar impacto:**
- [ ] ❌ NO

### ¿Requiere migración de datos?
- [ ] ✅ SÍ - **Adjuntar script de migración**
- [ ] ❌ NO

### ¿Requiere actualización de documentación?
- [ ] ✅ SÍ - **Documentación actualizada en:**
- [ ] ❌ NO

### ¿Tiene dependencias externas?
- [ ] ✅ SÍ - **Listar:**
- [ ] ❌ NO

---

## 🖼️ Screenshots (si aplica)

**Antes:**
<!-- Captura de pantalla del estado anterior -->

**Después:**
<!-- Captura de pantalla del nuevo estado -->

---

## ✅ Checklist del Developer

- [ ] Código sigue las convenciones de estilo (Black, Flake8)
- [ ] Pre-commit hooks pasan localmente
- [ ] Tests unitarios agregados/actualizados
- [ ] Tests pasan localmente
- [ ] Documentación actualizada (README, docstrings)
- [ ] Commit messages siguen convención `[TIPO][módulo]`
- [ ] Branch actualizado con develop (`git merge develop`)
- [ ] No hay conflictos de merge
- [ ] Si es CORE customization: documentado en `CORE_CUSTOMIZATIONS.md`

---

## 👀 Reviewers

**Asignados:**
- @developer1
- @developer2

**Checklist para Reviewers:**
- [ ] Código es legible y mantenible
- [ ] Lógica es correcta
- [ ] Tests cubren casos edge
- [ ] No hay código duplicado
- [ ] Performance es aceptable
- [ ] Seguridad: no hay vulnerabilidades obvias
- [ ] Si es CORE: cambio está bien justificado y documentado

---

## 📎 Referencias

**Issues relacionados:**
- Closes #123
- Related to #456

**Documentación:**
- [Link a documentación técnica]
- [Link a especificación]

**Notas adicionales:**
<!-- Cualquier información relevante -->
```

### 4.3 Proceso de Code Review

#### Roles:

1. **Author (Developer):**
   - Crear PR con template completo
   - Responder a comentarios
   - Realizar correcciones solicitadas

2. **Reviewers (2 mínimo):**
   - Revisar en máximo 24 horas
   - Dejar comentarios constructivos
   - Aprobar o solicitar cambios

3. **Maintainer (Tech Lead):**
   - Hacer merge final
   - Validar que cumple estándares

#### Checklist del Reviewer:

```markdown
## Code Review Checklist

### Funcionalidad
- [ ] El código hace lo que dice que hace
- [ ] La solución es la más simple posible
- [ ] Los casos edge están cubiertos

### Código
- [ ] Código legible y autodocumentado
- [ ] Nombres de variables/funciones son descriptivos
- [ ] No hay código comentado (dead code)
- [ ] No hay código duplicado (DRY)
- [ ] Imports están ordenados

### Odoo Best Practices
- [ ] Usa API de Odoo correctamente (@api.depends, etc.)
- [ ] Herencia de modelos es correcta (_name vs _inherit)
- [ ] Security rules (ir.model.access.csv) actualizadas
- [ ] Views siguen estructura estándar
- [ ] No hay hardcoded IDs (usar xml_id)

### Tests
- [ ] Tests cubren la funcionalidad nueva
- [ ] Tests cubren casos de error
- [ ] Tests pasan en CI/CD
- [ ] Nombres de tests son descriptivos

### Performance
- [ ] No hay queries N+1
- [ ] Usa búsquedas eficientes (search_read cuando aplica)
- [ ] Campos computados tienen store=True si se buscan
- [ ] No hay loops innecesarios

### Seguridad
- [ ] Inputs del usuario son validados
- [ ] No hay SQL injection (evitar SQL directo)
- [ ] Permisos de acceso están correctos
- [ ] No se expone información sensible

### Documentación
- [ ] Docstrings en métodos públicos
- [ ] Comentarios explican "por qué", no "qué"
- [ ] README actualizado si es necesario
- [ ] Si es CORE: documentado en CORE_CUSTOMIZATIONS.md

### Git
- [ ] Commits son atómicos (un concepto por commit)
- [ ] Mensajes de commit son claros
- [ ] Branch está actualizado con develop
- [ ] No hay merge conflicts
```

#### Tipos de Comentarios:

```markdown
# Bloquea merge (debe corregirse)
🔴 **[BLOCKER]** Este código tiene un bug: ...

# Debe corregirse antes de merge
🟡 **[MUST FIX]** Esta lógica debería estar en un método separado

# Sugerencia (no bloquea)
🟢 **[SUGGESTION]** Podrías mejorar esto usando ...

# Pregunta
❓ **[QUESTION]** ¿Por qué elegiste este enfoque?

# Nitpick (cosmético, no crítico)
💅 **[NITPICK]** Podrías renombrar esta variable a...

# Elogio (¡también importante!)
⭐ **[PRAISE]** Excelente uso de decoradores aquí
```

---

## 5. Testing Obligatorio

### 5.1 Regla de Oro

**🚫 NO SE MERGEA SIN TESTS**

Excepciones:
- Cambios solo de documentación (`[DOC]`)
- Cambios solo de traducciones (`[I18N]`)
- Hotfixes críticos (pero tests se agregan después en máximo 24h)

### 5.2 Cobertura Mínima Requerida

| Tipo de Módulo | Cobertura Mínima |
|----------------|------------------|
| Core customizations | 90% |
| Módulos custom críticos (sale, purchase, stock) | 80% |
| Módulos custom no críticos | 70% |
| Módulos de integración | 60% |

### 5.3 Estructura de Tests

```python
# addons/sale_custom/tests/__init__.py
from . import test_sale_order
from . import test_sale_order_line

# addons/sale_custom/tests/test_sale_order.py
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install', 'sale_custom')
class TestSaleOrder(TransactionCase):
    """Test suite for sale.order customizations"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Setup de datos de prueba
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
            'vip': True,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
            'discount_allowed': True,
        })

    def test_01_vip_discount_applied(self):
        """Test that VIP customers get automatic discount"""
        # Arrange
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        order_line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 10,
        })

        # Act
        order._apply_vip_discount()

        # Assert
        self.assertEqual(
            order_line.discount,
            10.0,
            "VIP customer should get 10% discount"
        )

    def test_02_no_discount_for_non_vip(self):
        """Test that non-VIP customers don't get discount"""
        # Arrange
        non_vip_partner = self.env['res.partner'].create({
            'name': 'Non VIP Partner',
            'vip': False,
        })
        order = self.env['sale.order'].create({
            'partner_id': non_vip_partner.id,
        })
        order_line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 10,
        })

        # Act
        order._apply_vip_discount()

        # Assert
        self.assertEqual(
            order_line.discount,
            0.0,
            "Non-VIP customer should not get discount"
        )

    def test_03_discount_not_allowed_on_product(self):
        """Test that products with discount_allowed=False don't get discount"""
        # Arrange
        no_discount_product = self.env['product.product'].create({
            'name': 'No Discount Product',
            'list_price': 100.0,
            'discount_allowed': False,
        })
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        order_line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': no_discount_product.id,
            'product_uom_qty': 10,
        })

        # Act
        order._apply_vip_discount()

        # Assert
        self.assertEqual(
            order_line.discount,
            0.0,
            "Product with discount_allowed=False should not get discount"
        )

    def test_04_discount_raises_error_if_negative(self):
        """Test that negative discounts raise validation error"""
        # Arrange
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        order_line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 10,
        })

        # Act & Assert
        with self.assertRaises(ValidationError):
            order_line.discount = -10.0
```

### 5.4 Ejecutar Tests Localmente

```bash
# Tests de un módulo específico
odoo -d test_db -i sale_custom --test-enable --stop-after-init

# Tests con cobertura
coverage run --source=addons/sale_custom odoo-bin -d test_db -i sale_custom --test-enable --stop-after-init
coverage report
coverage html  # Genera reporte HTML

# Tests con tags específicos
odoo -d test_db --test-tags sale_custom --stop-after-init

# Tests en modo debug
odoo -d test_db -i sale_custom --test-enable --stop-after-init --log-level=test
```

---

## 6. CI/CD Pipeline

### 6.1 Herramientas

**Opción recomendada: GitHub Actions** (gratis para repos privados)

Alternativas:
- GitLab CI/CD
- Jenkins
- CircleCI

### 6.2 Pipeline Automático

**Archivo: `.github/workflows/odoo-ci.yml`**

```yaml
name: Odoo CI/CD

on:
  pull_request:
    branches:
      - 19.0-develop
      - 19.0-staging
      - 19.0-main
  push:
    branches:
      - 19.0-develop
      - 19.0-staging

jobs:
  # Job 1: Linting y Code Quality
  lint:
    name: Lint and Code Quality
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install black flake8 isort pylint-odoo

      - name: Run Black
        run: black --check --line-length 120 addons/

      - name: Run Flake8
        run: flake8 --max-line-length 120 --extend-ignore=E203,W503 addons/

      - name: Run isort
        run: isort --check --profile black --line-length 120 addons/

      - name: Run pylint-odoo
        run: pylint --load-plugins=pylint_odoo --disable=all --enable=odoolint addons/

  # Job 2: Security Scan
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Bandit (security linter)
        run: |
          pip install bandit
          bandit -r addons/ -f json -o bandit-report.json

      - name: Upload security report
        uses: actions/upload-artifact@v3
        with:
          name: bandit-report
          path: bandit-report.json

  # Job 3: Unit Tests
  test:
    name: Unit Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: odoo
          POSTGRES_PASSWORD: odoo
          POSTGRES_DB: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install Odoo dependencies
        run: |
          pip install -r requirements.txt

      - name: Clone Odoo
        run: |
          git clone --depth 1 --branch 19.0 https://github.com/odoo/odoo.git odoo
          git clone --depth 1 --branch 19.0 https://github.com/odoo/enterprise.git enterprise

      - name: Install addons
        run: |
          ln -s $(pwd)/addons odoo/addons/custom

      - name: Create Odoo config
        run: |
          echo "[options]" > odoo.conf
          echo "addons_path = odoo/addons,enterprise,addons" >> odoo.conf
          echo "db_host = localhost" >> odoo.conf
          echo "db_port = 5432" >> odoo.conf
          echo "db_user = odoo" >> odoo.conf
          echo "db_password = odoo" >> odoo.conf

      - name: Initialize test database
        run: |
          python odoo/odoo-bin -c odoo.conf -d test_db --init base --stop-after-init --log-level=error

      - name: Run tests with coverage
        run: |
          coverage run --source=addons odoo/odoo-bin -c odoo.conf -d test_db \
            --test-enable --stop-after-init --log-level=test \
            -u $(find addons/* -maxdepth 0 -type d -printf "%f,")

      - name: Generate coverage report
        run: |
          coverage report
          coverage xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-odoo

  # Job 4: Build and Deploy to Staging (solo en develop)
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [lint, security, test]
    if: github.ref == 'refs/heads/19.0-develop' && github.event_name == 'push'
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to staging server
        run: |
          # Script de deployment (SSH a servidor staging)
          echo "Deploying to staging..."
          # ssh user@staging-server 'cd /opt/odoo && git pull && systemctl restart odoo'

      - name: Run smoke tests on staging
        run: |
          # Tests básicos en staging
          echo "Running smoke tests..."
          # curl -f https://staging.empresa.com/web/database/selector

      - name: Notify team
        run: |
          # Notificación a Slack/Email
          echo "Staging deployed successfully!"
```

### 6.3 Status Badges

Agregar al README.md:

```markdown
# Odoo Custom Addons

![CI Status](https://github.com/empresa/odoo-addons/workflows/Odoo%20CI%2FCD/badge.svg)
![Coverage](https://codecov.io/gh/empresa/odoo-addons/branch/19.0-develop/graph/badge.svg)
![Code Quality](https://img.shields.io/badge/code%20style-black-000000.svg)
```

---

## 7. Documentación de Cambios al Core

### 7.1 Archivo Obligatorio: `CORE_CUSTOMIZATIONS.md`

**Ubicación:** Raíz del repositorio odoo-core

**Estructura:**

```markdown
# Core Customizations - Odoo 19.0-marin

## 📋 Índice de Customizaciones

| ID | Módulo | Archivo | Método/Campo | Tipo | Criticidad | Fecha |
|----|--------|---------|--------------|------|------------|-------|
| CORE-001 | stock | models/stock_move.py | `_recompute_state()` | Override | Alta | 2025-10-15 |
| CORE-002 | sale | models/sale_order.py | `invoice_status` | Modify | Media | 2025-10-20 |
| CORE-003 | purchase | models/purchase_order.py | `button_cancel()` | Override | Alta | 2025-10-22 |

**Total customizaciones:** 3

---

## CORE-001: Override _recompute_state in stock.move

### 📋 Información General

| Campo | Valor |
|-------|-------|
| **ID** | CORE-001 |
| **Módulo** | stock |
| **Archivo** | `addons/stock/models/stock_move.py` |
| **Método** | `_recompute_state()` |
| **Tipo de cambio** | Override completo |
| **Criticidad** | 🔴 Alta |
| **Fecha de implementación** | 2025-10-15 |
| **Developer** | @developer1 |
| **Task Odoo** | TASK-567 |
| **Commit** | abc123def456 |

### 📝 Descripción del Cambio

**¿Qué se modificó?**

Se eliminó la validación del contexto `preserve_state` que bloqueaba el recálculo de estado en ciertos flujos.

**¿Por qué se hizo?**

En el flujo de validación de pickings con múltiples movimientos, el flag `preserve_state` causaba inconsistencias de estado cuando movimientos dependientes necesitaban actualizarse.

**¿Qué problema resuelve?**

- Estados de movimientos no se actualizaban correctamente después de validar picking
- Movimientos quedaban en estado "asignado" aunque ya estaban "hecho"
- Reportes de inventario mostraban datos inconsistentes

### 💻 Código

**ANTES (Odoo 19.0 vanilla):**

```python
def _recompute_state(self):
    if self._context.get('preserve_state'):
        return
    moves_state_to_write = defaultdict(set)
    # ... resto del código
```

**DESPUÉS (19.0-marin):**

```python
def _recompute_state(self):
    # CUSTOM: Removed preserve_state check to ensure state always updates
    # This fixes inconsistencies in multi-move picking validation
    # See: CORE_CUSTOMIZATIONS.md#CORE-001
    moves_state_to_write = defaultdict(set)
    # ... resto del código
```

**Diff:**

```diff
def _recompute_state(self):
-   if self._context.get('preserve_state'):
-       return
+   # CUSTOM: Removed preserve_state check
    moves_state_to_write = defaultdict(set)
```

### 🧪 Tests

**Tests añadidos:**

- `test_recompute_state_without_preserve_flag()` - Verifica que estado se actualiza
- `test_recompute_state_with_preserve_flag()` - Verifica que se ignora el flag
- `test_multi_move_picking_state_consistency()` - Verifica consistencia en pickings complejos

**Ubicación tests:**
`addons/stock_custom/tests/test_stock_move_core.py`

### 🔄 Impacto en Futuras Migraciones

**Odoo 20.0:**
- ✅ Verificar si Odoo upstream corrigió este comportamiento
- ⚠️ Si no, replicar este cambio en v20

**Proceso de verificación:**
1. Buscar commits relacionados con `_recompute_state` en Odoo repo oficial
2. Revisar si eliminaron o modificaron el flag `preserve_state`
3. Ejecutar tests de stock_custom en v20 vanilla para ver si pasan

### 📊 Dependencias

**Módulos que dependen de este cambio:**
- `stock_custom` - Tests de validación
- `stock_picking_batch_custom` - Usa recompute en batch operations

**Campos/Métodos relacionados:**
- `stock.move._action_done()`
- `stock.move._action_assign()`
- `stock.picking._action_done()`

### ✅ Checklist de Mantenimiento

- [x] Código comentado con referencia a CORE_CUSTOMIZATIONS.md
- [x] Tests unitarios agregados
- [x] Documentado en este archivo
- [x] Commit bien identificado con `[CORE]`
- [ ] Validado en cada upgrade de Odoo (pendiente v20)

---

## CORE-002: Modify invoice_status flow in sale.order

[Seguir el mismo formato...]

---

## 📚 Guía de Uso

### Para Developers:

Cuando hagas una customización del CORE:

1. Asigna el siguiente ID disponible (CORE-XXX)
2. Documenta siguiendo el template arriba
3. Agrega comentario en el código:
   ```python
   # CUSTOM: Brief explanation
   # See: CORE_CUSTOMIZATIONS.md#CORE-XXX
   ```
4. Agrega entrada en la tabla de índice
5. Crea tests específicos para el cambio
6. Commit con prefijo `[CORE][módulo]`

### Para Futuras Migraciones:

1. Abrir este archivo
2. Revisar cada customización (CORE-XXX)
3. Verificar en nueva versión de Odoo si ya está corregido
4. Marcar en checklist de mantenimiento
5. Actualizar o eliminar customización según corresponda
```

### 7.2 Comentarios en Código

**Obligatorio** agregar comentario en el código customizado:

```python
# addons/stock/models/stock_move.py

def _recompute_state(self):
    # ============================================================================
    # CUSTOM CORE MODIFICATION - CORE-001
    # Removed preserve_state check to ensure state always updates
    # This fixes state inconsistencies in multi-move picking validation
    # Documentation: CORE_CUSTOMIZATIONS.md#CORE-001
    # Date: 2025-10-15
    # ============================================================================
    moves_state_to_write = defaultdict(set)
    # ... resto del código
```

---

## 8. Code Review

### 8.1 Proceso de Review

**Timing:**
- Reviews deben completarse en máximo **24 horas**
- Si no puedes revisar, reasigna a otro developer

**Asignación:**
- Mínimo **2 reviewers** por PR
- Al menos 1 debe ser senior developer
- Si es CORE customization: **obligatorio** review del Tech Lead

### 8.2 Herramientas de Review

**GitHub/GitLab:**
- Usar sistema de comentarios inline
- Marcar conversaciones como "resueltas"
- Aprobar solo cuando todo esté OK

**Revisar también:**
- Commits individuales (no solo diff final)
- Tests añadidos
- Documentación actualizada

### 8.3 Criterios de Aprobación

**Aprobar solo si:**
- ✅ Código cumple estándares
- ✅ Tests pasan y cubren funcionalidad
- ✅ No hay código duplicado
- ✅ Documentación está completa
- ✅ Commits bien escritos
- ✅ Si es CORE: documentado en CORE_CUSTOMIZATIONS.md

**Rechazar si:**
- ❌ Tests fallan
- ❌ Linters tienen errores
- ❌ Código ilegible o sin documentar
- ❌ Performance degradada significativamente
- ❌ Vulnerabilidades de seguridad

---

## 9. Herramientas y Automatizaciones

### 9.1 Stack de Herramientas

```
┌─────────────────────────────────────────────────────────┐
│                   STACK DE HERRAMIENTAS                 │
└─────────────────────────────────────────────────────────┘

Control de Versiones:
├── Git                    # Control de versiones
├── GitHub/GitLab          # Hosting + PR + CI/CD
└── GitKraken/SourceTree   # Cliente visual (opcional)

Code Quality:
├── Black                  # Formateo automático Python
├── Flake8                 # Linting Python
├── isort                  # Ordenar imports
├── pylint-odoo            # Linting específico Odoo
└── pre-commit             # Hooks automáticos

Testing:
├── pytest (odoo-pytest)   # Framework de tests
├── coverage.py            # Cobertura de código
└── codecov                # Visualización de cobertura

CI/CD:
├── GitHub Actions         # Pipeline automático
├── Docker                 # Containers para testing
└── PostgreSQL             # Base de datos de tests

Gestión de Tareas:
├── Odoo Project           # Tareas y sprints
└── GitHub Projects        # Kanban (opcional)

Comunicación:
├── Slack                  # Notificaciones CI/CD
└── Email                  # Notificaciones críticas

Documentación:
├── Markdown               # Formato de documentación
├── MkDocs                 # Generador de docs (opcional)
└── draw.io                # Diagramas (opcional)
```

### 9.2 Scripts Útiles

**Archivo: `scripts/check_before_commit.sh`**

```bash
#!/bin/bash
# Script para ejecutar antes de commit
# Uso: ./scripts/check_before_commit.sh

set -e

echo "🔍 Ejecutando validaciones pre-commit..."

# 1. Black
echo "1/5 Ejecutando Black..."
black --check --line-length 120 addons/
if [ $? -ne 0 ]; then
    echo "❌ Black encontró problemas. Ejecuta: black addons/"
    exit 1
fi

# 2. Flake8
echo "2/5 Ejecutando Flake8..."
flake8 --max-line-length 120 --extend-ignore=E203,W503 addons/
if [ $? -ne 0 ]; then
    echo "❌ Flake8 encontró problemas."
    exit 1
fi

# 3. isort
echo "3/5 Ejecutando isort..."
isort --check --profile black --line-length 120 addons/
if [ $? -ne 0 ]; then
    echo "❌ isort encontró problemas. Ejecuta: isort addons/"
    exit 1
fi

# 4. pylint-odoo
echo "4/5 Ejecutando pylint-odoo..."
pylint --load-plugins=pylint_odoo --disable=all --enable=odoolint addons/
if [ $? -ne 0 ]; then
    echo "❌ pylint-odoo encontró problemas."
    exit 1
fi

# 5. Tests
echo "5/5 Ejecutando tests..."
odoo -d test_db --test-enable --stop-after-init -u $(find addons/* -maxdepth 0 -type d -printf "%f,")
if [ $? -ne 0 ]; then
    echo "❌ Tests fallaron."
    exit 1
fi

echo "✅ Todas las validaciones pasaron!"
```

**Archivo: `scripts/update_coverage.sh`**

```bash
#!/bin/bash
# Actualizar reporte de cobertura
# Uso: ./scripts/update_coverage.sh

coverage run --source=addons odoo-bin -d test_db --test-enable --stop-after-init
coverage report
coverage html
echo "✅ Reporte generado en htmlcov/index.html"
xdg-open htmlcov/index.html  # Abre en navegador
```

**Archivo: `scripts/new_feature.sh`**

```bash
#!/bin/bash
# Crear nueva feature branch siguiendo convenciones
# Uso: ./scripts/new_feature.sh TASK-123 "descripcion corta"

TASK_ID=$1
DESCRIPTION=$2

if [ -z "$TASK_ID" ] || [ -z "$DESCRIPTION" ]; then
    echo "Uso: ./scripts/new_feature.sh TASK-123 \"descripcion corta\""
    exit 1
fi

# Formatear descripción (lowercase, guiones)
FORMATTED_DESC=$(echo "$DESCRIPTION" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

# Crear branch
git checkout 19.0-develop
git pull origin 19.0-develop
git checkout -b feature/$TASK_ID-$FORMATTED_DESC

echo "✅ Branch creado: feature/$TASK_ID-$FORMATTED_DESC"
echo "📝 No olvides mover la tarea a 'In Progress' en Odoo"
```

### 9.3 Integraciones

#### Slack Notifications

**GitHub Actions → Slack:**

```yaml
# .github/workflows/odoo-ci.yml

- name: Notify Slack on success
  if: success()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "✅ CI passed for PR #${{ github.event.pull_request.number }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*CI Passed* :white_check_mark:\n*PR:* <${{ github.event.pull_request.html_url }}|#${{ github.event.pull_request.number }}>\n*Author:* ${{ github.event.pull_request.user.login }}"
            }
          }
        ]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

- name: Notify Slack on failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "❌ CI failed for PR #${{ github.event.pull_request.number }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*CI Failed* :x:\n*PR:* <${{ github.event.pull_request.html_url }}|#${{ github.event.pull_request.number }}>\n*Author:* ${{ github.event.pull_request.user.login }}"
            }
          }
        ]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## 10. Roles y Responsabilidades

### 10.1 Matriz RACI

| Actividad | Developer | Senior Dev | Tech Lead | DevOps |
|-----------|-----------|------------|-----------|---------|
| Crear feature branch | **R** | | I | |
| Escribir código | **R** | C | I | |
| Escribir tests | **R** | C | I | |
| Commit con mensajes correctos | **R** | C | A | |
| Crear Pull Request | **R** | | I | |
| Code Review | C | **R** | A | |
| Aprobar PR (2 aprobaciones) | | **R** | **R** | |
| Merge a develop | | C | **R** | |
| Deploy a staging | | | I | **R** |
| Validar staging | C | C | **A** | R |
| Deploy a producción | | | A | **R** |
| Documentar CORE changes | **R** | C | **A** | |
| Mantener CI/CD pipeline | I | I | C | **R** |
| Resolver merge conflicts | **R** | C | A | |

**Leyenda:**
- **R** = Responsible (ejecuta)
- **A** = Accountable (aprueba)
- **C** = Consulted (consultado)
- **I** = Informed (informado)

### 10.2 Descripción de Roles

#### Developer
**Responsabilidades:**
- Implementar features/bugfixes asignados
- Escribir tests para sus cambios
- Crear PRs siguiendo template
- Responder a comentarios de code review
- Documentar código (docstrings, comentarios)
- Resolver merge conflicts en sus branches

**Skills requeridos:**
- Python intermedio
- Conocimiento de Odoo framework
- Git básico
- Testing básico

#### Senior Developer
**Responsabilidades:**
- Revisar PRs de otros developers (code review)
- Aprobar PRs (mínimo 1 aprobación de senior)
- Mentorear a developers junior
- Diseñar soluciones técnicas complejas
- Resolver bugs críticos
- Estimar tiempos de desarrollo

**Skills requeridos:**
- Python avanzado
- Odoo framework avanzado
- Git avanzado
- Arquitectura de software
- Testing avanzado

#### Tech Lead
**Responsabilidades:**
- Aprobar TODAS las CORE customizations
- Hacer merge final a branches protegidos
- Mantener CORE_CUSTOMIZATIONS.md actualizado
- Definir arquitectura y estándares
- Revisar PRs complejos
- Tomar decisiones técnicas críticas
- Planificar roadmap técnico
- Coordinar con DevOps

**Skills requeridos:**
- Todos los de Senior Dev +
- Liderazgo técnico
- Conocimiento profundo de Odoo internals
- Experiencia en migraciones de versiones
- Visión de producto

#### DevOps
**Responsabilidades:**
- Mantener CI/CD pipeline funcionando
- Configurar y mantener servidores (dev, staging, prod)
- Automatizar deploys
- Monitorear performance y logs
- Gestionar backups
- Resolver issues de infraestructura
- Configurar herramientas (GitHub, Slack, etc.)

**Skills requeridos:**
- Linux/Bash
- Docker
- CI/CD (GitHub Actions, GitLab CI)
- PostgreSQL
- Nginx/Apache
- Scripting

---

## 11. Métricas y KPIs

### 11.1 Métricas a Trackear

| Métrica | Objetivo | Frecuencia |
|---------|----------|------------|
| Tiempo promedio de PR abierto → merged | < 48 horas | Semanal |
| % de PRs con CI passing en primer intento | > 80% | Semanal |
| Cobertura de tests | > 75% | Mensual |
| Número de CORE customizations | Minimizar | Trimestral |
| Bugs reportados en producción | < 5/mes | Mensual |
| Tiempo de deployment (staging) | < 30 min | Por deploy |
| Tiempo de rollback (si falla producción) | < 2 horas | N/A |

### 11.2 Dashboard Sugerido

**Herramientas:**
- GitHub Insights (gratis)
- Codecov (cobertura)
- Custom dashboard en Odoo (opcional)

**Métricas a mostrar:**
- PRs abiertos vs cerrados (gráfico de tiempo)
- Distribución de tipos de commits ([ADD], [FIX], etc.)
- Cobertura de tests por módulo (heatmap)
- Tiempo promedio de review
- Top contributors

---

## 12. Proceso de Adopción

### 12.1 Plan de Implementación (Fase a Fase)

#### Fase 1: Fundación (Semana 1-2)

**Objetivos:**
- Configurar herramientas básicas
- Proteger branches principales
- Establecer convenciones de commits

**Tareas:**
```
□ Instalar pre-commit en repos
□ Configurar Black, Flake8, isort
□ Proteger branches en GitHub (19.0-marin, 19.0-develop, etc.)
□ Crear template de PR
□ Documentar convenciones de commits
□ Workshop: Git Flow + Commits (2 horas)
```

#### Fase 2: Testing (Semana 3-4)

**Objetivos:**
- Establecer cultura de testing
- Configurar framework de tests
- Escribir primeros tests

**Tareas:**
```
□ Setup pytest-odoo
□ Configurar coverage.py
□ Escribir tests para módulos críticos (sale, purchase, stock)
□ Alcanzar 50% de cobertura inicial
□ Workshop: Testing en Odoo (3 horas)
```

#### Fase 3: CI/CD (Semana 5-6)

**Objetivos:**
- Automatizar validaciones
- Setup pipeline básico
- Integrar con Slack

**Tareas:**
```
□ Configurar GitHub Actions
□ Setup ambiente de testing (Docker + PostgreSQL)
□ Crear jobs de lint, test, deploy
□ Integrar notificaciones Slack
□ Workshop: CI/CD Pipeline (2 horas)
```

#### Fase 4: Code Review (Semana 7-8)

**Objetivos:**
- Establecer proceso de review
- Capacitar en mejores prácticas
- Hacer PRs obligatorios

**Tareas:**
```
□ Prohibir push directo a branches protegidos (enforcement)
□ Asignar roles de reviewers
□ Crear checklist de code review
□ Hacer 10 PRs de práctica con review
□ Workshop: Code Review Best Practices (2 horas)
```

#### Fase 5: Documentación CORE (Semana 9-10)

**Objetivos:**
- Documentar customizaciones existentes
- Establecer proceso para futuras customizaciones

**Tareas:**
```
□ Crear CORE_CUSTOMIZATIONS.md
□ Documentar customizaciones actuales de 19.0-marin
□ Agregar comentarios en código customizado
□ Establecer proceso obligatorio para nuevas customizations
□ Workshop: Documentar CORE changes (1 hora)
```

#### Fase 6: Optimización (Semana 11-12)

**Objetivos:**
- Refinar procesos
- Alcanzar objetivos de métricas
- Retrospectiva

**Tareas:**
```
□ Revisar métricas de las últimas semanas
□ Ajustar procesos según feedback del equipo
□ Alcanzar 75% de cobertura de tests
□ Reducir tiempo de PR a < 48h
□ Retrospectiva del equipo
□ Documentar lecciones aprendidas
```

### 12.2 Resistencia al Cambio

**Objeciones comunes y cómo manejarlas:**

| Objeción | Respuesta |
|----------|-----------|
| "Esto hace más lento el desarrollo" | "Inicialmente sí, pero previene bugs en producción que toman días arreglar. A largo plazo ahorramos tiempo." |
| "Los tests toman mucho tiempo" | "Empezamos con cobertura baja (50%) y subimos gradualmente. No es todo o nada." |
| "Ya sé programar, no necesito code review" | "El code review no es solo para encontrar errores, es para compartir conocimiento y mantener consistencia." |
| "Git Flow es muy complicado" | "Tenemos scripts que automatizan lo tedioso. Además, es estándar en la industria." |
| "No tengo tiempo para documentar CORE changes" | "Si no documentamos, la próxima migración tomará meses en vez de semanas. Es inversión, no gasto." |

**Estrategias:**
- 🎯 Mostrar datos: comparar tiempo de migración 18→19 vs proyección con nuevo proceso
- 👥 Peer pressure positivo: reconocer públicamente a quienes sigan el proceso
- 🏆 Gamificación: leaderboard de cobertura de tests, mejor reviewer del mes
- 📊 Transparencia: dashboard con métricas visibles para todos

### 12.3 Training Plan

**Workshops obligatorios:**

1. **Git Flow y Commits** (2 horas)
   - Convenciones de branches
   - Mensajes de commit
   - Manejo de merge conflicts
   - Demo: crear feature branch end-to-end

2. **Testing en Odoo** (3 horas)
   - Por qué testear
   - Estructura de tests en Odoo
   - Escribir tests unitarios
   - Ejecutar tests localmente
   - Hands-on: escribir tests para módulo existente

3. **CI/CD Pipeline** (2 horas)
   - Qué es CI/CD
   - Cómo funciona nuestro pipeline
   - Interpretar resultados de CI
   - Qué hacer cuando CI falla

4. **Code Review Best Practices** (2 horas)
   - Cómo hacer un buen review
   - Cómo recibir feedback
   - Tipos de comentarios
   - Práctica: revisar PRs reales

5. **Documentar CORE Changes** (1 hora)
   - Por qué documentar
   - Template de CORE_CUSTOMIZATIONS.md
   - Comentarios en código
   - Demo: documentar una customización

**Total:** 10 horas de training (distribuido en 2-3 semanas)

---

## 13. Casos de Uso Comunes

### 13.1 Caso: Feature Nueva

```bash
# 1. Crear tarea en Odoo: TASK-500 "Add auto-discount for VIP"
# 2. Mover a "In Progress"

# 3. Crear branch
git checkout 19.0-develop
git pull
git checkout -b feature/TASK-500-vip-auto-discount

# 4. Desarrollar
vim addons/sale_custom/models/sale_order.py
# ... código ...

# 5. Tests
vim addons/sale_custom/tests/test_vip_discount.py
# ... tests ...

# 6. Commit
git add .
git commit -m "[ADD][sale_custom] Add automatic discount for VIP customers

- Apply 10% discount for customers with VIP tag
- Only on products with discount_allowed=True
- Add config parameter for discount percentage
- Add tests for discount calculation

Task: TASK-500
"

# 7. Push y PR
git push origin feature/TASK-500-vip-auto-discount
# Crear PR en GitHub con template

# 8. Esperar aprobación y merge

# 9. Cleanup
git checkout 19.0-develop
git pull
git branch -d feature/TASK-500-vip-auto-discount

# 10. Cerrar tarea en Odoo
```

### 13.2 Caso: Bug Fix

```bash
# 1. Crear tarea: TASK-501 "Fix stock calculation error"
# 2. Mover a "In Progress"

# 3. Crear branch de bugfix
git checkout 19.0-develop
git pull
git checkout -b bugfix/TASK-501-stock-calculation

# 4. Fix
vim addons/stock_custom/models/stock_quant.py
# ... fix ...

# 5. Test que reproduce el bug
vim addons/stock_custom/tests/test_stock_quant.py
def test_stock_calculation_negative():
    """Test that stock calculation handles negative values correctly"""
    # Arrange
    # Act
    # Assert

# 6. Commit
git add .
git commit -m "[FIX][stock_custom] Fix stock calculation with negative moves

Bug: Stock calculation was incorrect when moves had negative quantities.
Root cause: Missing abs() in computation.

Solution: Add absolute value check in _compute_available_quantity()

Task: TASK-501
Fixes: #123
"

# 7. Push y PR
git push origin bugfix/TASK-501-stock-calculation
# Crear PR con label "bug"

# 8. Merge y cleanup
```

### 13.3 Caso: Hotfix en Producción

```bash
# 1. Crear tarea URGENTE: TASK-502 "Critical: Invoice generation fails"
# 2. Notificar a Tech Lead

# 3. Crear branch de hotfix desde PRODUCTION
git checkout 19.0-production
git pull
git checkout -b hotfix/TASK-502-invoice-crash

# 4. Fix (mínimo cambio posible)
vim addons/account_custom/models/account_move.py
# ... fix crítico ...

# 5. Test (puede ser después si es muy urgente)
# ... agregar test ...

# 6. Commit
git add .
git commit -m "[HOTFIX][account_custom] Fix invoice generation crash

Critical bug: Invoice generation crashes when partner has no email.
Fix: Add null check before sending email.

Task: TASK-502
Severity: Critical
"

# 7. Push y PR urgente
git push origin hotfix/TASK-502-invoice-crash
# Crear PR con label "hotfix" y "critical"
# Notificar a reviewers por Slack

# 8. Fast-track review (Tech Lead + 1 Senior)

# 9. Merge a production
# Tech Lead hace merge directo

# 10. Deploy inmediato
# DevOps deploya a producción

# 11. Backport a develop y staging
git checkout 19.0-develop
git merge hotfix/TASK-502-invoice-crash
git push

# 12. Agregar tests (si no se hizo antes) en siguientes 24h
```

### 13.4 Caso: Customización del CORE

```bash
# 1. Crear tarea: TASK-503 "Override stock.move._action_cancel"
# 2. Discutir con Tech Lead (¿es realmente necesario?)

# 3. Si se aprueba, crear branch
git checkout 19.0-marin  # ¡Nota: marin, no develop!
git pull
git checkout -b feature/TASK-503-override-cancel

# 4. Implementar override
vim odoo/addons/stock/models/stock_move.py

def _action_cancel(self):
    # ============================================================================
    # CUSTOM CORE MODIFICATION - CORE-004
    # Add validation to prevent cancellation of moves with related production
    # Documentation: CORE_CUSTOMIZATIONS.md#CORE-004
    # Date: 2025-11-01
    # ============================================================================
    for move in self:
        if move.production_id and move.production_id.state == 'done':
            raise ValidationError(
                "Cannot cancel move related to completed production order"
            )
    return super()._action_cancel()

# 5. Documentar en CORE_CUSTOMIZATIONS.md
vim CORE_CUSTOMIZATIONS.md
# ... agregar entrada CORE-004 ...

# 6. Tests
vim odoo/addons/stock_custom/tests/test_stock_move_core.py
# ... tests específicos ...

# 7. Commit
git add .
git commit -m "[CORE][stock] Override _action_cancel to validate production state

Prevent cancellation of stock moves that are linked to completed
production orders to maintain data integrity.

This is a CORE customization documented in CORE_CUSTOMIZATIONS.md#CORE-004

Task: TASK-503
"

# 8. Push y PR (requiere aprobación de Tech Lead)
git push origin feature/TASK-503-override-cancel
# PR con label "core-customization"

# 9. Review obligatorio de Tech Lead

# 10. Merge a 19.0-marin
```

---

## 14. FAQ

### ¿Qué hago si mi PR tiene conflictos con develop?

```bash
# 1. Actualizar develop localmente
git checkout 19.0-develop
git pull origin 19.0-develop

# 2. Volver a tu branch
git checkout feature/TASK-123-mi-feature

# 3. Merge develop en tu branch
git merge 19.0-develop

# 4. Resolver conflictos manualmente
# Editar archivos con conflictos
# Buscar marcadores: <<<<<<< HEAD

# 5. Marcar como resueltos
git add .
git commit -m "Merge develop and resolve conflicts"

# 6. Push
git push origin feature/TASK-123-mi-feature
```

### ¿Puedo hacer commits sin tests si es WIP?

**Sí**, pero:
- Márcalo claramente: `[WIP][módulo] descripción`
- NO crees PR hasta que tengas tests
- NO hagas push a branches protegidos

### ¿Qué hago si CI falla en mi PR?

1. Leer logs de CI en GitHub Actions
2. Reproducir el error localmente:
   ```bash
   # Ejecutar lo mismo que CI
   black --check addons/
   flake8 addons/
   pytest
   ```
3. Corregir el error
4. Commit y push
5. CI se ejecuta automáticamente de nuevo

### ¿Cuándo debo crear una CORE customization vs un addon?

**Crear addon si:**
- ✅ Puedes heredar el modelo sin modificar código original
- ✅ Es funcionalidad adicional, no modificación de existente
- ✅ Odoo vanilla funciona correctamente, solo agregas features

**Crear CORE customization si:**
- ⚠️ Odoo vanilla tiene un bug que afecta tu negocio
- ⚠️ Necesitas modificar lógica que no se puede overridear limpiamente
- ⚠️ El cambio debe aplicar a TODOS los módulos, no solo a tu addon

**Regla de oro:** Evitar CORE customizations siempre que sea posible.

### ¿Qué hago si necesito revertir un commit ya mergeado?

```bash
# Opción 1: Revert (crea un nuevo commit que deshace cambios)
git checkout 19.0-develop
git pull
git revert <commit-hash>
git push origin 19.0-develop

# Opción 2: Si NO se ha pusheado a production, y el commit es reciente
# Contactar a Tech Lead para evaluar git reset (peligroso)
```

### ¿Cómo manejo secretos y credenciales?

**🚫 NUNCA** commitear:
- Contraseñas
- API keys
- Tokens
- Archivos `.env`
- Certificados

**✅ Usar:**
- Variables de entorno
- GitHub Secrets (para CI/CD)
- Archivos `.env` en `.gitignore`
- Odoo config parameters (ir.config_parameter)

### ¿Qué hago si necesito hacer un cambio urgente pero no tengo aprobaciones?

1. **Evaluar severidad:**
   - ¿Es realmente crítico? (sistema caído, pérdida de dinero)
   - ¿Puede esperar 24h?

2. **Si es crítico:**
   - Notificar a Tech Lead por WhatsApp/llamada
   - Crear hotfix branch desde production
   - Tech Lead puede aprobar solo (excepción)
   - Documentar en post-mortem por qué fue crítico

3. **Si puede esperar:**
   - Seguir proceso normal
   - Pedir a reviewers que prioricen

---

## 15. Checklist de Implementación

### Para el Equipo

- [ ] Todos leyeron este documento
- [ ] Todos asistieron a workshops de capacitación
- [ ] Herramientas instaladas (pre-commit, Black, etc.)
- [ ] Branches protegidos configurados en GitHub
- [ ] Template de PR creado
- [ ] CI/CD pipeline funcionando
- [ ] Slack integrado con GitHub
- [ ] CORE_CUSTOMIZATIONS.md creado y poblado
- [ ] Scripts de ayuda en `scripts/` funcionando
- [ ] Métricas definidas y dashboard configurado
- [ ] Roles y responsabilidades claros
- [ ] Primera retrospectiva agendada (semana 12)

### Para Cada Developer

- [ ] Leí el documento completo
- [ ] Instalé pre-commit: `pre-commit install`
- [ ] Configuré Black en mi editor
- [ ] Sé cómo crear una feature branch
- [ ] Sé cómo escribir commits convencionales
- [ ] Sé cómo crear un PR con el template
- [ ] Sé cómo hacer code review
- [ ] Sé cómo escribir tests básicos
- [ ] Sé dónde encontrar ayuda (este doc, Tech Lead)

---

## 16. Recursos Adicionales

### Documentación

- [Git Flow Original](https://nvie.com/posts/a-successful-git-branching-model/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Odoo Testing](https://www.odoo.com/documentation/19.0/developer/reference/backend/testing.html)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Black Documentation](https://black.readthedocs.io/)

### Herramientas

- [GitHub](https://github.com)
- [GitLab](https://gitlab.com)
- [pre-commit](https://pre-commit.com/)
- [Codecov](https://codecov.io/)
- [Slack](https://slack.com)

### Comunidad Odoo

- [Odoo Community Association (OCA)](https://odoo-community.org/)
- [OCA Guidelines](https://github.com/OCA/maintainer-tools/blob/master/CONTRIBUTING.md)
- [OCA pylint-odoo](https://github.com/OCA/pylint-odoo)

---

## 17. Changelog del Documento

| Versión | Fecha | Cambios | Autor |
|---------|-------|---------|-------|
| 1.0 | 2025-10-07 | Documento inicial | Tech Lead |
| | | | |
| | | | |

---

**Última actualización:** 2025-10-07
**Versión:** 1.0
**Mantenido por:** Tech Lead
**Revisión programada:** Trimestral

---

**Este documento es un organismo vivo. Si encuentras mejoras, crea un PR actualizándolo. 🚀**
