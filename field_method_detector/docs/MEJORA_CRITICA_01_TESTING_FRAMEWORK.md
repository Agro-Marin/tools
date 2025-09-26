# Mejora Crítica 1: Testing Framework

## 🎯 Objetivo
Implementar una suite completa de testing para asegurar la confiabilidad y facilitar el mantenimiento de la herramienta `field_method_detector`.

## 📊 Análisis del Estado Actual

### Problemas Identificados
- **Sin tests**: 0% de cobertura de código
- **Refactoring riesgoso**: Imposible hacer cambios con confianza
- **Detección de regresiones**: Manual y propensa a errores
- **Validación de reglas**: No hay verificación automatizada de naming rules
- **CI/CD**: Imposible implementar pipelines de calidad

### Impacto de la Falta de Tests
```python
# Ejemplo de riesgo actual:
def _find_field_renames(self, fields_before, fields_after, ...):
    # 100+ líneas de lógica compleja
    # ¿Qué pasa si cambio el threshold de 0.50 a 0.60?
    # ¿Rompe detecciones existentes? NO LO SABEMOS
```

## 🏗️ Arquitectura de Testing Propuesta

### Estructura de Directorios
```
field_method_detector/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Fixtures compartidas
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_ast_parser.py      # Tests unitarios AST
│   │   ├── test_matching_engine.py # Tests unitarios matching
│   │   ├── test_naming_rules.py    # Tests reglas nomenclatura
│   │   ├── test_git_analyzer.py    # Tests análisis Git
│   │   └── test_csv_manager.py     # Tests gestión CSV
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_full_pipeline.py   # Tests extremo a extremo
│   │   └── test_module_analysis.py # Tests análisis módulos
│   ├── fixtures/
│   │   ├── sample_python_code/     # Código Python de prueba
│   │   ├── sample_xml_files/       # XML de prueba
│   │   └── test_repositories/      # Repos Git de prueba
│   └── data/
│       ├── expected_outputs/       # Resultados esperados
│       └── test_configs/           # Configuraciones de prueba
├── pytest.ini                     # Configuración pytest
└── requirements-test.txt           # Dependencias testing
```

## 🚀 MVP: Enfoque Minimalista (1-2 días)

### ¿Por Qué Empezar con MVP?
Para obtener **beneficios inmediatos** con **mínimo esfuerzo**, implementaremos primero un sistema de testing básico usando casos reales estáticos. Este MVP detectará regresiones críticas desde el día 1.

### Estructura MVP Minimalista
```
field_method_detector/
├── tests/
│   ├── test_cases/
│   │   ├── case_qty_patterns.yml
│   │   ├── case_count_patterns.yml
│   │   └── case_compute_methods.yml
│   ├── test_real_cases.py
│   └── conftest.py
├── tools/
│   └── extract_real_case.py
└── pytest.ini
```

### Formato de Caso Estático
```yaml
# tests/test_cases/case_qty_patterns.yml
name: "qty_delivered_to_transfered"
description: "Quantity fields pattern migration from sale module"

# Diff estático extraído directamente de Git
diff: |
  --- a/models/sale_order.py
  +++ b/models/sale_order.py
  @@ -15,7 +15,7 @@ class SaleOrder(models.Model):
       _name = 'sale.order'
       
  -    qty_delivered = fields.Float(string="Delivered")
  +    qty_transfered = fields.Float(string="Delivered")
       
  -    def _compute_qty_delivered(self):
  +    def _compute_qty_transfered(self):
           pass

# Resultado esperado (extraído de ejecución real exitosa)
expected_output:
  - old_name: "qty_delivered"
    new_name: "qty_transfered" 
    item_type: "field"
    confidence_min: 0.85
  - old_name: "_compute_qty_delivered"
    new_name: "_compute_qty_transfered"
    item_type: "method"
    confidence_min: 0.95
```

