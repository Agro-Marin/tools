# Ejemplos Prácticos - Field Method Renaming Tool

## Casos de Uso Reales

Este documento presenta ejemplos prácticos basados en casos reales de renombrado de campos y métodos en Odoo.

## Ejemplo 1: Renombrado de Campo Simple

### Contexto
Cambiar `quotations_count` a `count_quotations` en el modelo `crm.team` del módulo `sale`.

### CSV de Entrada
```csv
old_name,new_name,module,model
quotations_count,count_quotations,sale,crm.team
```

### Archivos Afectados

#### 1. Modelo (`models/crm_team.py`)
**Antes:**
```python
class CrmTeam(models.Model):
    _inherit = 'crm.team'
    
    quotations_count = fields.Integer(
        string='Number of Quotations',
        compute='_compute_quotations_count'
    )
    
    @api.depends('member_ids.quotation_ids')
    def _compute_quotations_count(self):
        for team in self:
            team.quotations_count = len(team.member_ids.mapped('quotation_ids'))
```

**Después:**
```python
class CrmTeam(models.Model):
    _inherit = 'crm.team'
    
    count_quotations = fields.Integer(
        string='Number of Quotations',
        compute='_compute_count_quotations'
    )
    
    @api.depends('member_ids.quotation_ids')
    def _compute_count_quotations(self):
        for team in self:
            team.count_quotations = len(team.member_ids.mapped('quotation_ids'))
```

#### 2. Vista (`views/crm_team_views.xml`)
**Antes:**
```xml
<record id="crm_team_form_view" model="ir.ui.view">
    <field name="model">crm.team</field>
    <field name="arch" type="xml">
        <form>
            <sheet>
                <div class="oe_button_box">
                    <button name="action_view_quotations" type="object"
                            class="oe_stat_button" icon="fa-file-text-o">
                        <field name="quotations_count" widget="statinfo" 
                               string="Quotations"/>
                    </button>
                </div>
                <field name="quotations_count" invisible="1"/>
            </sheet>
        </form>
    </field>
</record>
```

**Después:**
```xml
<record id="crm_team_form_view" model="ir.ui.view">
    <field name="model">crm.team</field>
    <field name="arch" type="xml">
        <form>
            <sheet>
                <div class="oe_button_box">
                    <button name="action_view_quotations" type="object"
                            class="oe_stat_button" icon="fa-file-text-o">
                        <field name="count_quotations" widget="statinfo" 
                               string="Quotations"/>
                    </button>
                </div>
                <field name="count_quotations" invisible="1"/>
            </sheet>
        </form>
    </field>
</record>
```

### Comando Ejecutado
```bash
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /home/user/odoo \
    --module sale \
    --verbose
```

### Resultado
```
🔍 Procesando cambios para módulo 'sale'...
📁 Archivos encontrados:
   - models/crm_team.py
   - views/crm_team_views.xml

🔄 Aplicando cambios:
   ✅ models/crm_team.py: quotations_count → count_quotations (2 occurrences)
   ✅ views/crm_team_views.xml: quotations_count → count_quotations (2 occurrences)

💾 Respaldos creados en: .backups/20240117_143052/
✅ Cambios aplicados exitosamente
```

## Ejemplo 2: Renombrado de Método

### Contexto
Cambiar `action_quotation_send` a `action_send_quotation` en el modelo `sale.order`.

### CSV de Entrada
```csv
old_name,new_name,module,model
action_quotation_send,action_send_quotation,sale,sale.order
```

### Archivos Afectados

#### 1. Modelo (`models/sale_order.py`)
**Antes:**
```python
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def action_quotation_send(self):
        """Send quotation by email"""
        self.ensure_one()
        template = self.env.ref('sale.email_template_edi_sale')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'context': {
                'default_template_id': template.id,
                'default_res_id': self.id,
            }
        }
```

**Después:**
```python
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def action_send_quotation(self):
        """Send quotation by email"""
        self.ensure_one()
        template = self.env.ref('sale.email_template_edi_sale')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'context': {
                'default_template_id': template.id,
                'default_res_id': self.id,
            }
        }
```

#### 2. Vista (`views/sale_order_views.xml`)
**Antes:**
```xml
<record id="view_order_form" model="ir.ui.view">
    <field name="arch" type="xml">
        <form>
            <header>
                <button name="action_quotation_send" 
                        string="Send by Email" 
                        type="object"
                        states="draft,sent"
                        class="btn-primary"/>
            </header>
        </form>
    </field>
</record>
```

