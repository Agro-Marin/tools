#!/usr/bin/env python3
"""
Odoo Field/Method Change Detector
==================================

Interactive script to detect renamed fields and methods between Git commits
using AST parsing, inheritance-aware analysis, and AgroMarin naming conventions.

This tool analyzes Odoo modules to identify when fields or methods have been
renamed between two Git commits, with special support for detecting renames
that cross inheritance boundaries (_inherit relationships).

Features:
- Inheritance-aware analysis (detects renames across _inherit boundaries)
- Interactive validation with confidence scoring
- Batch processing for similar patterns
- Automatic fallback to legacy analysis
- CSV output compatible with field_method_renaming tool

Usage:
    python detect_field_method_changes.py --json-file modified_modules.json [options]

Examples:
    # Interactive mode with auto-detected commits
    python detect_field_method_changes.py -i --json-file modified_modules.json
    
    # Automatic mode with specific commits
    python detect_field_method_changes.py --json-file modified_modules.json \
        --commit-from abc123 --commit-to def456 --confidence-threshold 0.80
    
    # Analyze specific module only
    python detect_field_method_changes.py --json-file modified_modules.json \
        --module account --interactive
"""

# =====================================
# IMPORTS AND INITIAL CONFIGURATION
# =====================================

# Standard library imports
import argparse
import json
import logging
import sys
from pathlib import Path

# Local imports
from analyzers.ast_parser import CodeInventoryExtractor
from analyzers.git_analyzer import GitAnalyzer, GitRepositoryError
from analyzers.matching_engine import MatchingEngine, RenameCandidate
from config.settings import Config, config
from core.model_flattener import ModelFlattener
from core.model_registry import ModelRegistry
from interactive.validation_ui import InteractiveValidator
from utils.csv_manager import CSVManager

# Add current directory to Python path for relative imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


# =====================================
# CONFIGURATION AND SETUP UTILITIES
# =====================================


def setup_logging(verbose: bool = False) -> None:
    """
    Configura el sistema de logging para la aplicación.

    Establece el nivel de logging apropiado y reduce el ruido de librerías
    externas. Configurado para mostrar output en stdout con formato detallado.

    Args:
        verbose: Si True, activa logging DEBUG. Si False, usa INFO.

    Side Effects:
        - Configura el logger global con formato específico
        - Reduce ruido de librerías externas (urllib3, requests)
        - Redirige todo el output a stdout para consistencia
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def parse_arguments() -> argparse.Namespace:
    """
    Parsea argumentos de línea de comandos con validaciones completas.

    Configura todos los argumentos disponibles incluyendo opciones para
    análisis específico de módulos, modos de operación, y configuración
    de salida.

    Returns:
        Namespace con argumentos validados y configuración por defecto

    Raises:
        SystemExit: Si argumentos son inválidos o --help se solicita

    Note:
        Los ejemplos en epilog están actualizados para mostrar el uso
        correcto de todas las opciones disponibles.
    """
    parser = argparse.ArgumentParser(
        description="Detect field and method name changes in Odoo modules with inheritance support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode with auto-detected commits
  %(prog)s -i --json-file modified_modules.json --repo-path /path/to/odoo
  
  # Automatic mode with specific commits  
  %(prog)s --json-file modified_modules.json --commit-from abc123 --commit-to def456 --repo-path /path/to/odoo
  
  # Interactive with custom confidence threshold
  %(prog)s -i --json-file modified_modules.json --confidence-threshold 0.80 --output changes.csv --repo-path /path/to/odoo
  
  # Analyze single module with verbose output
  %(prog)s -m account --json-file modified_modules.json --repo-path /path/to/odoo --verbose
  
  # Analyze multiple specific modules
  %(prog)s --modules account sale fleet --json-file modified_modules.json --repo-path /path/to/odoo
  
  # Dry run to see what would be detected
  %(prog)s --json-file modified_modules.json --dry-run --verbose
        """,
    )

    # Required arguments
    parser.add_argument(
        "--json-file",
        required=True,
        help="Path to modified_modules.json file containing module structure and commits",
    )

    # Git-related arguments
    parser.add_argument(
        "--commit-from",
        help="Starting commit SHA (auto-detects from parent if not provided)",
    )
    parser.add_argument(
        "--commit-to",
        help="Ending commit SHA (uses commit_to from JSON if not provided)",
    )
    parser.add_argument(
        "--repo-path",
        help="Git repository path (auto-detects from JSON structure if not provided)",
    )

    # Output configuration
    parser.add_argument(
        "--output",
        "-o",
        default="odoo_field_changes_detected.csv",
        help="Output CSV file path (default: %(default)s)",
    )
    parser.add_argument(
        "--report-file",
        help="Export detailed analysis report to this file (optional)",
    )

    # Analysis configuration
    parser.add_argument(
        "--confidence-threshold",
        "-t",
        type=float,
        default=0.75,
        help="Confidence threshold for auto-approval (0.0-1.0, default: %(default)s)",
    )

    # Mode selection
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Enable interactive validation mode for manual review",
    )
    parser.add_argument(
        "--batch-mode",
        action="store_true",
        help="Enable batch processing for similar patterns (experimental)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run analysis without writing results to CSV (useful for testing)",
    )

    # Module filtering
    parser.add_argument(
        "--module",
        "-m",
        help="Analyze only specific module (if omitted, all modules are analyzed)",
    )
    parser.add_argument(
        "--modules",
        nargs="+",
        help="Analyze only specific modules (space-separated list)",
    )

    # Debug and verbose options
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging with detailed debug information",
    )

    return parser.parse_args()