### Test Runner Simple
```python
# tests/test_real_cases.py
import yaml
import tempfile
import subprocess
import csv
from pathlib import Path

class TestRealCases:
    """Tests basados en casos reales extraídos del proyecto"""
    
    def test_qty_patterns(self):
        """Test detección de patrones qty_* -> qty_transfered"""
        self._run_case("case_qty_patterns.yml")
    
    def test_count_patterns(self):
        """Test detección de patrones *_count -> count_*"""
        self._run_case("case_count_patterns.yml")
        
    def test_compute_methods(self):
        """Test detección de métodos compute renombrados"""
        self._run_case("case_compute_methods.yml")
        
    def _run_case(self, case_file):
        """Ejecuta un caso de prueba específico"""
        # 1. Cargar definición del caso
        case = self._load_case(case_file)
        
        # 2. Crear repositorio temporal con el diff
        repo_path = self._create_temp_repo_with_diff(case['diff'])
        
        # 3. Ejecutar field_method_detector
        result_csv = self._run_detector(repo_path)
        
        # 4. Verificar que detecta lo esperado
        self._assert_detections_match(result_csv, case['expected_output'])
        
        # 5. Cleanup
        self._cleanup_temp_repo(repo_path)
    
    def _create_temp_repo_with_diff(self, diff_content):
        """Crea repo Git temporal aplicando el diff"""
        temp_dir = tempfile.mkdtemp()
        
        # Extraer archivos "before" del diff
        self._extract_before_state(temp_dir, diff_content)
        
        # Crear commit inicial
        subprocess.run(['git', 'init'], cwd=temp_dir, check=True)
        subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True) 
        subprocess.run(['git', 'commit', '-m', 'Initial state'], cwd=temp_dir, check=True)
        
        # Aplicar diff para crear estado "after"
        self._apply_diff(temp_dir, diff_content)
        subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'After changes'], cwd=temp_dir, check=True)
        
        return temp_dir
    
    def _run_detector(self, repo_path):
        """Ejecuta field_method_detector en el repo temporal"""
        output_csv = f"{repo_path}/test_output.csv"
        
        # Obtener commits del repo temporal
        result = subprocess.run(['git', 'rev-list', '--reverse', 'HEAD'], 
                              cwd=repo_path, capture_output=True, text=True, check=True)
        commits = result.stdout.strip().split('\n')
        
        # Ejecutar detector entre primer y último commit
        cmd = [
            'python', 'main.py',
            '--repo', repo_path,
            '--commit-before', commits[0],
            '--commit-after', commits[1], 
            '--output', output_csv
        ]
        subprocess.run(cmd, check=True)
        
        return output_csv
    
    def _assert_detections_match(self, result_csv, expected):
        """Verifica que las detecciones coincidan con lo esperado"""
        with open(result_csv, 'r') as f:
            reader = csv.DictReader(f)
            detections = list(reader)
        
        # Verificar que se detectaron todos los casos esperados
        for expected_item in expected:
            matching_detection = None
            for detection in detections:
                if (detection['old_name'] == expected_item['old_name'] and
                    detection['new_name'] == expected_item['new_name'] and
                    detection['item_type'] == expected_item['item_type']):
                    matching_detection = detection
                    break
            
            assert matching_detection is not None, f"No se detectó: {expected_item}"
            
            # Verificar nivel de confianza mínimo
            confidence = float(matching_detection.get('confidence', 0))
            min_confidence = expected_item.get('confidence_min', 0.8)
            assert confidence >= min_confidence, f"Confianza baja: {confidence} < {min_confidence}"
```

