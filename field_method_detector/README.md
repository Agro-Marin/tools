# Field Method Detector

[![OCA](https://img.shields.io/badge/OCA-Compatible-green.svg)](https://odoo-community.org/)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)

## Descripción General

La herramienta **Field Method Detector** es una utilidad especializada para detectar automáticamente campos y métodos renombrados en módulos de Odoo entre diferentes commits de Git. Utiliza análisis de árbol de sintaxis abstracta (AST) para proporcionar un análisis de código robusto y preciso.

### Propósito Principal

- Identificar campos y métodos que han sido renombrados en el código fuente de Odoo
- Facilitar la migración y actualización de módulos
- Generar reportes estructurados de cambios para revisión
- Proporcionar validación manual interactiva para cambios detectados

## Arquitectura del Proyecto

### Estructura Completa del Código

```
field_method_detector/
├── __init__.py                          # Inicialización del paquete
├── detect_field_method_changes.py       # Script principal de ejecución
├── analyzers/                           # Motor de Análisis
│   ├── __init__.py
│   ├── ast_visitor.py                   # Parser AST - Extrae definiciones de campos/métodos
│   ├── cross_reference_analyzer.py      # Encuentra referencias cruzadas en todo el codebase
│   ├── git_analyzer.py                  # Compara archivos entre commits de Git
│   └── matching_engine.py               # Empareja campos/métodos usando heurísticas
├── core/                                # Lógica Central del Sistema
│   ├── __init__.py
│   ├── models.py                        # Estructuras de datos (FieldInfo, MethodInfo, ChangeRecord)
│   ├── model_registry.py                # Registro de modelos Odoo y sus relaciones
│   ├── inheritance_graph.py             # Mapea herencia entre modelos (_inherit, _inherits)
│   └── model_flattener.py               # Resuelve herencia para vista completa de modelos
├── config/                              # Configuración del Sistema
│   ├── __init__.py
│   ├── naming_rules.py                  # Reglas para detectar patrones de renombrado
│   └── settings.py                      # Configuración general (rutas, filtros, umbrales)
├── interactive/                         # Interfaz de Usuario
│   ├── __init__.py
│   └── validation_ui.py                 # UI para validación manual de cambios
├── utils/                               # Utilidades de Soporte
│   ├── __init__.py
│   ├── csv_manager.py                   # Maneja lectura/escritura del CSV de salida
│   ├── csv_validator.py                 # Valida integridad del CSV generado
│   └── test_case_extractor.py           # Extrae casos de prueba del código
├── tests/                               # Suite de Pruebas
│   ├── test_cases/
│   ├── test_cross_reference_implementation.py
│   ├── test_csv_manager.py
│   └── test_real_cases.py
├── modified_modules.json                # Lista de módulos a analizar
└── odoo_field_changes_detected.csv      # Resultado principal con cambios detectados
```

### Flujo de Procesamiento

El sistema funciona en las siguientes etapas secuenciales:

1. **Análisis Git**: `GitAnalyzer` obtiene archivos modificados entre commits
2. **Extracción AST**: `ASTVisitor` parsea código Python extrayendo campos y métodos
3. **Construcción de Modelos**: `ModelRegistry` + `ModelFlattener` resuelven herencia Odoo
4. **Emparejamiento**: `MatchingEngine` identifica elementos renombrados usando similitudes
5. **Referencias Cruzadas**: `CrossReferenceAnalyzer` encuentra usos de cada cambio
6. **Generación CSV**: `CSVManager` produce archivo final con cambios y referencias

### Componentes Principales por Responsabilidad

#### Análisis de Código (`analyzers/`)
- **`ast_visitor.py`**: Parsea AST de Python extrayendo campos y métodos con sus firmas
- **`git_analyzer.py`**: Compara archivos entre commits usando comandos Git
- **`matching_engine.py`**: Empareja elementos renombrados basándose en similitudes
- **`cross_reference_analyzer.py`**: Busca referencias de campos/métodos en todo el codebase

#### Lógica Central (`core/`)
- **`models.py`**: Define estructuras de datos para representar cambios
- **`model_registry.py`**: Mantiene registro completo de modelos Odoo
- **`inheritance_graph.py`**: Mapea relaciones de herencia entre modelos
- **`model_flattener.py`**: Resuelve herencia múltiple para análisis completo

#### Configuración (`config/`)
- **`settings.py`**: Configuración general (rutas, umbrales, filtros)
- **`naming_rules.py`**: Reglas para detectar patrones de renombrado automático

#### Utilidades (`utils/`)
- **`csv_manager.py`**: Gestiona entrada/salida de archivos CSV
- **`csv_validator.py`**: Valida estructura e integridad de datos CSV
- **`test_case_extractor.py`**: Extrae casos de prueba del código fuente

## Instalación y Configuración

### Requisitos

- Python 3.7 o superior
- Git instalado y configurado
- Acceso al repositorio de Odoo a analizar

### Instalación

```bash
# Clonar el repositorio de herramientas
git clone <repository-url>
cd agromarin-tools/field_method_detector

# Instalar dependencias (si las hay)
pip install -r requirements.txt  # Si existe
```

### Configuración

1. **Configurar módulos a analizar** en `modified_modules.json`:
```json
{
  "modules": [
    "module_name_1",
    "module_name_2"
  ]
}
```

2. **Ajustar reglas de nomenclatura** en `config/naming_rules.py`
3. **Configurar settings** en `config/settings.py`

## Ejemplos de Uso

### Uso Básico

```bash
# Ejecutar detección entre dos commits
python detect_field_method_changes.py --commit-from abc123 --commit-to def456

# Modo interactivo para validación manual
python detect_field_method_changes.py --commit-from abc123 --commit-to def456 --interactive

# Especificar archivo de módulos personalizado
python detect_field_method_changes.py --modules-file custom_modules.json --commit-from abc123 --commit-to def456
```

### Parámetros Disponibles

- `--commit-from`: Commit de origen para comparación
- `--commit-to`: Commit de destino para comparación
- `--modules-file`: Archivo JSON con lista de módulos (opcional)
- `--interactive`: Habilita validación manual interactiva
- `--output`: Archivo de salida CSV (por defecto: `odoo_field_changes_detected.csv`)

### Ejemplo de Flujo Completo

```bash
# 1. Preparar lista de módulos modificados
echo '{"modules": ["sale", "purchase", "stock"]}' > my_modules.json

# 2. Ejecutar análisis
python detect_field_method_changes.py \
    --commit-from v15.0 \
    --commit-to v16.0 \
    --modules-file my_modules.json \
    --interactive

# 3. Revisar resultados
cat odoo_field_changes_detected.csv
```

## Archivos de Salida

### `odoo_field_changes_detected.csv`

Archivo principal con los resultados de la detección. La estructura actual incluye:

**Columnas Básicas:**
- **change_id**: Identificador único del cambio
- **old_name**: Nombre original del campo/método
- **new_name**: Nuevo nombre detectado
- **item_type**: Tipo de elemento (`field` o `method`)
- **module**: Módulo donde se detectó el cambio
- **model**: Modelo de Odoo específico
- **confidence**: Puntuación de confianza (0.0 - 1.0)

**Columnas Extendidas** (cuando están disponibles):
- **change_scope**: Alcance del cambio (`model`, `inherited`, etc.)
- **impact_type**: Tipo de impacto (`primary`, `secondary`)
- **context**: Información contextual adicional
- **parent_change_id**: Referencia a cambio relacionado

### Ejemplo de Salida CSV

```csv
change_id,old_name,new_name,item_type,module,model,confidence
1,supplier_invoice_count,count_supplier_invoice,field,account,res.partner,1.000
2,_compute_supplier_invoice_count,_compute_count_supplier_invoice,method,account,res.partner,1.000
3,action_open_product_template,action_view_product_template,method,product,product.product,0.950
```

## Consideraciones Técnicas

### Algoritmo de Detección

1. **Análisis Git**: Compara archivos modificados entre dos commits específicos
2. **Extracción AST**: Parsea código Python extrayendo definiciones de campos y métodos
3. **Generación de Firmas**: Crea identificadores únicos basados en:
   - Tipo de campo/decoradores de método
   - Argumentos y parámetros de función
   - Contexto de definición (clase contenedora)
   - Excluye nombres para permitir detección de renombres
4. **Resolución de Herencia**: Construye grafo completo de herencia Odoo (_inherit, _inherits)
5. **Matching Inteligente**: Empareja elementos usando:
   - Similitud de firmas (alta confianza)
   - Heurísticas de nomenclatura (confianza media)
   - Análisis de contexto y posición
6. **Referencias Cruzadas**: Busca usos de cada cambio detectado en todo el codebase
7. **Validación**: Aplica reglas de nomenclatura y calcula puntuaciones de confianza

### Limitaciones Actuales

- **Análisis Python únicamente**: Solo procesa archivos `.py`, no detecta cambios en XML
- **Herencia compleja**: La resolución de herencia múltiple puede ser lenta en proyectos grandes
- **Falsos positivos**: Heurísticas pueden generar coincidencias incorrectas en casos ambiguos
- **Rendimiento**: El análisis completo puede tardar varios minutos en repositorios grandes
- **Scope limitado**: Se enfoca en renombres, no detecta refactorizaciones de lógica

### Áreas de Optimización Identificadas

1. **Consolidación de analizadores**: Unificar `ast_visitor.py` y `cross_reference_analyzer.py`
2. **Caché de herencia**: Implementar caché más agresivo en `ModelFlattener`
3. **Configuración simplificada**: Reducir número de archivos de configuración
4. **Utilidades CSV unificadas**: Consolidar `csv_manager.py` y `csv_validator.py`

### Mejores Prácticas

1. **Validación Manual**: Siempre revisar resultados con alta confianza
2. **Commits Específicos**: Usar commits específicos para análisis precisos
3. **Módulos Filtrados**: Analizar solo módulos relevantes para mejor rendimiento
4. **Reglas Personalizadas**: Ajustar reglas de nomenclatura según convenciones del proyecto

## Contribución

Para contribuir a esta herramienta:

1. Fork el repositorio
2. Crear una rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit los cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear un Pull Request

## Licencia

Esta herramienta sigue las directrices de la OCA para herramientas de desarrollo de Odoo.

## Soporte

Para reportar bugs o solicitar funcionalidades, por favor crear un issue en el repositorio del proyecto.