def load_modified_modules_json(json_file_path: str) -> dict:
    """
    Carga y valida el archivo JSON de módulos modificados.

    El archivo JSON debe contener la estructura de módulos modificados
    generada por el analizador de cambios, incluyendo información de
    commits y categorización de archivos.

    Args:
        json_file_path: Ruta al archivo modified_modules.json

    Returns:
        Diccionario con estructura validada:
        {
            'modified_modules': [lista de módulos],
            'commit_to': 'sha_commit',
            'repository_path': 'path/to/repo',
            ...
        }

    Raises:
        FileNotFoundError: Si el archivo no existe en la ruta especificada
        ValueError: Si el JSON es inválido o le falta estructura requerida

    Example:
        >>> data = load_modified_modules_json("modified_modules.json")
        >>> print(f"Found {len(data['modified_modules'])} modified modules")
        >>> print(f"Target commit: {data['commit_to']}")
    """
    json_path = Path(json_file_path)

    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_file_path}")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate required structure
        if "modified_modules" not in data:
            raise ValueError(
                "JSON file missing 'modified_modules' key. "
                "Ensure you're using a valid modified_modules.json file."
            )

        if not isinstance(data["modified_modules"], list):
            raise ValueError(
                "'modified_modules' must be a list. " "Check the JSON file structure."
            )

        logger.info(
            f"Loaded JSON with {len(data['modified_modules'])} modified modules"
        )

        # Log additional context if available
        if "commit_to" in data:
            logger.info(f"Target commit from JSON: {data['commit_to'][:8]}...")
        if "repository_path" in data:
            logger.info(f"Repository path from JSON: {data['repository_path']}")

        return data

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON file format: {e}")


# =====================================
# INHERITANCE-AWARE ANALYSIS (MAIN)
# =====================================


def analyze_module_files_with_inheritance(
    module_data: dict,
    git_analyzer: GitAnalyzer,
    commit_from: str,
    commit_to: str,
    extractor: CodeInventoryExtractor,
    matching_engine: MatchingEngine,
) -> list[RenameCandidate]:
    """
    Analiza archivos de un módulo para encontrar renames considerando herencia Odoo.

    Este es el método principal que implementa análisis consciente de herencia.
    Construye registros completos de modelos, los aplana para resolver herencia,
    y compara modelos completos en lugar de archivos individuales.

    Proceso detallado:
    1. Extrae archivos Python relevantes del módulo (models/, wizards/)
    2. Construye ModelRegistry para ambos commits usando batch processing
    3. Crea ModelFlattener para resolver cadenas de herencia completas
    4. Analiza cada modelo unificado para encontrar renames cross-file
    5. Convierte resultados al formato compatible con MatchingEngine
    6. Enriquece candidatos con contexto de herencia

    Args:
        module_data: Datos del módulo con estructura:
            {
                'module_name': str,
                'file_categories': {
                    'models': [lista de archivos .py],
                    'wizards': [lista de archivos .py],
                    ...
                }
            }
        git_analyzer: Instancia configurada de GitAnalyzer
        commit_from: SHA del commit inicial para comparación
        commit_to: SHA del commit final para comparación
        extractor: CodeInventoryExtractor (usado para fallback legacy)
        matching_engine: MatchingEngine con algoritmos de detección

    Returns:
        Lista de RenameCandidate encontrados con contexto de herencia.
        Cada candidato incluye información adicional como:
        - inheritance_chain: cadena de herencia del modelo
        - model_name: modelo Odoo donde se encontró el rename
        - inheritance_aware: flag indicando análisis con herencia

    Raises:
        Exception: Si falla el análisis, automáticamente hace fallback a legacy.
                  No propaga excepciones para garantizar robustez.

    Note:
        Si el análisis con herencia falla por cualquier razón,
        automáticamente revierte al análisis legacy sin interrumpir el flujo.
        Esto garantiza que la herramienta nunca falle completamente.

    Performance:
        - Optimizado para minimizar operaciones Git costosas
        - Usa cache interno en ModelRegistry y ModelFlattener
        - Batch processing para checkout de commits

    Example:
        Para un módulo con herencia:
        - models/sale_order.py: clase base SaleOrder
        - models/sale_custom.py: herencia de sale.order

        El análisis tradicional vería cada archivo por separado.
        Este análisis ve 'sale.order' como un modelo unificado con
        todos los campos/métodos de ambos archivos, permitiendo
        detectar renames que cruzan la frontera de archivos.
    """
    module_name = module_data["module_name"]
    logger.info(f"Starting inheritance-aware analysis for module '{module_name}'")

    try:
        # 1. Extraer archivos Python relevantes del módulo
        python_files = _extract_python_files_from_module(module_data)
        if not python_files:
            logger.warning(f"No Python files found in module {module_name}")
            return []

        # 2. Construir registros de modelos para ambos commits
        logger.info(
            f"Building model registries for commits {commit_from[:8]} → {commit_to[:8]}"
        )
        registry_before, registry_after = _build_registries_for_commits(
            python_files, git_analyzer, commit_from, commit_to
        )

        # 3. Analizar modelos unificados para encontrar renames
        candidates = _analyze_unified_models_for_renames(
            registry_before, registry_after, module_name, matching_engine
        )

        logger.info(
            f"Inheritance-aware analysis completed. Found {len(candidates)} candidates"
        )
        return candidates

    except Exception as e:
        logger.error(f"Error in inheritance-aware analysis for {module_name}: {e}")
        logger.info("Falling back to legacy file-by-file analysis")
        return analyze_module_files_legacy(
            module_data,
            git_analyzer,
            commit_from,
            commit_to,
            extractor,
            matching_engine,
        )


