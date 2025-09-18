# Arquitectura Técnica - Field Method Renaming Tool

## Visión General de la Arquitectura

El módulo `field_method_renaming` está diseñado con una arquitectura modular y extensible que separa claramente las responsabilidades de cada componente.

## Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                 apply_field_method_changes.py              │
│                    (Script Principal)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
              ┌───────▼────────┐
              │  CSVReader     │
              │ (utils/)       │
              └───────┬────────┘
                      │
              ┌───────▼────────┐
              │  FileFinder    │
              │ (utils/)       │
              └───────┬────────┘
                      │
          ┌───────────▼────────────┐
          │     Processors        │
          │                       │
      ┌───▼──────┐    ┌──────▼────┐
      │ Python   │    │    XML    │
      │Processor │    │ Processor │
      └─────┬────┘    └─────┬─────┘
            │               │
        ┌───▼────┐      ┌───▼────┐
        │Backup  │      │Confirm │
        │Manager │      │UI      │
        └────────┘      └────────┘
```

## Componentes Principales

### 1. Script Principal (apply_field_method_changes.py)

**Responsabilidad**: Orquestación del flujo principal y manejo de argumentos.

```python
class FieldMethodRenamingTool:
    def __init__(self, config):
        self.csv_reader = CSVReader(config.csv_file)
        self.file_finder = FileFinder(config.repo_path)
        self.python_processor = PythonProcessor()
        self.xml_processor = XMLProcessor()
        self.backup_manager = BackupManager(config.backup_dir)
        
    def run(self):
        # 1. Cargar cambios desde CSV
        # 2. Agrupar por módulo/modelo
        # 3. Encontrar archivos relevantes
        # 4. Procesar cada archivo
        # 5. Validar resultados
```

### 2. CSVReader (utils/csv_reader.py)

**Responsabilidad**: Lectura, validación y parsing del archivo CSV de entrada.

```python
class CSVReader:
    def load_changes(self) -> list[FieldChange]:
        """Carga y valida cambios desde CSV"""
        
    def validate_csv_structure(self) -> bool:
        """Valida estructura del CSV"""
        
    def group_by_module(self, changes) -> dict[str, list[FieldChange]]:
        """Agrupa cambios por módulo para procesamiento eficiente"""
```

**Estructuras de Datos**:
```python
@dataclass
class FieldChange:
    old_name: str
    new_name: str
    module: str
    model: str
    change_type: str  # 'field' | 'method'
```

### 3. FileFinder (utils/file_finder.py)

**Responsabilidad**: Localización de archivos siguiendo convenciones OCA.

```python
class FileFinder:
    def find_files_for_model(self, module: str, model: str) -> FileSet:
        """Encuentra archivos usando convenciones OCA"""
        
    def _build_file_patterns(self, model: str) -> dict[str, list[str]]:
        """Construye patrones de archivos según convenciones OCA"""
        
    def _search_recursive_fallback(self, module_path: Path, model: str) -> list[Path]:
        """Búsqueda fallback si no encuentra archivos con naming estándar"""
```

**Estructura de Datos**:
```python
@dataclass
class FileSet:
    python_files: list[Path]
    view_files: list[Path]
    data_files: list[Path]
    demo_files: list[Path]
    template_files: list[Path]
    report_files: list[Path]
    security_files: list[Path]
```

### 4. BaseProcessor (processors/base_processor.py)

**Responsabilidad**: Funcionalidad común para todos los procesadores.

```python
class BaseProcessor:
    def process_file(self, file_path: Path, changes: list[FieldChange]) -> ProcessResult:
        """Template method para procesamiento de archivos"""
        
    def validate_syntax(self, file_path: Path) -> bool:
        """Valida sintaxis del archivo modificado"""
        
    def create_backup(self, file_path: Path) -> Path:
        """Crea respaldo del archivo original"""
