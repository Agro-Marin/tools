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

## Estructura del Código

```
field_method_detector/
├── __init__.py                          # Inicialización del paquete
├── detect_field_method_changes.py       # Script principal
├── analyzers/                           # Analizadores de código
│   ├── __init__.py
│   ├── ast_parser.py                    # Parser AST para análisis de código
│   ├── git_analyzer.py                  # Integración con Git
│   └── matching_engine.py               # Motor de coincidencias
├── config/                              # Configuración
│   ├── __init__.py
│   ├── naming_rules.py                  # Reglas de nomenclatura
│   └── settings.py                      # Configuraciones generales
├── interactive/                         # Interfaz interactiva
│   ├── __init__.py
│   └── validation_ui.py                 # UI para validación manual
├── utils/                               # Utilidades
│   ├── __init__.py
│   └── csv_manager.py                   # Gestión de archivos CSV
├── modified_modules.json                # Lista de módulos modificados
└── odoo_field_changes_detected.csv      # Resultado de detecciones
```

### Componentes Principales

#### 1. AST Parser (`ast_parser.py`)
- **CodeInventoryExtractor**: Extrae inventarios de campos y métodos
- Genera "firmas" únicas basadas en argumentos, tipos y decoradores
- Excluye nombres para permitir detección de renombres

#### 2. Git Analyzer (`git_analyzer.py`)
- **GitAnalyzer**: Interactúa con repositorios Git
- Obtiene contenido de archivos en commits específicos
- Utiliza comandos `git show` y `git diff` internamente

#### 3. Matching Engine (`matching_engine.py`)
- **MatchingEngine**: Lógica central de detección
- Compara inventarios entre versiones "antes" y "después"
- Aplica reglas de nomenclatura para validación
- Calcula puntuaciones de confianza

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

Archivo principal con los resultados de la detección. Contiene las siguientes columnas:

- **old_name**: Nombre original del campo/método
- **new_name**: Nuevo nombre del campo/método
- **item_type**: Tipo de elemento (`field` o `method`)
- **module**: Nombre del módulo analizado
- **model**: Modelo de Odoo donde se encuentra el elemento

### Ejemplo de Salida CSV

```csv
old_name,new_name,item_type,module,model
x_custom_field,custom_field,field,sale,sale.order
_compute_old,_compute_new,method,purchase,purchase.order
```

## Consideraciones Técnicas

### Algoritmo de Detección

1. **Extracción de Inventario**: Utiliza AST para extraer campos y métodos
2. **Generación de Firmas**: Crea identificadores únicos basados en:
   - Tipo de campo/decoradores de método
   - Argumentos y parámetros
   - Contexto de definición
3. **Matching por Firma**: Compara firmas entre commits
4. **Aplicación de Reglas**: Valida con reglas de nomenclatura
5. **Cálculo de Confianza**: Asigna puntuaciones basadas en similitud

### Limitaciones

- **Dependencia de AST**: Solo analiza código Python válido
- **Cambios Complejos**: No detecta refactorizaciones mayores
- **Falsos Positivos**: Puede generar coincidencias incorrectas en casos ambiguos
- **Rendimiento**: El análisis puede ser lento en repositorios grandes
- **Cobertura**: Limited a cambios de nombres, no detecta cambios de lógica

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