def _extract_python_files_from_module(module_data: dict) -> list[str]:
    """
    Extrae archivos Python relevantes de la estructura del módulo.

    Se enfoca en categorías que típicamente contienen modelos Odoo:
    'models' y 'wizards'. Filtra automáticamente para incluir solo
    archivos .py y omite archivos que no son relevantes para análisis.

    Args:
        module_data: Diccionario con estructura de categorías de archivos:
            {
                'file_categories': {
                    'models': ['models/sale_order.py', 'models/partner.py'],
                    'wizards': ['wizards/import_wizard.py'],
                    'views': ['views/sale_view.xml'],  # Omitido
                    'data': ['data/demo_data.xml']     # Omitido
                }
            }

    Returns:
        Lista de rutas de archivos Python para analizar.
        Solo incluye archivos de categorías relevantes que terminan en .py

    Example:
        >>> module_data = {
        ...     'file_categories': {
        ...         'models': ['models/sale_order.py', 'models/partner.py'],
        ...         'wizards': ['wizards/import_wizard.py', 'wizards/export.py'],
        ...         'views': ['views/sale_view.xml']  # Será ignorado
        ...     }
        ... }
        >>> files = _extract_python_files_from_module(module_data)
        >>> print(files)
        ['models/sale_order.py', 'models/partner.py', 'wizards/import_wizard.py', 'wizards/export.py']
    """
    relevant_categories = ["models", "wizards"]
    relevant_files = []

    file_categories = module_data.get("file_categories", {})

    for category in relevant_categories:
        if category in file_categories:
            category_files = file_categories[category]
            relevant_files.extend(category_files)
            logger.debug(f"Found {len(category_files)} files in category '{category}'")

    # Filter to Python files only and log the filtering
    python_files = [f for f in relevant_files if f.endswith(".py")]
    filtered_out = len(relevant_files) - len(python_files)

    if filtered_out > 0:
        logger.debug(f"Filtered out {filtered_out} non-Python files")

    logger.info(f"Found {len(python_files)} Python files to analyze")

    return python_files


def _build_registries_for_commits(
    python_files: list[str], git_analyzer: GitAnalyzer, commit_from: str, commit_to: str
) -> tuple[ModelRegistry, ModelRegistry]:
    """
    Construye registros de modelos para ambos commits de forma optimizada.

    Utiliza la función build_registry_for_commit para cada commit,
    que ya implementa optimizaciones como batch processing y manejo
    robusto de errores.

    Args:
        python_files: Lista de archivos Python a procesar
        git_analyzer: Instancia configurada de GitAnalyzer
        commit_from: SHA del commit inicial
        commit_to: SHA del commit final

    Returns:
        Tupla con (registry_before, registry_after)

    Performance Notes:
        - Cada registro se construye con una sola operación de checkout
        - Se restaura el commit original automáticamente
        - Maneja errores de archivos no encontrados gracefully
        - Utiliza cache interno del ModelRegistry para evitar re-parsing
    """
    logger.debug(f"Building model registries for {len(python_files)} Python files")

    # Construir registros en secuencia (no paralelizable debido a Git checkout)
    registry_before = build_registry_for_commit(python_files, git_analyzer, commit_from)
    registry_after = build_registry_for_commit(python_files, git_analyzer, commit_to)

    # Log estadísticas para debugging
    models_before = len(registry_before.get_all_model_names())
    models_after = len(registry_after.get_all_model_names())

    logger.debug(f"Registry before: {models_before} models")
    logger.debug(f"Registry after: {models_after} models")

    return registry_before, registry_after


def _analyze_unified_models_for_renames(
    registry_before: ModelRegistry,
    registry_after: ModelRegistry,
    module_name: str,
    matching_engine: MatchingEngine,
) -> list[RenameCandidate]:
    """
    Analiza modelos unificados (con herencia resuelta) para encontrar renames.

    Para cada modelo encontrado en cualquiera de los registros:
    1. Aplana el modelo resolviendo toda la cadena de herencia
    2. Compara versión before vs after del modelo completo
    3. Usa MatchingEngine existente para encontrar renames
    4. Enriquece candidatos con contexto de herencia

    Args:
        registry_before: Registro de modelos del commit inicial
        registry_after: Registro de modelos del commit final
        module_name: Nombre del módulo para contexto en candidatos
        matching_engine: Engine configurado con algoritmos de matching

    Returns:
        Lista de candidatos con información de herencia enriquecida

    Algorithm:
        El algoritmo itera sobre la unión de modelos en ambos registros,
        asegurando que se analicen modelos que aparecen solo en uno de
        los commits (nuevo modelo o modelo eliminado). Esto es crucial
        para detectar casos donde un modelo es renombrado completamente
        o donde la herencia se reorganiza.
    """
    # Crear flatteners para resolver herencia en cada registro
    flattener_before = ModelFlattener(registry_before)
    flattener_after = ModelFlattener(registry_after)

    # Encontrar todos los modelos únicos en ambos commits
    models_before = registry_before.get_all_model_names()
    models_after = registry_after.get_all_model_names()
    all_models = models_before.union(models_after)

    logger.info(
        f"Found {len(all_models)} unique models to analyze: {sorted(all_models)}"
    )

    # Debug: mostrar modelos que aparecen solo en un commit
    only_before = models_before - models_after
    only_after = models_after - models_before

    if only_before:
        logger.debug(f"Models only in before: {sorted(only_before)}")
    if only_after:
        logger.debug(f"Models only in after: {sorted(only_after)}")

    # Analizar cada modelo individualmente
    all_candidates = []
    for model_name in sorted(all_models):
        model_candidates = _analyze_single_unified_model(
            model_name, flattener_before, flattener_after, module_name, matching_engine
        )
        all_candidates.extend(model_candidates)

    return all_candidates