```

### 5. PythonProcessor (processors/python_processor.py)

**Responsabilidad**: Procesamiento de archivos Python usando AST.

```python
class PythonProcessor(BaseProcessor):
    def __init__(self):
        self.ast_modifier = ASTModifier()
        
    def process_python_file(self, file_path: Path, changes: list[FieldChange]) -> ProcessResult:
        """Procesa archivo Python usando AST"""
        
    def _apply_field_changes(self, tree: ast.AST, changes: list[FieldChange]) -> ast.AST:
        """Aplica cambios de campos en AST"""
        
    def _apply_method_changes(self, tree: ast.AST, changes: list[FieldChange]) -> ast.AST:
        """Aplica cambios de métodos en AST"""
```

**Componente AST**:
```python
class ASTModifier(ast.NodeTransformer):
    def visit_Assign(self, node):
        """Modifica asignaciones de campos"""
        
    def visit_FunctionDef(self, node):
        """Modifica definiciones de métodos"""
        
    def visit_Str(self, node):
        """Modifica strings con referencias"""
```

### 6. XMLProcessor (processors/xml_processor.py)

**Responsabilidad**: Procesamiento de archivos XML usando ElementTree y regex.

```python
class XMLProcessor(BaseProcessor):
    def __init__(self):
        self.patterns = XMLPatterns()
        
    def process_xml_file(self, file_path: Path, changes: list[FieldChange]) -> ProcessResult:
        """Procesa archivo XML"""
        
    def _apply_elementtree_changes(self, root: ET.Element, changes: list[FieldChange]):
        """Aplica cambios usando ElementTree para elementos estructurados"""
        
    def _apply_regex_changes(self, content: str, changes: list[FieldChange]) -> str:
        """Aplica cambios usando regex para patrones complejos"""
```

**Patrones XML**:
```python
class XMLPatterns:
    FIELD_PATTERNS = [
        r'<field\s+name=["\']({old_name})["\']',
        r't-field=["\'][^"\']*\.({old_name})["\']',
        r't-esc=["\'][^"\']*\.({old_name})["\']',
    ]
    
    METHOD_PATTERNS = [
        r'<button\s+name=["\']({old_name})["\']',
        r'action=["\']({old_name})["\']',
        r't-call=["\']({old_name})["\']',
    ]
```

### 7. BackupManager (utils/backup_manager.py)

**Responsabilidad**: Gestión de respaldos automáticos.

```python
class BackupManager:
    def create_backup(self, file_path: Path) -> Path:
        """Crea respaldo con timestamp"""
        
    def create_batch_backup(self, files: list[Path]) -> Path:
        """Crea respaldo de múltiples archivos"""
        
    def restore_backup(self, backup_path: Path) -> bool:
        """Restaura desde respaldo"""
        
    def cleanup_old_backups(self, retention_days: int):
        """Limpia respaldos antiguos"""
```

### 8. ConfirmationUI (interactive/confirmation_ui.py)

**Responsabilidad**: Interfaz interactiva para confirmación de cambios.

```python
class ConfirmationUI:
    def confirm_file_changes(self, file_path: Path, changes: list[FieldChange]) -> bool:
        """Confirma cambios en un archivo"""
        
    def show_diff(self, original: str, modified: str):
        """Muestra diferencias antes/después"""
        
    def batch_confirm(self, file_changes: dict[Path, list[FieldChange]]) -> dict[Path, bool]:
        """Confirmación en lote"""
```

## Flujo de Procesamiento

### 1. Fase de Inicialización
```python
def initialize():
    # 1. Validar argumentos CLI
    # 2. Cargar configuración
    # 3. Inicializar componentes
    # 4. Validar prerrequisitos (CSV, repo, permisos)
```

### 2. Fase de Carga
```python
def load_phase():
    # 1. Leer y validar CSV
    # 2. Agrupar cambios por módulo
    # 3. Aplicar filtros (módulo, tipo de archivo)
    # 4. Validar integridad de datos