### Script de Extracción de Casos
```python
# tools/extract_real_case.py
#!/usr/bin/env python3
"""Extrae casos de prueba desde commits Git reales"""

import subprocess
import yaml
import argparse
import csv
import sys

def extract_case_from_commits(commit_before, commit_after, case_name, output_file):
    """Extrae un caso real desde commits Git existentes"""
    
    print(f"Extrayendo caso desde {commit_before} a {commit_after}...")
    
    # 1. Obtener diff entre commits
    try:
        diff_result = subprocess.run([
            'git', 'diff', f"{commit_before}..{commit_after}"
        ], capture_output=True, text=True, check=True)
        diff_content = diff_result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error obteniendo diff: {e}")
        sys.exit(1)
    
    # 2. Ejecutar detector en esos commits para obtener expected output
    try:
        detector_result = subprocess.run([
            'python', 'main.py',
            '--commit-before', commit_before,
            '--commit-after', commit_after,
            '--output', '/tmp/extract_output.csv'
        ], capture_output=True, text=True, check=True)
        
        # Parsear CSV resultado
        expected_output = []
        with open('/tmp/extract_output.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                expected_output.append({
                    'old_name': row['old_name'],
                    'new_name': row['new_name'],
                    'item_type': row['item_type'],
                    'confidence_min': max(0.8, float(row.get('confidence', 0.8)) - 0.05)
                })
                
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando detector: {e}")
        sys.exit(1)
    
    # 3. Crear estructura del caso
    case_data = {
        'name': case_name,
        'description': f"Real case extracted from commits {commit_before[:7]}..{commit_after[:7]}",
        'source_commits': {
            'before': commit_before,
            'after': commit_after
        },
        'diff': diff_content,
        'expected_output': expected_output
    }
    
    # 4. Guardar archivo YAML
    with open(output_file, 'w') as f:
        yaml.dump(case_data, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ Caso extraído: {output_file}")
    print(f"   - {len(expected_output)} detecciones esperadas")
    print(f"   - Diff: {len(diff_content.splitlines())} líneas")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrae casos de prueba desde commits Git")
    parser.add_argument("--before", required=True, help="Commit antes de los cambios")
    parser.add_argument("--after", required=True, help="Commit después de los cambios")
    parser.add_argument("--name", required=True, help="Nombre descriptivo del caso")
    parser.add_argument("--output", required=True, help="Archivo de salida (.yml)")
    
    args = parser.parse_args()
    extract_case_from_commits(args.before, args.after, args.name, args.output)
```

### Configuración Pytest Mínima
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = 
    --tb=short
    -v
markers =
    mvp: Tests del MVP minimalista
```

### Uso del MVP

#### Extraer casos desde commits conocidos:
```bash
# Extraer caso de qty patterns
python tools/extract_real_case.py \
  --before 7c142414 \
  --after 0c2db5f5 \
  --name "qty_patterns_migration" \
  --output tests/test_cases/case_qty_patterns.yml

# Extraer caso de count patterns  
python tools/extract_real_case.py \
  --before 8b5d3bff \
  --after e9a7e669 \
  --name "count_patterns_migration" \
  --output tests/test_cases/case_count_patterns.yml
```

#### Ejecutar suite MVP:
```bash
# Instalar dependencias mínimas
pip install pytest pyyaml

# Ejecutar tests
pytest tests/test_real_cases.py -v -m mvp

# Output esperado:
# tests/test_real_cases.py::test_qty_patterns PASSED
# tests/test_real_cases.py::test_count_patterns PASSED  
# tests/test_real_cases.py::test_compute_methods PASSED
```

### Beneficios del MVP (1-2 días implementación)

1. **Detección inmediata de regresiones** en patrones críticos
2. **Casos basados en datos reales** del proyecto actual
3. **Fácil adición de nuevos casos** cuando se encuentren bugs
4. **Base sólida** para evolucionar hacia testing completo
5. **ROI inmediato** con mínima inversión

### Evolución del MVP

```
Día 1-2:  MVP funcional con 3-5 casos críticos
Semana 2: Añadir 10-15 casos más desde CSV existente  
Semana 3: Evolucionar hacia testing unitario completo
Mes 2:    Sistema completo como se describe abajo
```

---

## 📋 Plan de Implementación Completo (Post-MVP)

### Fase 1: Setup Base (2-3 días)

#### 1.1 Configuración Inicial
```bash
# Instalar dependencias
pip install pytest pytest-cov pytest-mock pytest-xdist