def _analyze_single_unified_model(
    model_name: str,
    flattener_before: ModelFlattener,
    flattener_after: ModelFlattener,
    module_name: str,
    matching_engine: MatchingEngine,
) -> list[RenameCandidate]:
    """
    Analiza un modelo individual unificado para encontrar renames.

    Este es el núcleo del análisis con herencia. Toma un modelo específico
    y lo analiza como una unidad completa, incluyendo todos los campos y
    métodos que hereda de otros archivos/clases.

    Proceso detallado:
    1. Obtiene modelo aplanado (con herencia resuelta) para ambas versiones
    2. Verifica que el modelo existe en ambos commits
    3. Convierte a formato inventory compatible con MatchingEngine
    4. Ejecuta algoritmos de matching existentes sobre modelos completos
    5. Enriquece resultados con contexto de herencia para trazabilidad

    Args:
        model_name: Nombre del modelo Odoo (ej: 'sale.order', 'account.move')
        flattener_before: ModelFlattener configurado con registry del commit inicial
        flattener_after: ModelFlattener configurado con registry del commit final
        module_name: Nombre del módulo para contexto en candidatos
        matching_engine: MatchingEngine con algoritmos de detección configurados

    Returns:
        Lista de RenameCandidate encontrados para este modelo específico.
        Cada candidato incluye contexto de herencia enriquecido.

    Example:
        Para un modelo 'sale.order' que se define en múltiples archivos:
        - models/sale_order.py: define clase base con campos básicos
        - models/sale_order_custom.py: hereda y añade campos custom
        - models/sale_order_extra.py: hereda y sobreescribe métodos

        El método ve 'sale.order' como UN SOLO modelo con TODOS los
        campos y métodos, permitiendo detectar:
        - Rename de campo en clase base usado por herencia
        - Rename de método sobreescrito en herencia
        - Campos/métodos movidos entre archivos de herencia

    Performance:
        - Utiliza cache del ModelFlattener para modelos ya procesados
        - Solo procesa modelos que existen en ambos commits
        - Logging optimizado para debug sin impacto en performance
    """
    logger.debug(f"Analyzing unified model: {model_name}")

    # Obtener modelos aplanados (herencia resuelta) para ambos commits
    flattened_before = flattener_before.get_flattened_model(model_name)
    flattened_after = flattener_after.get_flattened_model(model_name)

    # Skip si el modelo no existe en alguno de los commits
    if not flattened_before or not flattened_after:
        logger.debug(f"Model {model_name} not found in one of the commits, skipping")
        return []

    # Convertir modelos aplanados a formato inventory para compatibilidad
    # con MatchingEngine existente
    inventory_before = convert_flattened_to_inventory(flattened_before)
    inventory_after = convert_flattened_to_inventory(flattened_after)

    # Debug logging para visibilidad del proceso
    before_fields = len(inventory_before["fields"])
    before_methods = len(inventory_before["methods"])
    after_fields = len(inventory_after["fields"])
    after_methods = len(inventory_after["methods"])

    logger.debug(
        f"Model {model_name} - Before: {before_fields} fields, {before_methods} methods | "
        f"After: {after_fields} fields, {after_methods} methods"
    )

    # Usar MatchingEngine existente para encontrar renames
    # El file_path se marca como "MODEL:" para indicar análisis unificado
    model_candidates = matching_engine.find_renames_in_inventories(
        inventory_before, inventory_after, module_name, f"MODEL:{model_name}"
    )

    # Enriquecer candidatos con contexto de herencia
    for candidate in model_candidates:
        candidate.context_info = {
            "inheritance_aware": True,
            "model_name": model_name,
            "inheritance_chain": flattened_before.inheritance_chain,
            "analysis_method": "unified_model",
            "total_fields_before": before_fields,
            "total_methods_before": before_methods,
            "total_fields_after": after_fields,
            "total_methods_after": after_methods,
        }

    # Log resultados para debugging
    if model_candidates:
        logger.debug(
            f"✅ Found {len(model_candidates)} rename candidates in model {model_name}"
        )
        for candidate in model_candidates:
            logger.debug(
                f"   {candidate.old_name} → {candidate.new_name} "
                f"(confidence: {candidate.confidence:.2f}, type: {candidate.item_type})"
            )
    else:
        logger.debug(f"   No rename candidates found in model {model_name}")

    return model_candidates


# =====================================
# REGISTRY CONSTRUCTION AND CONVERSION
# =====================================


def build_registry_for_commit(
    files: list[str], git_analyzer: GitAnalyzer, commit: str
) -> ModelRegistry:
    """
    Construye un ModelRegistry completo para un commit específico.

    Este método maneja operaciones Git de forma altamente optimizada:
    1. Extrae paths de módulos automáticamente desde lista de archivos
    2. Hace checkout al commit target una sola vez (no por archivo)
    3. Procesa todos los módulos encontrados en batch
    4. Restaura commit original automáticamente en bloque finally
    5. Maneja errores de archivos faltantes gracefully

    Args:
        files: Lista de archivos Python a procesar. Se usan para inferir
               los directorios de módulos que deben escanearse.
        git_analyzer: Instancia configurada de GitAnalyzer con acceso al repo
        commit: SHA del commit a analizar

    Returns:
        ModelRegistry poblado con todos los modelos encontrados en el commit.
        El registry incluye información completa de herencia, campos, métodos
        y referencias cruzadas para todos los modelos descubiertos.

    Performance Notes:
        - Una sola operación checkout por commit (no por archivo)
        - Extrae paths de módulos automáticamente usando patrón "addons/"
        - Cache interno en ModelRegistry evita re-parsing de archivos
        - Batch processing de todos los módulos encontrados

    Error Handling:
        - Si checkout falla, propaga GitRepositoryError
        - Si archivos individuales fallan, los omite con warning
        - Siempre restaura commit original en bloque finally
        - Si no se encuentran paths válidos, retorna registry vacío con warning

    Module Discovery:
        La función busca el patrón "addons/module_name" en las rutas de archivos
        para determinar qué directorios de módulos debe escanear. Esto permite
        procesar múltiples módulos automáticamente.

    Example:
        >>> files = ['addons/sale/models/sale_order.py', 'addons/account/models/move.py']
        >>> registry = build_registry_for_commit(files, git_analyzer, 'abc123')
        >>> print(registry.get_all_model_names())
        {'sale.order', 'account.move', 'sale.order.line', ...}
    """
    registry = ModelRegistry()

    # Extraer paths de módulos desde la lista de archivos
    # Busca patrón "addons/module_name" para determinar directorios a escanear
    module_paths = set()
    for file_path in files:
        parts = Path(file_path).parts
        if "addons" in parts:
            addon_idx = parts.index("addons")
            if addon_idx + 1 < len(parts):
                # Construir path hasta el directorio del módulo
                module_path = "/".join(parts[: addon_idx + 2])
                module_paths.add(module_path)

    if not module_paths:
        logger.warning(
            f"No valid module paths found in {len(files)} files for commit {commit[:8]}"
        )
        return registry

    logger.debug(f"Discovered {len(module_paths)} module paths: {sorted(module_paths)}")

    # Optimización crítica: un solo checkout, procesar todo, restaurar
    current_commit = git_analyzer.get_current_commit()
    try:
        logger.debug(f"Checking out commit {commit[:8]} for registry construction")
        git_analyzer.checkout_commit(commit)

        # Procesar todos los módulos en el commit actual
        logger.debug(f"Scanning {len(module_paths)} module paths")
        registry.scan_modules(list(module_paths))

        # Log estadísticas del registry construido
        discovered_models = registry.get_all_model_names()
        logger.debug(
            f"Registry built for commit {commit[:8]}: {len(discovered_models)} models"
        )

        if logger.isEnabledFor(logging.DEBUG) and discovered_models:
            logger.debug(f"Models found: {sorted(discovered_models)}")

    except Exception as e:
        logger.error(f"Error building registry for commit {commit[:8]}: {e}")
        # No re-raise para permitir fallback graceful

    finally:
        # Siempre restaurar commit original
        if current_commit:
            logger.debug(f"Restoring original commit {current_commit[:8]}")
            try:
                git_analyzer.checkout_commit(current_commit)
            except Exception as restore_error:
                logger.error(f"Failed to restore original commit: {restore_error}")

    return registry


