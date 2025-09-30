# Plan de Implementación: CSV Completo con Referencias Cruzadas

## 🎯 **Objetivo Final**
Modificar el field_method_detector para que el CSV incluya todas las 179 referencias detectadas (primarias + cross-references + estados de validación) usando IDs secuenciales simples.

## 📋 **Plan de Implementación**

### **Fase 1: Modificar Estructura de Datos (2-3 días)**

#### **1.1 Actualizar RenameCandidate**
```python
@dataclass
class RenameCandidate:
    # Campos nuevos/modificados
    change_id: str = ""
    model: str = ""                  # Mantener campo existente
    change_scope: str = ""          # 'declaration', 'reference', 'call', 'super_call'
    impact_type: str = ""           # 'primary', 'self_reference', 'cross_model', etc.
    context: str = ""               # Contexto específico
    parent_change_id: str = ""      # Vinculación jerárquica
    validation_status: str = "pending"  # 'pending', 'approved', 'rejected', 'auto_approved'
    
    # Campos existentes (mantener compatibilidad)
    old_name: str
    new_name: str
    item_type: str
    module: str
    confidence: float
    signature_match: bool = False
    rule_applied: str = ""
    scoring_breakdown: dict = None
    file_path: str = ""
```

#### **1.2 Nuevo Enum para Estados**
```python
class ValidationStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved" 
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"

class ChangeScope(Enum):
    DECLARATION = "declaration"
    REFERENCE = "reference"
    CALL = "call"
    SUPER_CALL = "super_call"

class ImpactType(Enum):
    PRIMARY = "primary"
    SELF_REFERENCE = "self_reference"
    SELF_CALL = "self_call"
    CROSS_MODEL = "cross_model"
    CROSS_MODEL_CALL = "cross_model_call"
    INHERITANCE = "inheritance"
    DECORATOR = "decorator"
```

### **Fase 2: Expandir CrossReferenceAnalyzer (3-4 días)**

#### **2.1 Generar Todas las Referencias como RenameCandidate**
```python
class CrossReferenceAnalyzer:
    def generate_all_rename_candidates(self, primary_changes: list[RenameCandidate]) -> list[RenameCandidate]:
        """Convierte cambios primarios + todas sus referencias a RenameCandidate"""
        
        all_candidates = []
        change_id_counter = 1
        
        for primary_change in primary_changes:
            # 1. Asignar ID al cambio primario
            primary_change.change_id = str(change_id_counter)
            primary_change.change_scope = ChangeScope.DECLARATION.value
            primary_change.impact_type = ImpactType.PRIMARY.value
            primary_change.target_model = primary_change.model  # Migrar campo
            primary_change.context = ""
            primary_change.parent_change_id = ""
            primary_change.validation_status = ValidationStatus.PENDING.value
            
            all_candidates.append(primary_change)
            change_id_counter += 1
            
            # 2. Buscar todas las referencias cruzadas
            cross_references = self.find_all_cross_references(primary_change)
            
            # 3. Convertir cada referencia a RenameCandidate
            for reference in cross_references:
                impact_candidate = self._reference_to_candidate(
                    reference, 
                    primary_change, 
                    str(change_id_counter)
                )
                all_candidates.append(impact_candidate)
                change_id_counter += 1
        
        return all_candidates
    
    def _reference_to_candidate(self, reference: Reference, primary: RenameCandidate, change_id: str) -> RenameCandidate:
        """Convierte Reference a RenameCandidate"""
        
        return RenameCandidate(
            change_id=change_id,
            old_name=primary.old_name,
            new_name=primary.new_name,
            item_type=primary.item_type,
            module=reference.source_model.split('.')[0],  # Extraer módulo
            model=reference.target_model,
            change_scope=self._determine_change_scope(reference),
            impact_type=self._determine_impact_type(reference, primary),
            context=self._determine_context(reference),
            confidence=self._calculate_reference_confidence(reference, primary),
            parent_change_id=primary.change_id,
            validation_status=self._auto_validate(reference),
            file_path=reference.source_file,
            # Heredar del primario
            signature_match=primary.signature_match,
            rule_applied=primary.rule_applied
        )
```

#### **2.2 Lógica de Auto-Validación**
```python
def _auto_validate(self, reference: Reference) -> str:
    """Auto-aprueba referencias con alta confianza"""
    
    confidence = self._calculate_reference_confidence(reference)
    
    if confidence >= 0.90:
        return ValidationStatus.AUTO_APPROVED.value
    else:
        return ValidationStatus.PENDING.value
```