# Crear estructura de directorios
mkdir -p tests/{unit,integration,fixtures,data}
```

#### 1.2 Archivo `pytest.ini`
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --disable-warnings
    --cov=.
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Pruebas unitarias
    integration: Pruebas de integración
    slow: Pruebas que tardan más de 1 segundo
```

#### 1.3 Fixtures Base (`conftest.py`)
```python
import pytest
import tempfile
import shutil
from pathlib import Path
from analyzers.ast_parser import CodeInventoryExtractor
from analyzers.matching_engine import MatchingEngine
from config.naming_rules import naming_engine

@pytest.fixture
def sample_python_code():
    """Código Python de muestra para testing"""
    return '''
from odoo import models, fields, api

class SaleOrder(models.Model):
    _name = 'sale.order'
    
    # Field que será renombrado
    delivery_count = fields.Integer(string="Deliveries")
    
    @api.depends('order_line')
    def _compute_delivery_count(self):
        for record in self:
            record.delivery_count = len(record.picking_ids)
    '''

@pytest.fixture
def temp_git_repo():
    """Repositorio Git temporal para testing"""
    temp_dir = tempfile.mkdtemp()
    # Setup git repo with commits
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def extractor():
    return CodeInventoryExtractor()

@pytest.fixture
def matching_engine():
    return MatchingEngine()
```

### Fase 2: Tests Unitarios Críticos (3-4 días)

#### 2.1 Tests AST Parser (`test_ast_parser.py`)
```python
class TestOdooASTVisitor:
    def test_extract_field_basic(self, extractor):
        """Test extracción básica de campos"""
        code = '''
from odoo import fields, models
class TestModel(models.Model):
    _name = 'test.model'
    my_field = fields.Char(string="Test Field")
'''
        inventory = extractor.extract_python_inventory(code, "test.py")
        
        assert len(inventory["fields"]) == 1
        field = inventory["fields"][0]
        assert field["name"] == "my_field"
        assert field["field_type"] == "Char"
        assert "Test Field" in field["signature"]

    def test_extract_method_with_decorators(self, extractor):
        """Test extracción de métodos con decoradores"""
        code = '''
class TestModel(models.Model):
    _name = 'test.model'
    
    @api.depends('line_ids')
    def _compute_total(self, param1, param2="default"):
        pass
'''
        inventory = extractor.extract_python_inventory(code, "test.py")
        
        assert len(inventory["methods"]) == 1
        method = inventory["methods"][0]
        assert method["name"] == "_compute_total"
        assert "api.depends" in method["decorators"]
        assert "param1" in method["args"]
        assert "param2" in method["args"]
        
    def test_signature_generation_consistency(self, extractor):
        """Test consistencia en generación de signatures"""
        # Mismo campo definido de formas diferentes
        code1 = 'field1 = fields.Char(string="Test", required=True)'
        code2 = 'field2 = fields.Char(required=True, string="Test")'
        
        # Ambos deberían generar signatures equivalentes
        # para detectar que son el "mismo" campo
```