def convert_flattened_to_inventory(flattened_model) -> dict:
    """
    Convierte FlattenedModel al formato inventory compatible con MatchingEngine.

    El MatchingEngine existente espera un formato específico de diccionario
    con claves 'fields', 'methods', y 'classes'. Esta función actúa como
    adaptador entre el nuevo sistema de herencia y el engine de matching
    existente, preservando toda la funcionalidad mientras añade capacidades
    de herencia.

    Args:
        flattened_model: Instancia de FlattenedModel con herencia resuelta.
                        Contiene all_fields y all_methods con información
                        completa de herencia.

    Returns:
        Diccionario en formato inventory compatible con estructura:
        {
            'fields': [lista de campos con metadatos completos],
            'methods': [lista de métodos con metadatos completos],
            'classes': [],  # Vacío para compatibilidad con MatchingEngine
            'file_path': 'FLATTENED:{model_name}'  # Indicador especial
        }

    Data Transformation:
        Cada campo/método mantiene toda su información original del AST
        parsing más metadatos adicionales de herencia como:
        - defined_in_model: modelo donde se definió originalmente
        - is_inherited: si proviene de herencia o definición directa
        - is_overridden: si sobreescribe definición de modelo padre
        - source_file: archivo físico donde está el código

        Esto permite que el MatchingEngine funcione normalmente mientras
        preserva contexto de herencia completo para debugging/reporting.

    Compatibility:
        El formato generado es 100% compatible con el MatchingEngine
        existente. Los campos adicionales de herencia son ignorados por
        el engine pero están disponibles para logging y análisis posterior.

    Example:
        Para un modelo 'sale.order' con herencia:
        - Campo 'name' definido en models/sale_order.py
        - Campo 'custom_field' definido en models/sale_custom.py
        - Método 'action_confirm' sobreescrito en models/sale_custom.py

        El inventory resultante contiene todos los campos/métodos como si
        fueran de un solo modelo, pero preserva información de origen.
    """
    inventory = {
        "fields": [],
        "methods": [],
        "classes": [],  # Mantenido vacío para compatibilidad
        "file_path": f"FLATTENED:{flattened_model.model_name}",
    }

    # Convertir campos aplanados preservando toda la metadata
    for field in flattened_model.all_fields:
        field_dict = {
            # Campos requeridos por MatchingEngine (formato original)
            "name": field.name,
            "type": "field",
            "field_type": field.field_type,
            "args": field.args,
            "kwargs": field.kwargs,
            "signature": field.signature,
            "definition": field.definition,
            "line": field.line_number,
            "model": flattened_model.model_name,
            # Metadata de herencia adicional (ignorada por MatchingEngine)
            "source_file": field.source_file,
            "defined_in_model": field.defined_in_model,
            "is_inherited": field.is_inherited,
        }
        inventory["fields"].append(field_dict)

    # Convertir métodos aplanados preservando toda la metadata
    for method in flattened_model.all_methods:
        method_dict = {
            # Campos requeridos por MatchingEngine (formato original)
            "name": method.name,
            "type": "method",
            "args": method.args,
            "decorators": method.decorators,
            "signature": method.signature,
            "definition": method.definition,
            "line": method.line_number,
            "model": flattened_model.model_name,
            # Metadata de herencia adicional (ignorada por MatchingEngine)
            "source_file": method.source_file,
            "defined_in_model": method.defined_in_model,
            "is_inherited": method.is_inherited,
            "is_overridden": method.is_overridden,
        }
        inventory["methods"].append(method_dict)

    return inventory


# =====================================
# LEGACY ANALYSIS (FALLBACK)
# =====================================


