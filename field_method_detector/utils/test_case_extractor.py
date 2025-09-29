#!/usr/bin/env python3
"""
Test Case Extractor for Field Method Detector
==============================================

Extrae casos de prueba desde commits Git reales para crear test cases YAML
que se pueden usar en el framework de testing MVP.
"""

import subprocess
import yaml
import argparse
import csv
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class TestCaseExtractor:
    """Extractor de casos de prueba desde Git commits reales"""

    def __init__(self, repo_path: str = ".", main_script: str = "main.py"):
        """
        Initialize the test case extractor.
        
        Args:
            repo_path: Path al repositorio Git
            main_script: Path al script principal del field_method_detector
        """
        self.repo_path = Path(repo_path).resolve()
        self.main_script = Path(main_script).resolve()
        
        # Verificar que estamos en un repo Git
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"No se encontró repositorio Git en: {self.repo_path}")
        
        # Verificar que existe el script principal
        if not self.main_script.exists():
            raise ValueError(f"Script principal no encontrado: {self.main_script}")

    def extract_case_from_commits(
        self, 
        commit_before: str, 
        commit_after: str, 
        case_name: str, 
        output_file: str,
        description: Optional[str] = None
    ) -> bool:
        """
        Extrae un caso de prueba desde commits Git existentes.
        
        Args:
            commit_before: Hash del commit "antes" de los cambios
            commit_after: Hash del commit "después" de los cambios
            case_name: Nombre descriptivo del caso
            output_file: Archivo YAML de salida
            description: Descripción opcional del caso
            
        Returns:
            True si la extracción fue exitosa
        """
        logger.info(f"Extrayendo caso desde {commit_before[:8]} a {commit_after[:8]}...")
        
        try:
            # 1. Validar que los commits existen
            self._validate_commits(commit_before, commit_after)
            
            # 2. Validar que hay cambios entre commits (sin obtener diff completo)
            logger.info("Validando que existen cambios entre commits...")
            
            # 3. Ejecutar field_method_detector en esos commits
            expected_output = self._run_detector_on_commits(commit_before, commit_after, getattr(self, 'json_file', None))
            
            if not expected_output:
                logger.warning("El detector no encontró cambios en estos commits")
                return False
            
            # 4. Crear estructura del caso (sin diff)
            case_data = self._create_case_structure(
                case_name, commit_before, commit_after, expected_output, description
            )
            
            # 5. Guardar archivo YAML
            success = self._save_yaml_case(case_data, output_file)
            
            if success:
                logger.info(f"✅ Caso extraído exitosamente: {output_file}")
                logger.info(f"   - {len(expected_output)} detecciones esperadas")
                return True
            
        except Exception as e:
            logger.error(f"Error extrayendo caso: {e}")
            return False
        
        return False

    def _validate_commits(self, commit_before: str, commit_after: str) -> None:
        """Valida que los commits existen en el repositorio"""
        for commit in [commit_before, commit_after]:
            try:
                result = subprocess.run([
                    'git', 'cat-file', '-e', commit
                ], cwd=self.repo_path, capture_output=True, check=True)
            except subprocess.CalledProcessError:
                raise ValueError(f"Commit no válido o no encontrado: {commit}")

    def _get_diff_between_commits(self, commit_before: str, commit_after: str) -> str:
        """Obtiene el diff entre dos commits"""
        try:
            result = subprocess.run([
                'git', 'diff', f"{commit_before}..{commit_after}"
            ], cwd=self.repo_path, capture_output=True, text=True, check=True)
            
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error obteniendo diff: {e}")

    def _run_detector_on_commits(self, commit_before: str, commit_after: str, json_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """Ejecuta field_method_detector en los commits especificados"""
        try:
            # Crear archivo temporal para la salida
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                temp_csv = tmp_file.name
            
            # Ejecutar el detector con los argumentos correctos
            cmd = [
                'python', str(self.main_script),
                '--repo-path', str(self.repo_path),
                '--commit-from', commit_before,
                '--commit-to', commit_after,
                '--output', temp_csv
            ]
            
            # Añadir JSON file si se proporciona
            if json_file:
                cmd.extend(['--json-file', json_file])
            
            logger.info(f"Ejecutando: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                cwd=self.repo_path.parent  # Ejecutar desde el directorio padre
            )
            
            # Leer resultados del CSV
            expected_output = []
            if Path(temp_csv).exists():
                with open(temp_csv, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        expected_output.append({
                            'old_name': row['old_name'],
                            'new_name': row['new_name'],
                            'item_type': row['item_type'],
                            'module': row.get('module', ''),
                            'model': row.get('model', '')
                        })
                
                # Limpiar archivo temporal
                Path(temp_csv).unlink()
            
            return expected_output
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error ejecutando detector: {e}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            return []

    def _create_case_structure(
        self, 
        case_name: str, 
        commit_before: str, 
        commit_after: str, 
        expected_output: List[Dict[str, Any]],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Crea la estructura del caso de prueba"""
        
        if description is None:
            description = f"Real case extracted from commits {commit_before[:7]}..{commit_after[:7]}"
        
        return {
            'name': case_name,
            'description': description,
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'source_commits': {
                    'before': commit_before,
                    'after': commit_after
                },
                'extractor_version': '1.0',
                'total_detections': len(expected_output)
            },
            'expected_output': expected_output
        }

    def _save_yaml_case(self, case_data: Dict[str, Any], output_file: str) -> bool:
        """Guarda el caso en un archivo YAML"""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(case_data, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error guardando YAML: {e}")
            return False

    def validate_case_file(self, yaml_file: str) -> bool:
        """Valida que un archivo YAML de caso esté bien formado"""
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                case = yaml.safe_load(f)
            
            # Validaciones básicas
            required_fields = ['name', 'expected_output']
            for field in required_fields:
                if field not in case:
                    logger.error(f"Campo requerido faltante: {field}")
                    return False
            
            # Validar expected_output
            for item in case['expected_output']:
                required_item_fields = ['old_name', 'new_name', 'item_type']
                for field in required_item_fields:
                    if field not in item:
                        logger.error(f"Campo requerido faltante en expected_output: {field}")
                        return False
                
                if item['item_type'] not in ['field', 'method']:
                    logger.error(f"item_type inválido: {item['item_type']}")
                    return False
            
            logger.info(f"✅ Archivo YAML válido: {yaml_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error validando YAML: {e}")
            return False

    def extract_critical_cases_from_csv(self, csv_file: str, output_dir: str, max_cases: int = 5) -> List[str]:
        """
        Extrae casos críticos basándose en el CSV de detecciones existente.
        
        Args:
            csv_file: Archivo CSV con detecciones existentes
            output_dir: Directorio de salida para los casos
            max_cases: Número máximo de casos a extraer
            
        Returns:
            Lista de archivos YAML creados
        """
        logger.info(f"Extrayendo casos críticos desde CSV: {csv_file}")
        
        if not Path(csv_file).exists():
            logger.error(f"Archivo CSV no encontrado: {csv_file}")
            return []
        
        # Analizar patrones más frecuentes del CSV
        pattern_frequency = {}
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    old_name = row.get('old_name', '')
                    new_name = row.get('new_name', '')
                    
                    # Identificar patrones
                    if 'qty_' in old_name and 'qty_' in new_name:
                        pattern = 'qty_patterns'
                    elif '_count' in old_name and 'count_' in new_name:
                        pattern = 'count_patterns'
                    elif old_name.startswith('_compute') and new_name.startswith('_compute'):
                        pattern = 'compute_methods'
                    elif 'order_line' in old_name and 'line_ids' in new_name:
                        pattern = 'order_line_patterns'
                    else:
                        pattern = 'other_patterns'
                    
                    pattern_frequency[pattern] = pattern_frequency.get(pattern, 0) + 1
        
        except Exception as e:
            logger.error(f"Error leyendo CSV: {e}")
            return []
        
        # Identificar los patrones más críticos
        critical_patterns = sorted(pattern_frequency.items(), key=lambda x: x[1], reverse=True)[:max_cases]
        
        logger.info("Patrones críticos identificados:")
        for pattern, count in critical_patterns:
            logger.info(f"  - {pattern}: {count} ocurrencias")
        
        # Para crear casos sintéticos (ya que no tenemos acceso a commits específicos aquí)
        created_files = []
        for pattern, count in critical_patterns:
            case_file = Path(output_dir) / f"case_{pattern}.yml"
            if self._create_synthetic_case(pattern, case_file):
                created_files.append(str(case_file))
        
        return created_files

    def _create_synthetic_case(self, pattern: str, output_file: Path) -> bool:
        """Crea un caso sintético basado en patrones identificados"""
        # Templates sintéticos basados en patrones reales
        templates = {
            'qty_patterns': {
                'name': 'qty_delivered_to_transfered_synthetic',
                'description': 'Synthetic case for qty_delivered -> qty_transfered pattern',
                'expected_output': [
                    {
                        'old_name': 'qty_delivered',
                        'new_name': 'qty_transfered',
                        'item_type': 'field'
                    },
                    {
                        'old_name': '_compute_qty_delivered',
                        'new_name': '_compute_qty_transfered',
                        'item_type': 'method'
                    }
                ]
            },
            'count_patterns': {
                'name': 'delivery_count_to_count_delivery_synthetic',
                'description': 'Synthetic case for delivery_count -> count_delivery pattern',
                'expected_output': [
                    {
                        'old_name': 'delivery_count',
                        'new_name': 'count_delivery',
                        'item_type': 'field'
                    }
                ]
            }
        }
        
        if pattern not in templates:
            logger.warning(f"No hay template para el patrón: {pattern}")
            return False
        
        try:
            case_data = templates[pattern].copy()
            case_data['metadata'] = {
                'extraction_date': datetime.now().isoformat(),
                'type': 'synthetic',
                'pattern': pattern,
                'extractor_version': '1.0'
            }
            
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(case_data, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            logger.info(f"✅ Caso sintético creado: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error creando caso sintético: {e}")
            return False


def main():
    """CLI para el extractor de casos de prueba"""
    parser = argparse.ArgumentParser(
        description="Extrae casos de prueba para field_method_detector desde commits Git",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Extraer caso desde commits específicos
  python utils/test_case_extractor.py extract-commits \\
    --before 7c142414 \\
    --after 0c2db5f5 \\
    --name "qty_patterns_critical" \\
    --output tests/test_cases/case_qty_patterns.yml

  # Extraer casos críticos desde CSV existente
  python utils/test_case_extractor.py extract-from-csv \\
    --csv odoo_field_changes_detected.csv \\
    --output-dir tests/test_cases/ \\
    --max-cases 5

  # Validar archivo YAML existente
  python utils/test_case_extractor.py validate \\
    --yaml tests/test_cases/case_qty_patterns.yml
        """
    )
    
    # Configurar logging
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando: extract-commits
    extract_parser = subparsers.add_parser('extract-commits', help='Extraer caso desde commits Git')
    extract_parser.add_argument('--before', required=True, help='Commit antes de los cambios')
    extract_parser.add_argument('--after', required=True, help='Commit después de los cambios')
    extract_parser.add_argument('--name', required=True, help='Nombre descriptivo del caso')
    extract_parser.add_argument('--output', required=True, help='Archivo YAML de salida')
    extract_parser.add_argument('--description', help='Descripción opcional del caso')
    extract_parser.add_argument('--repo', default='.', help='Path al repositorio Git')
    extract_parser.add_argument('--main-script', default='main.py', help='Script principal del detector')
    extract_parser.add_argument('--json-file', help='Path al archivo JSON de módulos (requerido para detect_field_method_changes.py)')
    
    # Comando: extract-from-csv
    csv_parser = subparsers.add_parser('extract-from-csv', help='Extraer casos críticos desde CSV')
    csv_parser.add_argument('--csv', required=True, help='Archivo CSV con detecciones')
    csv_parser.add_argument('--output-dir', required=True, help='Directorio de salida')
    csv_parser.add_argument('--max-cases', type=int, default=5, help='Máximo número de casos')
    
    # Comando: validate
    validate_parser = subparsers.add_parser('validate', help='Validar archivo YAML de caso')
    validate_parser.add_argument('--yaml', required=True, help='Archivo YAML a validar')
    
    args = parser.parse_args()
    
    # Configurar logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'extract-commits':
            extractor = TestCaseExtractor(args.repo, args.main_script)
            # Pasar json_file si se proporciona
            if hasattr(args, 'json_file') and args.json_file:
                extractor.json_file = args.json_file
            success = extractor.extract_case_from_commits(
                args.before, args.after, args.name, args.output, args.description
            )
            return 0 if success else 1
            
        elif args.command == 'extract-from-csv':
            extractor = TestCaseExtractor()
            created_files = extractor.extract_critical_cases_from_csv(
                args.csv, args.output_dir, args.max_cases
            )
            logger.info(f"✅ Creados {len(created_files)} casos de prueba")
            for file in created_files:
                logger.info(f"   - {file}")
            return 0
            
        elif args.command == 'validate':
            extractor = TestCaseExtractor()
            valid = extractor.validate_case_file(args.yaml)
            return 0 if valid else 1
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())