#### 2.2 Tests Matching Engine (`test_matching_engine.py`)
```python
class TestMatchingEngine:
    def test_find_exact_field_rename(self, matching_engine):
        """Test detección de rename exacto de campo"""
        before = [{
            "name": "delivery_count",
            "field_type": "Integer", 
            "signature": "Integer(string='Deliveries')",
            "model": "sale.order"
        }]
        
        after = [{
            "name": "transfer_count", 
            "field_type": "Integer",
            "signature": "Integer(string='Deliveries')",
            "model": "sale.order"
        }]
        
        candidates = matching_engine._find_field_renames(
            before, after, "sale", "models/sale.py"
        )
        
        assert len(candidates) == 1
        candidate = candidates[0]
        assert candidate.old_name == "delivery_count"
        assert candidate.new_name == "transfer_count"
        assert candidate.signature_match == True
        assert candidate.confidence > 0.8

    def test_disambiguate_multiple_matches(self, matching_engine):
        """Test desambiguación cuando hay múltiples matches"""
        before = [{
            "name": "qty_delivered",
            "signature": "Float()",
            "model": "sale.order"
        }]
        
        # Dos candidatos con misma signature
        after = [
            {"name": "qty_transfered", "signature": "Float()", "model": "sale.order"},
            {"name": "qty_processed", "signature": "Float()", "model": "sale.order"}
        ]
        
        candidates = matching_engine._find_field_renames(
            before, after, "sale", "models/sale.py"
        )
        
        # Debería elegir qty_transfered por naming rules
        assert len(candidates) == 1
        assert candidates[0].new_name == "qty_transfered"
```

#### 2.3 Tests Naming Rules (`test_naming_rules.py`)
```python
class TestNamingRules:
    def test_delivery_to_transfer_rule(self):
        """Test regla específica delivery->transfer"""
        result = naming_engine.validate_rename(
            old_name="delivery_count",
            new_name="transfer_count", 
            item_type="field"
        )
        
        assert result["confidence"] > 0.8
        assert "delivery_transfer" in result["rule_applied"]
        
    def test_compute_method_rule(self):
        """Test regla para métodos compute"""
        result = naming_engine.validate_rename(
            old_name="_compute_qty_received",
            new_name="_compute_qty_transfered",
            item_type="method",
            decorators=["@api.depends"]
        )
        
        assert result["confidence"] == 1.0
        assert result["rule_applied"] is not None

    def test_scoring_breakdown(self):
        """Test desglose detallado del scoring"""
        result = naming_engine.validate_rename(
            old_name="delivery_method",
            new_name="transfer_method",
            item_type="field"
        )
        
        breakdown = result["scoring_breakdown"]
        assert "pattern_match" in breakdown
        assert "context_consistency" in breakdown
        assert isinstance(breakdown["pattern_match"], float)
```

### Fase 3: Tests de Integración (2-3 días)

#### 3.1 Test Pipeline Completo (`test_full_pipeline.py`)
```python
class TestFullPipeline:
    @pytest.fixture
    def test_git_repo(self):
        """Repo git con cambios reales de renombrado"""
        # Crear repo temporal con 2 commits:
        # - Commit 1: código original
        # - Commit 2: campos/métodos renombrados
        pass
        
    def test_end_to_end_detection(self, test_git_repo):
        """Test completo desde Git hasta CSV"""
        # Ejecutar el pipeline completo
        # Verificar que detecta los renames esperados
        pass
        
    def test_confidence_thresholds(self):
        """Test diferentes umbrales de confianza"""
        # Verificar que different thresholds filtran correctamente
        pass
```

#### 3.2 Tests de Rendimiento
```python
@pytest.mark.slow
class TestPerformance:
    def test_large_module_analysis(self):
        """Test análisis de módulo grande (100+ archivos)"""
        # Verificar que no excede timeouts
        # Verificar uso de memoria
        pass
        
    def test_concurrent_analysis(self):
        """Test análisis concurrente múltiples módulos"""
        pass
```

### Fase 4: Tests de Regresión (1-2 días)

#### 4.1 Test Suite de Casos Conocidos
```python
class TestRegressionSuite:
    """Tests basados en casos reales encontrados en producción"""
    
    def test_known_delivery_transfers(self):
        """Test casos conocidos de delivery->transfer"""
        # Usar datos reales anonimizados
        pass
        
    def test_edge_cases(self):
        """Test casos edge documentados"""
        pass
```

## 🔧 Herramientas y Configuración