**Después:**
```xml
<record id="view_order_form" model="ir.ui.view">
    <field name="arch" type="xml">
        <form>
            <header>
                <button name="action_send_quotation" 
                        string="Send by Email" 
                        type="object"
                        states="draft,sent"
                        class="btn-primary"/>
            </header>
        </form>
    </field>
</record>
```

#### 3. Template (`templates/sale_order_templates.xml`)
**Antes:**
```xml
<template id="quotation_template">
    <div class="quotation-actions">
        <a t-att-href="'/web#action=sale.action_quotations&amp;model=sale.order&amp;view_type=form&amp;res_id=%s' % order.id"
           class="btn btn-primary">
           <t t-call="action_quotation_send"/>
        </a>
    </div>
</template>
```

**Después:**
```xml
<template id="quotation_template">
    <div class="quotation-actions">
        <a t-att-href="'/web#action=sale.action_quotations&amp;model=sale.order&amp;view_type=form&amp;res_id=%s' % order.id"
           class="btn btn-primary">
           <t t-call="action_send_quotation"/>
        </a>
    </div>
</template>
```

## Ejemplo 3: Múltiples Cambios en un Módulo

### Contexto
Aplicar múltiples cambios en el módulo `sale` siguiendo las nuevas convenciones de naming.

### CSV de Entrada
```csv
old_name,new_name,module,model
quotations_count,count_quotations,sale,crm.team
quotations_amount,amount_quotations,sale,crm.team
commitment_date,date_commitment,sale,sale.order
validity_date,date_validity,sale,sale.order
action_quotation_send,action_send_quotation,sale,sale.order
```

### Comando con Modo Interactivo
```bash
python apply_field_method_changes.py \
    --csv-file multiple_changes.csv \
    --repo-path /home/user/odoo \
    --module sale \
    --interactive
```

### Sesión Interactiva
```
🔍 Procesando 5 cambios para módulo 'sale'...

📝 Cambio 1/5:
   Archivo: models/crm_team.py
   Tipo: Campo
   quotations_count → count_quotations en crm.team
   
   Línea 15: quotations_count = fields.Integer(
   Línea 20: def _compute_quotations_count(self):
   
¿Aplicar este cambio? [y/N/s/q]: y
✅ Aplicado

📝 Cambio 2/5:
   Archivo: models/crm_team.py  
   Tipo: Campo
   quotations_amount → amount_quotations en crm.team
   
¿Aplicar este cambio? [y/N/s/q]: y
✅ Aplicado

📝 Cambio 3/5:
   Archivo: models/sale_order.py
   Tipo: Campo
   commitment_date → date_commitment en sale.order
   
¿Aplicar este cambio? [y/N/s/q]: y
✅ Aplicado

📝 Cambio 4/5:
   Archivo: models/sale_order.py
   Tipo: Campo  
   validity_date → date_validity en sale.order
   
¿Aplicar este cambio? [y/N/s/q]: y
✅ Aplicado

📝 Cambio 5/5:
   Archivo: models/sale_order.py
   Tipo: Método
   action_quotation_send → action_send_quotation en sale.order
   
   También afectará:
   - views/sale_order_views.xml (1 referencia)
   - templates/sale_order_templates.xml (1 referencia)
   
¿Aplicar este cambio? [y/N/s/q]: y
✅ Aplicado

📊 Resumen:
   ✅ 5/5 cambios aplicados
   📁 6 archivos modificados
   💾 6 respaldos creados
```

## Ejemplo 4: Procesamiento Solo de Vistas

### Contexto
Aplicar cambios únicamente en archivos de vistas, sin modificar código Python.

### Comando
```bash
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /home/user/odoo \
    --file-types views \
    --dry-run
```

### Resultado (Dry-run)
```
🔍 Modo DRY-RUN: Simulando cambios...
📁 Tipos de archivo seleccionados: views

📊 Análisis:
   📂 sale/views/crm_team_views.xml:
      - quotations_count → count_quotations (2 referencias)
      - quotations_amount → amount_quotations (1 referencia)
   
   📂 sale/views/sale_order_views.xml:
      - commitment_date → date_commitment (3 referencias)
      - validity_date → date_validity (2 referencias)
      - action_quotation_send → action_send_quotation (1 referencia)

⚠️  Nota: No se modificarán archivos Python. 
   Esto puede causar inconsistencias si los campos/métodos 
   no existen con los nuevos nombres.

💡 Sugerencia: Ejecutar primero cambios en archivos Python
```

## Ejemplo 5: Manejo de Errores

### Caso: Error de Sintaxis

#### Archivo Problemático (`models/sale_order.py`)
```python
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # Sintaxis inválida intencionalmente
    commitment_date = fields.Date(
        string='Commitment Date'
        # Falta coma aquí
        help='Expected delivery date'
    )
```