### **Fase 3: Modificar CSVManager (1-2 días)**

#### **3.1 Nuevo Header del CSV**
```python
class EnhancedCSVManager:
    CSV_HEADERS = [
        "change_id", "old_name", "new_name", "item_type", "module", 
        "model", "change_scope", "impact_type", "context", 
        "confidence", "parent_change_id", "validation_status"
    ]
    
    def write_enhanced_csv(self, all_candidates: list[RenameCandidate], filename: str):
        """Escribe todas las referencias con nueva estructura"""
        
        rows = []
        for candidate in all_candidates:
            row = {
                "change_id": candidate.change_id,
                "old_name": candidate.old_name,
                "new_name": candidate.new_name,
                "item_type": candidate.item_type,
                "module": candidate.module,
                "model": candidate.model,
                "change_scope": candidate.change_scope,
                "impact_type": candidate.impact_type,
                "context": candidate.context,
                "confidence": f"{candidate.confidence:.3f}",
                "parent_change_id": candidate.parent_change_id,
                "validation_status": candidate.validation_status
            }
            rows.append(row)
        
        # Escribir CSV
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=self.CSV_HEADERS)
            writer.writeheader()
            writer.writerows(rows)
    
    def read_enhanced_csv(self, filename: str) -> list[RenameCandidate]:
        """Lee CSV y reconstruye RenameCandidate"""
        
        candidates = []
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                candidate = RenameCandidate(
                    change_id=row['change_id'],
                    old_name=row['old_name'],
                    new_name=row['new_name'],
                    item_type=row['item_type'],
                    module=row['module'],
                    model=row['model'],
                    change_scope=row['change_scope'],
                    impact_type=row['impact_type'],
                    context=row['context'],
                    confidence=float(row['confidence']),
                    parent_change_id=row['parent_change_id'],
                    validation_status=row['validation_status']
                )
                candidates.append(candidate)
        
        return candidates
```

### **Fase 4: Modificar ValidationUI (2-3 días)**

#### **4.1 Validación que Actualiza CSV Directamente**
```python
class ValidationUI:
    def run_enhanced_validation_session(self, csv_filename: str):
        """Lee CSV, permite validación granular, actualiza estados"""
        
        # Leer CSV actual
        candidates = self.csv_manager.read_enhanced_csv(csv_filename)
        
        # Agrupar por declaración principal
        grouped = self._group_by_primary(candidates)
        
        print(f"\n🔍 VALIDACIÓN INTERACTIVA - {len(grouped)} cambios principales detectados")
        
        for primary_change, impacts in grouped.items():
            self._validate_change_group(primary_change, impacts, candidates)
        
        # Escribir CSV actualizado
        self.csv_manager.write_enhanced_csv(candidates, csv_filename)
        
        # Mostrar resumen final
        self._show_validation_summary(candidates)
    
    def _validate_change_group(self, primary: RenameCandidate, impacts: list[RenameCandidate], all_candidates: list[RenameCandidate]):
        """Valida un grupo de cambio primario + sus impactos"""
        
        print(f"\n📋 {primary.old_name} → {primary.new_name}")
        print(f"   📍 {primary.target_model} ({primary.module})")
        print(f"   📊 {len(impacts)} referencias encontradas")
        
        # Mostrar preview de referencias
        self._show_references_preview(impacts)
        
        choice = self._get_validation_choice([
            "(A)probar TODO (declaración + todas las referencias)",
            "(G)ranular (validar cada referencia individualmente)", 
            "(P)rimario solo (solo la declaración)",
            "(R)echazar todo",
            "(V)er detalles completos",
            "(S)altar (mantener pendiente)"
        ])
        
        if choice == 'A':  # Aprobar todo
            primary.validation_status = ValidationStatus.APPROVED.value
            for impact in impacts:
                impact.validation_status = ValidationStatus.APPROVED.value
                
        elif choice == 'G':  # Validación granular
            primary.validation_status = ValidationStatus.APPROVED.value
            self._validate_individual_impacts(impacts)
            
        elif choice == 'P':  # Solo primario
            primary.validation_status = ValidationStatus.APPROVED.value
            for impact in impacts:
                impact.validation_status = ValidationStatus.REJECTED.value
                
        elif choice == 'R':  # Rechazar todo
            primary.validation_status = ValidationStatus.REJECTED.value
            for impact in impacts:
                impact.validation_status = ValidationStatus.REJECTED.value
                
        elif choice == 'V':  # Ver detalles
            self._show_detailed_references(impacts)
            # Recursión para nueva decisión
            self._validate_change_group(primary, impacts, all_candidates)
        
        # 'S' = no cambiar estados (mantener pending)
```