### Dependencias Testing
```txt
# requirements-test.txt
pytest>=7.0
pytest-cov>=4.0
pytest-mock>=3.10
pytest-xdist>=3.0     # Ejecución paralela
pytest-html>=3.1      # Reportes HTML
pytest-benchmark>=4.0 # Performance testing
freezegun>=1.2         # Mock de fechas/tiempos
responses>=0.22        # Mock de requests HTTP
```

### GitHub Actions CI
```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: pytest --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 📊 Métricas de Éxito

### Cobertura Objetivo
- **Cobertura global**: >80%
- **Componentes críticos**: >95%
  - `matching_engine.py`
  - `ast_parser.py`  
  - `naming_rules.py`

### Performance Benchmarks
- **Tests unitarios**: <5 segundos total
- **Tests integración**: <30 segundos total
- **Memory usage**: <500MB durante tests

### Calidad de Tests
- **Mutation testing**: >70% mutation score
- **Edge case coverage**: 100% de casos conocidos
- **Documentation**: Cada test documentado con propósito claro

## ⚡ Beneficios Inmediatos

1. **Detección Temprana de Bugs**: Tests catches issues before production
2. **Refactoring Seguro**: Confidence para mejorar código existente  
3. **Documentación Viva**: Tests sirven como especificación
4. **Onboarding**: Nuevos desarrolladores entienden comportamiento esperado
5. **CI/CD Ready**: Foundation para automated deployments

## 🚀 Roadmap de Ejecución

### Enfoque MVP-First

#### Día 1-2: MVP Minimalista ⭐ **EMPEZAR AQUÍ**
- [ ] Implementar `test_real_cases.py` básico
- [ ] Crear `tools/extract_real_case.py`  
- [ ] Extraer 3-5 casos críticos desde commits conocidos
- [ ] Configuración pytest mínima
- [ ] **Resultado**: Detección de regresiones inmediata

#### Semana 2: Expansión MVP
- [ ] Extraer 10-15 casos más desde CSV existente
- [ ] Automatizar extracción de casos
- [ ] Añadir validaciones de confianza más estrictas
- [ ] **Resultado**: Cobertura de casos reales >80%

#### Semana 3-4: Testing Unitario Completo
- [ ] Setup estructura testing completa
- [ ] Tests unitarios AST parser  
- [ ] Tests unitarios Matching Engine
- [ ] Tests Naming Rules
- [ ] **Resultado**: Cobertura código >60%

#### Mes 2: Integration & Polish
- [ ] Tests integración end-to-end
- [ ] Performance tests
- [ ] CI/CD integration
- [ ] **Resultado**: Suite completa, cobertura >80%

### Comparación de Enfoques

| Aspecto | MVP (1-2 días) | Completo (15-20 días) |
|---------|----------------|----------------------|
| **Tiempo inversión** | 1-2 días | 15-20 días |
| **Detección regresiones** | ✅ Inmediata | ✅ Completa |
| **Casos reales** | ✅ 3-5 críticos | ✅ Exhaustivos |
| **Cobertura código** | ❌ 0% | ✅ >80% |
| **Tests unitarios** | ❌ No | ✅ Completos |
| **CI/CD ready** | ⚠️ Básico | ✅ Profesional |
| **ROI inmediato** | ✅ Alto | ⚠️ Diferido |

### Recomendación: **Implementar MVP primero**

El MVP te dará:
- **Protección inmediata** contra regresiones críticas
- **Validación del concepto** con esfuerzo mínimo  
- **Base sólida** para evolución incremental
- **Confianza** para refactorizar desde el día 1

**Tiempo Total Estimado**: 
- **MVP**: 1-2 días (ROI inmediato)
- **Sistema Completo**: 15-20 días (ROI diferido)
- **Enfoque Recomendado**: MVP → Incremental → Completo

**ROI**: Crítico - protección inmediata con mínima inversión
**Riesgo**: Muy Bajo - solo agrega funcionalidad, no modifica existente