```

### 3. Fase de Descubrimiento
```python
def discovery_phase():
    # 1. Para cada módulo/modelo:
    #    - Encontrar archivos Python
    #    - Encontrar archivos XML (todos los tipos)
    #    - Validar que archivos existan
    # 2. Crear plan de procesamiento
```

### 4. Fase de Procesamiento
```python
def processing_phase():
    # Para cada archivo encontrado:
    # 1. Crear respaldo (si está habilitado)
    # 2. Cargar contenido original
    # 3. Aplicar cambios según tipo:
    #    - Python: AST modification
    #    - XML: ElementTree + regex
    # 4. Validar sintaxis del resultado
    # 5. Escribir archivo modificado
    # 6. Registrar cambios aplicados
```

### 5. Fase de Validación
```python
def validation_phase():
    # 1. Verificar sintaxis de archivos modificados
    # 2. Verificar que todos los cambios se aplicaron
    # 3. Generar reporte de resultados
    # 4. Cleanup en caso de errores
```

## Manejo de Errores

### Estrategia de Error Handling

```python
class ProcessingError(Exception):
    """Error base para procesamiento"""
    
class SyntaxValidationError(ProcessingError):
    """Error de validación de sintaxis"""
    
class FileNotFoundError(ProcessingError):
    """Archivo esperado no encontrado"""
    
class BackupError(ProcessingError):
    """Error en creación de respaldo"""
```

### Rollback Strategy
```python
def handle_processing_error(self, error: ProcessingError, context: ProcessingContext):
    # 1. Log error detallado
    # 2. Restaurar desde respaldo si es necesario
    # 3. Marcar archivo como fallido
    # 4. Continuar con siguiente archivo o abortar según configuración
```

## Extensibilidad

### Agregar Nuevos Tipos de Archivo

1. **Crear nuevo procesador**:
```python
class YAMLProcessor(BaseProcessor):
    def process_yaml_file(self, file_path: Path, changes: list[FieldChange]) -> ProcessResult:
        # Implementar lógica específica para YAML
```

2. **Registrar en FileFinder**:
```python
FILE_TYPE_PATTERNS = {
    'yaml': ['*.yml', '*.yaml'],
    'json': ['*.json'],
}
```

3. **Actualizar script principal**:
```python
def get_processor(file_type: str) -> BaseProcessor:
    processors = {
        'python': PythonProcessor(),
        'xml': XMLProcessor(),
        'yaml': YAMLProcessor(),  # Nuevo
    }
    return processors[file_type]
```

### Agregar Nuevos Patrones

```python
# En XMLPatterns
CUSTOM_PATTERNS = [
    r'custom-field=["\']({old_name})["\']',
    r'@{model}\.({old_name})',
]
```

## Configuración y Settings

### Archivo de Configuración
```python
# config/renaming_settings.py
class RenamingConfig:
    # Patrones de archivos
    FILE_PATTERNS = {...}
    
    # Configuración de respaldos
    BACKUP_ENABLED = True
    BACKUP_RETENTION_DAYS = 30
    
    # Configuración de procesamiento
    PARALLEL_PROCESSING = False
    MAX_WORKERS = 4
    
    # Validación
    STRICT_SYNTAX_VALIDATION = True
    CONTINUE_ON_ERROR = False
```

## Performance y Optimización

### Estrategias de Optimización

1. **Lazy Loading**: Cargar archivos solo cuando se necesitan
2. **Caching**: Cache de patrones compilados y AST parseados
3. **Batch Processing**: Agrupar cambios por archivo
4. **Parallel Processing**: Procesar archivos independientes en paralelo

### Métricas de Performance
```python
@dataclass
class ProcessingMetrics:
    files_processed: int
    total_changes_applied: int
    processing_time: float
    backup_time: float
    validation_time: float
    errors_encountered: int
```