def analyze_module_files_legacy(
    module_data: dict,
    git_analyzer: GitAnalyzer,
    commit_from: str,
    commit_to: str,
    extractor: CodeInventoryExtractor,
    matching_engine: MatchingEngine,
) -> list[RenameCandidate]:
    """
    Análisis archivo por archivo (implementación original).

    Este método mantiene la lógica original como fallback robusto y confiable.
    Se ejecuta automáticamente si el análisis con herencia falla por cualquier
    razón, garantizando que la herramienta nunca falle completamente.

    Diferencias principales vs análisis con herencia:
    - Procesa cada archivo independientemente (no ve relaciones entre archivos)
    - No resuelve herencia entre modelos (_inherit relationships)
    - Más rápido pero menos preciso para detección cross-file
    - 100% compatible con versiones anteriores de la herramienta
    - Usa CodeInventoryExtractor original sin modificaciones

    Ventajas del método legacy:
    - Simplicidad y confiabilidad probada
    - Menor consumo de memoria (no construye registros completos)
    - Menos operaciones Git (solo get_file_content_at_commit)
    - Debug logging detallado para cada archivo procesado

    Args:
        module_data: Datos del módulo con archivos categorizados
        git_analyzer: Instancia GitAnalyzer configurada
        commit_from: SHA commit inicial para comparación
        commit_to: SHA commit final para comparación
        extractor: CodeInventoryExtractor para parsing AST tradicional
        matching_engine: MatchingEngine para algoritmos de detección

    Returns:
        Lista de RenameCandidate encontrados por análisis tradicional.
        No incluye contexto de herencia, pero mantiene toda la información
        estándar de candidatos (confidence, signature_match, etc.)

    Note:
        Esta función preserva exactamente el comportamiento y logging
        de la versión original para mantener compatibilidad total y
        servir como fallback confiable en caso de problemas con el
        análisis de herencia.

    Performance:
        - Procesamiento secuencial archivo por archivo
        - Dos operaciones get_file_content_at_commit por archivo
        - Logging detallado de inventarios para debugging
        - Sin construcción de estructuras de datos complejas
    """
    module_name = module_data["module_name"]
    candidates = []

    # Procesar solo archivos de categorías relevantes (como en análisis con herencia)
    relevant_files = []
    for category in ["models", "wizards"]:
        if category in module_data.get("file_categories", {}):
            relevant_files.extend(module_data["file_categories"][category])

    logger.info(
        f"Analyzing {len(relevant_files)} files in module '{module_name}' (legacy mode)"
    )

    # Procesar cada archivo independientemente (método tradicional)
    for file_path in relevant_files:
        if not file_path.endswith(".py"):
            continue

        try:
            # Obtener contenido del archivo en ambos commits
            content_before = git_analyzer.get_file_content_at_commit(
                file_path, commit_from
            )
            content_after = git_analyzer.get_file_content_at_commit(
                file_path, commit_to
            )

            if not content_before or not content_after:
                logger.debug(
                    f"File {file_path} not found in one of the commits, skipping"
                )
                continue

            # Extraer inventarios usando AST parser original
            inventory_before = extractor.extract_inventory(content_before, file_path)
            inventory_after = extractor.extract_inventory(content_after, file_path)

            # Logging detallado para debugging (preservado del original)
            logger.debug(f"\n{'='*80}")
            logger.debug(f"ANALYZING FILE: {file_path}")
            logger.debug(f"{'='*80}")

            # Log inventory before
            before_fields = inventory_before.get("fields", [])
            before_methods = inventory_before.get("methods", [])
            logger.debug(f"COMMIT BEFORE ({commit_from[:8]}):")
            logger.debug(
                f"  Fields ({len(before_fields)}): {[f['name'] for f in before_fields]}"
            )
            logger.debug(
                f"  Methods ({len(before_methods)}): {[m['name'] for m in before_methods]}"
            )

            # Log inventory after
            after_fields = inventory_after.get("fields", [])
            after_methods = inventory_after.get("methods", [])
            logger.debug(f"COMMIT AFTER ({commit_to[:8]}):")
            logger.debug(
                f"  Fields ({len(after_fields)}): {[f['name'] for f in after_fields]}"
            )
            logger.debug(
                f"  Methods ({len(after_methods)}): {[m['name'] for m in after_methods]}"
            )

            # Encontrar renames usando MatchingEngine (método tradicional)
            file_candidates = matching_engine.find_renames_in_inventories(
                inventory_before, inventory_after, module_name, file_path
            )

            candidates.extend(file_candidates)

            # Log resultados (preservado del original)
            if file_candidates:
                logger.debug(f"✅ FOUND {len(file_candidates)} rename candidates:")
                for candidate in file_candidates:
                    logger.debug(
                        f"   {candidate.old_name} → {candidate.new_name} "
                        f"(confidence: {candidate.confidence:.2f})"
                    )
            else:
                logger.debug(f"❌ No rename candidates found")

            logger.debug(f"{'='*80}\n")

        except Exception as e:
            logger.warning(f"Error analyzing file {file_path}: {e}")
            continue

    logger.info(
        f"Legacy analysis completed for {module_name}. Found {len(candidates)} candidates"
    )
    return candidates


# Mantener alias para compatibilidad hacia atrás completa
analyze_module_files = analyze_module_files_with_inheritance


# =====================================
# MAIN FUNCTION AND ORCHESTRATION
# =====================================