#### **4.2 Validación Individual de Referencias**
```python
def _validate_individual_impacts(self, impacts: list[RenameCandidate]):
    """Valida cada referencia individualmente"""
    
    # Agrupar por tipo para mejor UX
    by_type = defaultdict(list)
    for impact in impacts:
        by_type[impact.impact_type].append(impact)
    
    for impact_type, group_impacts in by_type.items():
        print(f"\n  📂 {impact_type.replace('_', ' ').title()} ({len(group_impacts)} referencias)")
        
        for impact in group_impacts:
            self._show_impact_detail(impact)
            
            choice = self._get_validation_choice([
                f"(A)probar esta referencia (confianza: {impact.confidence:.2f})",
                "(R)echazar esta referencia",
                "(E)ditar nombre destino",
                "(S)altar (mantener pending)"
            ])
            
            if choice == 'A':
                impact.validation_status = ValidationStatus.APPROVED.value
            elif choice == 'R':
                impact.validation_status = ValidationStatus.REJECTED.value
            elif choice == 'E':
                new_name = input(f"Nuevo nombre para '{impact.old_name}': ")
                impact.new_name = new_name
                impact.validation_status = ValidationStatus.APPROVED.value
            # 'S' = mantener pending

def _show_impact_detail(self, impact: RenameCandidate):
    """Muestra detalle de una referencia específica"""
    
    print(f"    🎯 {impact.target_model} → {impact.context}")
    print(f"    📝 {impact.change_scope}: {impact.old_name} → {impact.new_name}")
    print(f"    📊 Confianza: {impact.confidence:.2f}")
    print(f"    📁 Archivo: {impact.file_path}")
```

### **Fase 5: Integrar con Pipeline Principal (1 día)**

#### **5.1 Modificar detect_field_method_changes.py**
```python
def main():
    # ... código existente hasta detectar cambios primarios ...
    
    # NUEVO: Expandir a todas las referencias cruzadas
    cross_ref_analyzer = CrossReferenceAnalyzer(all_models, inheritance_graph)
    all_candidates = cross_ref_analyzer.generate_all_rename_candidates(primary_changes)
    
    # Escribir CSV inicial con todas las referencias (status = pending/auto_approved)
    csv_manager = EnhancedCSVManager()
    csv_filename = "odoo_field_changes_detected.enhanced.csv"
    csv_manager.write_enhanced_csv(all_candidates, csv_filename)
    
    print(f"📊 Detección completa: {len(all_candidates)} referencias encontradas")
    print(f"💾 CSV generado: {csv_filename}")
    
    # Iniciar validación interactiva
    if input("¿Iniciar validación interactiva? (y/N): ").lower() == 'y':
        validation_ui = ValidationUI(csv_manager)
        validation_ui.run_validation_session(csv_filename)
    
    # Generar reporte final
    final_candidates = csv_manager.read_enhanced_csv(csv_filename)
    generate_final_report(final_candidates)

def generate_final_report(candidates: list[RenameCandidate]):
    """Genera reporte estadístico final"""
    
    total = len(candidates)
    approved = len([c for c in candidates if c.validation_status == ValidationStatus.APPROVED.value])
    auto_approved = len([c for c in candidates if c.validation_status == ValidationStatus.AUTO_APPROVED.value])
    rejected = len([c for c in candidates if c.validation_status == ValidationStatus.REJECTED.value])
    pending = len([c for c in candidates if c.validation_status == ValidationStatus.PENDING.value])
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              📊 RESUMEN FINAL                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

📈 Estadísticas:
   • Total detectado: {total}
   • Auto-aprobados: {auto_approved} (≥90% confianza)
   • Aprobados manualmente: {approved}
   • Rechazados: {rejected}
   • Pendientes: {pending}
   • TOTAL PARA APLICAR: {approved + auto_approved}

💾 Archivo completo: odoo_field_changes_detected.enhanced.csv
   (Incluye TODAS las referencias con estados de validación)
    """)
```

### **Fase 6: Testing y Validación (2-3 días)**

#### **6.1 Tests Unitarios**
```python
def test_enhanced_csv_structure():
    """Test que CSV contiene todas las columnas esperadas"""
    
def test_cross_reference_generation():
    """Test que se generan todas las referencias cruzadas"""
    
def test_validation_status_updates():
    """Test que validación actualiza estados correctamente"""
    
def test_hierarchical_relationships():
    """Test que parent_change_id vincula correctamente"""
```