#### Comando
```bash
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /home/user/odoo \
    --verbose
```

#### Resultado
```
🔍 Procesando cambios...

❌ Error en models/sale_order.py:
   Sintaxis Python inválida en archivo original
   
   SyntaxError: invalid syntax (line 7)
   
🔄 Acciones tomadas:
   ⏭️  Saltando archivo models/sale_order.py
   ✅ Continuando con otros archivos...
   
📊 Resumen:
   ✅ 3/4 archivos procesados exitosamente
   ❌ 1 archivo saltado por errores
   
📝 Ver log detallado en: field_method_renaming.log
```

### Caso: Archivo No Encontrado

#### Estructura de Módulo No Estándar
```
custom_module/
├── model/          # ❌ Debería ser 'models'
│   └── custom.py
├── wizard/         # ✅ Directorio wizard (singular) válido
│   └── custom_wizard.py
└── view/           # ❌ Debería ser 'views'  
    └── custom.xml
```

#### Resultado
```
⚠️  No se encontraron archivos siguiendo convenciones OCA para custom.model

🔍 Búsqueda fallback activada...
   📁 Encontrado: model/custom.py
   📁 Encontrado: wizard/custom_wizard.py
   📁 Encontrado: view/custom.xml

✅ Archivos localizados usando búsqueda recursiva
   Sugerencia: Considerar reorganizar según convenciones OCA
```

## Ejemplo 6: Integración con Git

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Verificando cambios de campos/métodos..."

# Buscar si hay cambios pendientes en CSV
if [ -f "tools/field_changes_pending.csv" ]; then
    echo "❌ Hay cambios de campos pendientes de aplicar"
    echo "Ejecute: python apply_field_method_changes.py --csv-file tools/field_changes_pending.csv"
    exit 1
fi

echo "✅ No hay cambios de campos pendientes"
```

### Workflow de CI/CD
```yaml
# .github/workflows/field-renaming.yml
name: Apply Field Renamings

on:
  push:
    paths:
      - 'tools/field_changes_*.csv'

jobs:
  apply-renamings:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
          
      - name: Apply Field Changes
        run: |
          python tools/field_method_renaming/apply_field_method_changes.py \
            --csv-file tools/field_changes_detected.csv \
            --repo-path . \
            --no-backup \
            --file-types python views
            
      - name: Commit Changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add .
          git commit -m "🤖 Apply automatic field/method renamings" || exit 0
          git push
```

## Ejemplo 7: Configuración Personalizada

### Archivo de Configuración Avanzada
```python
# config/custom_renaming_config.py

class CustomRenamingConfig:
    # Patrones adicionales para archivos específicos
    CUSTOM_XML_PATTERNS = {
        'field': [
            r'data-field=["\']({old_name})["\']',      # Atributos personalizados
            r'#{model}\.({old_name})',                  # Referencias en JS
        ],
        'method': [
            r'onclick=["\']({old_name})\(\)["\']',     # Llamadas en onclick
        ]
    }
    
    # Directorios adicionales para buscar
    ADDITIONAL_SEARCH_PATHS = [
        'static/src/js/',
        'static/src/xml/',
        'wizard/',     # Directorio wizard (singular)
        'wizards/',    # Directorio wizards (plural)
    ]
    
    # Filtros de archivos
    EXCLUDE_PATTERNS = [
        '*/migrations/*',
        '*/tests/*',
        '*/__pycache__/*',
    ]
    
    # Configuración de respaldos
    BACKUP_CONFIG = {
        'enabled': True,
        'retention_days': 30,
        'compress': True,
        'separate_by_module': True,
    }
```

### Uso con Configuración Personalizada
```bash
python apply_field_method_changes.py \
    --csv-file changes.csv \
    --repo-path /home/user/odoo \
    --config config/custom_renaming_config.py \
    --include-js \
    --verbose
```

## Mejores Prácticas

### 1. Preparación
- ✅ Siempre crear respaldo del repositorio antes de ejecutar
- ✅ Revisar CSV en modo `--dry-run` primero
- ✅ Usar modo `--interactive` para cambios críticos

### 2. Validación
- ✅ Ejecutar tests después de aplicar cambios
- ✅ Verificar que las vistas se rendericen correctamente
- ✅ Comprobar que no se rompan dependencias entre módulos

### 3. Rollback
```bash
# Si algo sale mal, restaurar desde respaldo
python restore_backup.py --backup-dir .backups/20240117_143052
```

### 4. Documentación
- 📝 Documentar razones para los cambios
- 📝 Mantener changelog de renamings aplicados
- 📝 Notificar a equipo sobre cambios en APIs públicas