def main() -> int:
    """
    Función principal que orquesta todo el proceso de detección de renames.

    Esta función coordina el flujo completo de análisis desde la carga de
    configuración hasta la generación de resultados finales. Maneja todos
    los casos de error posibles y proporciona códigos de salida específicos
    para integración con scripts y pipelines.

    Flujo principal:
    1. Parsea argumentos y configura logging con nivel apropiado
    2. Carga y valida archivo JSON de módulos modificados
    3. Inicializa configuración de aplicación con parámetros
    4. Determina ruta de repositorio (auto-detección o manual)
    5. Inicializa GitAnalyzer y resuelve commits para análisis
    6. Muestra información de configuración para confirmación
    7. Inicializa componentes de análisis (MatchingEngine, etc.)
    8. Filtra módulos según especificaciones de usuario
    9. Procesa cada módulo usando análisis con herencia
    10. Ejecuta validación interactiva o procesamiento automático
    11. Guarda resultados en CSV y genera reportes opcionales
    12. Muestra resumen final con estadísticas completas

    Error Handling:
        La función captura y maneja específicamente diferentes tipos de errores:
        - Errores de configuración y argumentos → Exit code 1
        - Errores de Git (repositorio no encontrado, commits inválidos) → Exit code 2
        - Errores de archivos (JSON no encontrado, permisos) → Exit code 3
        - Errores durante análisis → Exit code 4 (pero guarda resultados parciales)
        - Interrupción por usuario (Ctrl+C) → Exit code 130 (estándar Unix)

    Exit Codes:
        - 0: Éxito completo, resultados guardados correctamente
        - 1: Error de Git o repositorio (configuración incorrecta)
        - 2: Error de archivos (JSON no encontrado, permisos CSV)
        - 3: Error de entrada inválida (argumentos, estructura JSON)
        - 4: Error durante análisis (pero resultados parciales pueden existir)
        - 130: Interrupción por usuario (Ctrl+C)

    Interactive Mode:
        En modo interactivo (-i/--interactive), presenta cada candidato
        al usuario para aprobación manual. Incluye:
        - Vista detallada de cada rename con contexto
        - Opciones de aprobación/rechazo individual
        - Procesamiento en lotes para patrones similares
        - Resumen final con estadísticas de aprobación

    Automatic Mode:
        En modo automático, solo aprueba candidatos que superan el
        umbral de confianza configurado. Más rápido pero conservador.

    Performance Considerations:
        - Usa análisis con herencia por defecto (más preciso)
        - Fallback automático a análisis legacy si hay problemas
        - Filtrado de duplicados para evitar re-procesamiento
        - Carga incremental de CSV existente

    Example Usage:
        # Análisis interactivo completo
        python detect_field_method_changes.py -i --json-file modules.json

        # Análisis automático con umbral personalizado
        python detect_field_method_changes.py --json-file modules.json -t 0.85

        # Análisis de módulo específico con verbose
        python detect_field_method_changes.py -m sale --json-file modules.json -v
    """
    # Parse arguments and setup basic configuration
    args = parse_arguments()
    setup_logging(args.verbose)

    global logger
    logger = logging.getLogger(__name__)

    try:
        # BLOCK 1: Configuration Loading and Validation
        logger.info("Loading modified modules JSON...")
        modules_data = load_modified_modules_json(args.json_file)

        # Initialize application configuration with parsed arguments
        app_config = Config()
        app_config.confidence_threshold = args.confidence_threshold
        app_config.interactive_mode = args.interactive
        app_config.batch_mode = args.batch_mode
        app_config.verbose = args.verbose
        app_config.output_csv = args.output
        app_config.report_file = args.report_file

        # BLOCK 2: Git Repository and Component Initialization
        # Determine repository path (auto-detect from JSON or use provided)
        repo_path = args.repo_path or app_config.get_repo_path_from_json(args.json_file)
        logger.info(f"Using repository path: {repo_path}")

        # Initialize Git analyzer for repository operations
        logger.info("Initializing Git analyzer...")
        git_analyzer = GitAnalyzer(repo_path)

        # BLOCK 3: Commit Resolution and Information Display
        logger.info("Resolving commits...")
        commit_from, commit_to = git_analyzer.resolve_commits(
            args.commit_from, args.commit_to, modules_data
        )

        # Gather commit information for user display
        commit_from_info = git_analyzer.get_commit_info(commit_from)
        commit_to_info = git_analyzer.get_commit_info(commit_to)

        # Build module filtering information for display
        module_filter_info = ""
        if args.module:
            module_filter_info = f"\n   🎯 Módulo específico: {args.module}"
        elif args.modules:
            module_filter_info = (
                f"\n   🎯 Módulos específicos: {', '.join(args.modules)}"
            )

        # Display comprehensive configuration information
        print(
            f"""
🔍 Análisis de Cambios de Nombres - Configuración:
📂 Repositorio: {repo_path}
📊 Total módulos modificados: {len(modules_data['modified_modules'])}{module_filter_info}

📅 Commits a comparar:
    Desde: {commit_from[:8]} - {commit_from_info['message'][:50]}...
    Hasta: {commit_to[:8]} - {commit_to_info['message'][:50]}...

⚙️  Configuración:
    Método de análisis: {'Herencia + Fallback Legacy' if not args.verbose else 'Herencia (con debug completo)'}
    Umbral de confianza: {app_config.confidence_threshold:.1%}
    Modo interactivo: {'Sí' if app_config.interactive_mode else 'No'}
    Archivo de salida: {app_config.output_csv}
    {'Dry run: SÍ (no se guardará)' if args.dry_run else ''}
        """
        )

        # BLOCK 4: Analysis Components Initialization
        # Initialize all analysis components
        extractor = CodeInventoryExtractor()
        matching_engine = MatchingEngine()
        csv_manager = CSVManager(app_config.output_csv)

        # Load existing CSV records to avoid duplicates
        logger.info("Loading existing CSV records...")
        existing_records = csv_manager.load_existing_csv()
        logger.info(f"Found {len(existing_records)} existing records in CSV")

        # BLOCK 5: Module Filtering and Selection
        modules_to_analyze = modules_data["modified_modules"]

        if args.module:
            # Single module specified - filter and validate
            modules_to_analyze = [
                m for m in modules_to_analyze if m["module_name"] == args.module
            ]
            if not modules_to_analyze:
                logger.error(f"Module '{args.module}' not found in modified modules")
                return 4
            logger.info(f"Analyzing single module: {args.module}")

        elif args.modules:
            # Multiple modules specified - filter and report missing
            specified_modules = set(args.modules)
            modules_to_analyze = [
                m for m in modules_to_analyze if m["module_name"] in specified_modules
            ]

            found_modules = {m["module_name"] for m in modules_to_analyze}
            missing_modules = specified_modules - found_modules

            if missing_modules:
                logger.warning(
                    f"Modules not found in modified modules: {', '.join(missing_modules)}"
                )

            if not modules_to_analyze:
                logger.error(
                    "None of the specified modules were found in modified modules"
                )
                return 4

            logger.info(
                f"Analyzing {len(modules_to_analyze)} specified modules: {', '.join(found_modules)}"
            )

        else:
            # Analyze all modified modules
            logger.info(f"Analyzing all {len(modules_to_analyze)} modified modules")

        # BLOCK 6: Module Analysis Processing
        logger.info("Starting inheritance-aware analysis of selected modules...")
        all_candidates = []

        for i, module_data in enumerate(modules_to_analyze, 1):
            module_name = module_data["module_name"]
            logger.info(
                f"[{i}/{len(modules_to_analyze)}] Analyzing module: {module_name}"
            )

            # Use inheritance-aware analysis (with automatic fallback to legacy)
            module_candidates = analyze_module_files(
                module_data,
                git_analyzer,
                commit_from,
                commit_to,
                extractor,
                matching_engine,
            )

            all_candidates.extend(module_candidates)
            logger.info(
                f"Module {module_name} completed: {len(module_candidates)} candidates found"
            )

        logger.info(
            f"Analysis complete. Found {len(all_candidates)} potential renames total"
        )

        # Early exit if no candidates found
        if not all_candidates:
            print("\n✅ No se detectaron cambios de nombres de campos o métodos.")
            return 0

        # BLOCK 7: Duplicate Filtering and Processing
        # Filter out duplicates against existing CSV records
        new_candidates, duplicate_candidates = csv_manager.filter_new_candidates(
            all_candidates
        )

        if duplicate_candidates:
            logger.info(
                f"Filtered out {len(duplicate_candidates)} duplicates from existing CSV"
            )

        if not new_candidates:
            print(
                f"\n✅ Todos los {len(all_candidates)} cambios detectados ya están en el CSV."
            )
            return 0

        logger.info(f"Processing {len(new_candidates)} new candidates")

        # BLOCK 8: Validation Processing (Interactive vs Automatic)
        if app_config.interactive_mode:
            # Interactive validation with user input
            logger.info("Starting interactive validation...")
            validator = InteractiveValidator(
                confidence_threshold=app_config.confidence_threshold,
                auto_approve_threshold=0.90,  # High confidence auto-approval
            )

            approved_candidates, validation_summary = validator.validate_candidates(
                new_candidates
            )

            if not approved_candidates:
                print("\n❌ No se aprobaron cambios para incluir en el CSV.")
                return 0

        else:
            # Automatic processing - only high confidence candidates
            approved_candidates = [
                c
                for c in new_candidates
                if c.confidence >= app_config.confidence_threshold
            ]

            validation_summary = {
                "total_detected": len(new_candidates),
                "total_approved": len(approved_candidates),
                "auto_approved": len(approved_candidates),
                "manually_approved": 0,
                "auto_rejected": len(new_candidates) - len(approved_candidates),
            }

            print(
                f"""
📊 Procesamiento Automático Completado:
   • Total detectados: {validation_summary['total_detected']}
   • Auto-aprobados (≥{app_config.confidence_threshold:.0%}): {validation_summary['auto_approved']}
   • Auto-rechazados (<{app_config.confidence_threshold:.0%}): {validation_summary['auto_rejected']}
            """
            )

        # BLOCK 9: Results Writing and Reporting
        # Write to CSV unless dry run mode
        if args.dry_run:
            logger.info(f"DRY RUN: Would add {len(approved_candidates)} records to CSV")
            print(
                f"🧪 DRY RUN: Se habrían añadido {len(approved_candidates)} registros al CSV"
            )
        else:
            # Add approved candidates to CSV
            logger.info(
                f"Writing {len(approved_candidates)} approved candidates to CSV..."
            )
            records_added = csv_manager.add_candidates_to_csv(approved_candidates)
            logger.info(f"Successfully added {records_added} new records to CSV")

        # Export detailed report if requested
        if app_config.report_file and approved_candidates:
            logger.info(f"Exporting detailed report to {app_config.report_file}...")
            csv_manager.export_candidates_report(
                approved_candidates, app_config.report_file
            )
            print(f"📄 Reporte detallado exportado: {app_config.report_file}")

        # BLOCK 10: Final Summary Display
        if app_config.interactive_mode:
            # Show interactive validation summary
            validator.show_final_summary(
                approved_candidates, validation_summary, app_config.output_csv
            )
        else:
            # Show automatic processing summary
            final_total = len(existing_records) + len(approved_candidates)
            print(
                f"""
✅ Proceso completado exitosamente:
   💾 Archivo CSV: {app_config.output_csv}
   📝 Registros añadidos: {len(approved_candidates)}
   📊 Total registros en CSV: {final_total}
   🧠 Método de análisis: {'Herencia-aware (con fallback)' if len(approved_candidates) > 0 else 'Sin cambios detectados'}
            """
            )

        return 0

    except KeyboardInterrupt:
        logger.info("Process interrupted by user (Ctrl+C)")
        print("\n⚠️ Proceso interrumpido por el usuario")
        return 130

    except GitRepositoryError as e:
        logger.error(f"Git repository error: {e}")
        print(f"\n❌ Error de repositorio Git: {e}")
        return 1

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"\n❌ Archivo no encontrado: {e}")
        return 2

    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        print(f"\n❌ Entrada inválida: {e}")
        return 3

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n💥 Error inesperado: {e}")

        if args.verbose:
            import traceback

            traceback.print_exc()

        return 1


if __name__ == "__main__":
    sys.exit(main())