#### **6.2 Test con Datos Reales**
- Ejecutar con módulos sale, purchase, stock
- Verificar que se detectan 179+ referencias
- Validar manualmente muestra aleatoria
- Confirmar que CSV es utilizable en Excel/LibreOffice

## 📅 **Cronograma**

| Fase | Duración | Dependencias |
|------|----------|--------------|
| Fase 1: Estructura de Datos | 2-3 días | - |
| Fase 2: CrossReferenceAnalyzer | 3-4 días | Fase 1 |
| Fase 3: CSVManager | 1-2 días | Fase 1 |
| Fase 4: ValidationUI | 2-3 días | Fase 1, 3 |
| Fase 5: Integración | 1 día | Fases 1-4 |
| Fase 6: Testing | 2-3 días | Fases 1-5 |

**Total: 11-16 días**

## 🎯 **Resultado Esperado**

### **Estructura CSV Final**
```csv
change_id,old_name,new_name,item_type,module,model,change_scope,impact_type,context,confidence,parent_change_id,validation_status
```

### **Ejemplo de Contenido**
```csv
change_id,old_name,new_name,item_type,module,model,change_scope,impact_type,context,confidence,parent_change_id,validation_status
1,amount_total,total_amount,field,sale,sale.order,declaration,primary,,0.95,,approved
2,amount_total,total_amount,field,sale,sale.order,reference,self_reference,_compute_tax,0.90,1,approved
3,amount_total,total_amount,field,sale,sale.order,reference,decorator,api.depends,0.85,1,approved
4,amount_total,total_amount,field,account,sale.order,reference,cross_model,create_from_sale,0.80,1,rejected
5,amount_total,total_amount,field,sale,sale.order,reference,xml_view,form_view,0.70,1,pending
6,amount_total,total_amount,field,sale,sale.order,reference,js_reference,widget,0.65,1,rejected
7,send_email,send_notification,method,sale,sale.order,declaration,primary,,0.95,,approved
8,send_email,send_notification,method,sale,sale.order,call,self_call,confirm_order,0.90,7,auto_approved
9,send_email,send_notification,method,sale,sale.order,super_call,inheritance,process_order,0.85,7,approved
```

## 🔑 **Beneficios Clave**

### **1. Trazabilidad Completa**
- Todas las 179 referencias detectadas preservadas en el CSV
- Relación padre-hijo clara via `parent_change_id`
- Estado de validación de cada referencia individual

### **2. Validación Granular**
- Opción de aprobar/rechazar referencias individualmente
- Auto-aprobación para alta confianza (≥90%)
- Capacidad de editar nombres durante validación

### **3. Análisis Post-Validación**
```python
# Estadísticas por tipo de impacto
df.groupby(['impact_type', 'validation_status']).size()

# Referencias con mayor tasa de rechazo
rejection_rate = df[df['validation_status'] == 'rejected'].groupby('impact_type').size()

# Cambios listos para aplicar
ready_to_apply = df[df['validation_status'].isin(['approved', 'auto_approved'])]
```

### **4. Formato Estándar**
- CSV compatible con Excel, LibreOffice, pandas
- Sin dependencias de archivos JSON adicionales
- Fácil importación en cualquier herramienta de análisis

## ⚠️ **Consideraciones de Implementación**

### **Compatibilidad hacia Atrás**
- Mantener soporte para formato CSV legacy durante transición
- Migración gradual de herramientas existentes
- Tests de regresión para funcionalidad actual

### **Performance**
- CSV significativamente más grande (179 vs 43 filas)
- Optimizar lectura/escritura para archivos grandes
- Considerar compresión para almacenamiento

### **Usabilidad**
- UI de validación debe ser intuitiva para 179 referencias
- Filtros y agrupaciones para manejar volumen
- Preview contextual para decisiones informadas

## 🏁 **Conclusión**

Este plan transforma el field_method_detector de un detector básico (43 declaraciones) a un analizador completo de impacto (179+ referencias) manteniendo:

- **Simplicidad**: IDs secuenciales simples (1, 2, 3...)
- **Completitud**: Todas las referencias detectadas preservadas
- **Flexibilidad**: Validación granular por referencia
- **Trazabilidad**: Estados de validación y relaciones jerárquicas
- **Estándar**: CSV como formato universal sin dependencias adicionales

**Resultado**: De ~30% de detección actual a ~85%+ con trazabilidad completa de decisiones de validación.