#!/usr/bin/env python3
"""
Test Real Cases for Field Method Detector
=========================================

Tests que ejecutan la herramienta field_method_detector contra casos reales
extraídos desde commits y validan que las detecciones sigan siendo correctas.
"""

import yaml
import subprocess
import csv
import tempfile
import os
import logging
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class TestRealCases:
    """Tests basados en casos reales extraídos del proyecto"""
    
    def __init__(self, repo_path: str = None, commit_before: str = None, commit_after: str = None):
        self.test_dir = Path(__file__).parent
        self.cases_dir = self.test_dir / "test_cases"
        self.project_root = self.test_dir.parent
        self.detector_script = self.project_root / "detect_field_method_changes.py"
        self.json_file = self.project_root / "modified_modules.json"
        
        # Parámetros configurables
        self.override_repo_path = repo_path
        self.override_commit_before = commit_before
        self.override_commit_after = commit_after
        
        # Validar que existan los archivos necesarios
        if not self.detector_script.exists():
            raise FileNotFoundError(f"Script detector no encontrado: {self.detector_script}")
        if not self.json_file.exists():
            raise FileNotFoundError(f"JSON file no encontrado: {self.json_file}")
    
    def test_odoo_migration_case(self):
        """Test caso de migración real de Odoo extraído desde commits"""
        case_file = "case_odoo_migration.yml"
        self._run_case(case_file)
    
    def test_qty_patterns_case(self):
        """Test patrones qty_* -> qty_transfered si existe el caso"""
        case_file = "case_qty_patterns.yml"
        if (self.cases_dir / case_file).exists():
            self._run_case(case_file)
        else:
            logger.info(f"Caso {case_file} no existe, saltando test")
    
    def test_count_patterns_case(self):
        """Test patrones *_count -> count_* si existe el caso"""
        case_file = "case_count_patterns.yml"
        if (self.cases_dir / case_file).exists():
            self._run_case(case_file)
        else:
            logger.info(f"Caso {case_file} no existe, saltando test")
    
    def _run_case(self, case_file: str):
        """
        Ejecuta un caso de prueba específico.
        
        Args:
            case_file: Nombre del archivo YAML del caso
        """
        logger.info(f"🧪 Ejecutando caso: {case_file}")
        
        # 1. Cargar definición del caso
        case = self._load_case(case_file)
        
        # 2. Verificar que el caso tiene la información necesaria
        self._validate_case(case, case_file)
        
        # 3. Ejecutar detector en los commits del caso
        result_csv = self._run_detector_on_case(case)
        
        try:
            # 4. Verificar que detecta lo esperado
            self._assert_detections_match(result_csv, case['expected_output'], case_file)
            
            logger.info(f"✅ Caso {case_file} PASÓ")
            
        finally:
            # 5. Limpiar archivo temporal
            if result_csv and Path(result_csv).exists():
                Path(result_csv).unlink()
    
    def _load_case(self, case_file: str) -> Dict[str, Any]:
        """Carga un caso de prueba desde YAML"""
        case_path = self.cases_dir / case_file
        
        if not case_path.exists():
            raise FileNotFoundError(f"Caso no encontrado: {case_path}")
        
        try:
            with open(case_path, 'r', encoding='utf-8') as f:
                case = yaml.safe_load(f)
            return case
        except Exception as e:
            raise ValueError(f"Error cargando caso {case_file}: {e}")
    
    def _validate_case(self, case: Dict[str, Any], case_file: str):
        """Valida que el caso tenga la estructura correcta"""
        required_fields = ['name', 'expected_output']
        for field in required_fields:
            if field not in case:
                raise ValueError(f"Caso {case_file} falta campo requerido: {field}")
        
        # Solo validar commits si no hay override de parámetros
        if not (self.override_repo_path and self.override_commit_before and self.override_commit_after):
            metadata = case.get('metadata', {})
            source_commits = metadata.get('source_commits')
            
            if not source_commits:
                raise ValueError(f"Caso {case_file} falta información de commits en metadata.source_commits")
            
            if 'before' not in source_commits or 'after' not in source_commits:
                raise ValueError(f"Caso {case_file} falta commits 'before' y/o 'after'")
        
        # Validar expected_output
        if not case['expected_output']:
            raise ValueError(f"Caso {case_file} no tiene detecciones esperadas")
        
        for item in case['expected_output']:
            required_item_fields = ['old_name', 'new_name', 'item_type']
            for field in required_item_fields:
                if field not in item:
                    raise ValueError(f"Caso {case_file} item falta campo: {field}")
    
    def _run_detector_on_case(self, case: Dict[str, Any]) -> str:
        """
        Ejecuta el detector en el caso específico.
        
        Args:
            case: Diccionario con la definición del caso
            
        Returns:
            Path al archivo CSV con resultados
        """
        # Usar parámetros override o del caso
        if self.override_commit_before and self.override_commit_after:
            commit_before = self.override_commit_before
            commit_after = self.override_commit_after
            repo_path = self.override_repo_path
            logger.info(f"🔧 Usando commits de parámetros: {commit_before[:8]}..{commit_after[:8]}")
        else:
            metadata = case['metadata']
            commits = metadata['source_commits']
            commit_before = commits['before']
            commit_after = commits['after']
            repo_path = metadata.get('repo_path', '/home/suniagajose/Instancias/odoo')
            logger.info(f"📋 Usando commits del YAML: {commit_before[:8]}..{commit_after[:8]}")
        
        # Crear archivo temporal para resultados
        temp_fd, temp_csv = tempfile.mkstemp(suffix='.csv')
        os.close(temp_fd)  # Cerrar file descriptor, solo necesitamos el path
        
        # Construir comando para ejecutar detector
        cmd = [
            'python', str(self.detector_script),
            '--json-file', str(self.json_file),
            '--repo-path', repo_path,  # Usar repo_path calculado
            '--commit-from', commit_before,
            '--commit-to', commit_after,
            '--output', temp_csv
        ]
        
        logger.info(f"Ejecutando: {' '.join(cmd)}")
        
        try:
            # Ejecutar comando
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.project_root  # Ejecutar desde directorio del proyecto
            )
            
            logger.info("✅ Detector ejecutado exitosamente")
            return temp_csv
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error ejecutando detector:")
            logger.error(f"   STDOUT: {e.stdout}")
            logger.error(f"   STDERR: {e.stderr}")
            logger.error(f"   Return code: {e.returncode}")
            
            # Limpiar archivo temporal
            if Path(temp_csv).exists():
                Path(temp_csv).unlink()
            
            raise RuntimeError(f"Detector falló con código {e.returncode}")
    
    def _assert_detections_match(
        self, 
        result_csv: str, 
        expected_output: List[Dict[str, Any]], 
        case_file: str
    ):
        """
        Verifica que las detecciones del CSV coincidan con lo esperado.
        
        Args:
            result_csv: Path al CSV con resultados del detector
            expected_output: Lista de detecciones esperadas
            case_file: Nombre del caso (para logs)
        """
        if not Path(result_csv).exists():
            raise FileNotFoundError(f"Archivo de resultados no existe: {result_csv}")
        
        # Leer detecciones del CSV
        detections = []
        try:
            with open(result_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                detections = list(reader)
        except Exception as e:
            raise RuntimeError(f"Error leyendo CSV resultado: {e}")
        
        logger.info(f"📊 Detector encontró {len(detections)} detecciones")
        logger.info(f"📋 Esperadas: {len(expected_output)} detecciones")
        
        # Verificar cada detección esperada
        missing_detections = []
        for expected_item in expected_output:
            matching_detection = self._find_matching_detection(detections, expected_item)
            
            if matching_detection is None:
                missing_detections.append(expected_item)
                logger.error(
                    f"❌ NO DETECTADO: {expected_item['old_name']} -> {expected_item['new_name']} "
                    f"({expected_item['item_type']})"
                )
            else:
                logger.info(
                    f"✅ DETECTADO: {expected_item['old_name']} -> {expected_item['new_name']} "
                    f"({expected_item['item_type']})"
                )
        
        # Fallar test si hay detecciones faltantes
        if missing_detections:
            missing_str = ", ".join([
                f"{item['old_name']}->{item['new_name']}" 
                for item in missing_detections
            ])
            raise AssertionError(
                f"❌ REGRESIÓN DETECTADA en {case_file}: "
                f"Faltan {len(missing_detections)} detecciones: {missing_str}"
            )
        
        logger.info(f"✅ Todas las detecciones esperadas fueron encontradas")
    
    def _find_matching_detection(
        self, 
        detections: List[Dict[str, str]], 
        expected_item: Dict[str, Any]
    ) -> Dict[str, str] | None:
        """
        Busca una detección que coincida con el item esperado.
        
        Args:
            detections: Lista de detecciones del CSV
            expected_item: Item esperado
            
        Returns:
            Detección coincidente o None
        """
        for detection in detections:
            if (detection.get('old_name') == expected_item['old_name'] and
                detection.get('new_name') == expected_item['new_name'] and
                detection.get('item_type') == expected_item['item_type']):
                return detection
        
        return None


def test_odoo_migration_case(repo_path=None, commit_before=None, commit_after=None):
    """Test function para pytest"""
    runner = TestRealCases(repo_path, commit_before, commit_after)
    runner.test_odoo_migration_case()


def test_qty_patterns_case(repo_path=None, commit_before=None, commit_after=None):
    """Test function para pytest"""
    runner = TestRealCases(repo_path, commit_before, commit_after)
    runner.test_qty_patterns_case()


def test_count_patterns_case(repo_path=None, commit_before=None, commit_after=None):
    """Test function para pytest"""
    runner = TestRealCases(repo_path, commit_before, commit_after)
    runner.test_count_patterns_case()


if __name__ == "__main__":
    import argparse
    
    # Parser para argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description="Ejecuta tests de casos reales para field_method_detector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Usar configuración del YAML (default)
  python tests/test_real_cases.py

  # Usar commits y repo específicos
  python tests/test_real_cases.py \\
    --repo /path/to/odoo \\
    --commit-before abc123 \\
    --commit-after def456

  # Ejecutar solo un caso específico
  python tests/test_real_cases.py \\
    --repo /path/to/odoo \\
    --commit-before abc123 \\
    --commit-after def456 \\
    --case case_odoo_migration.yml
        """
    )
    
    parser.add_argument('--repo', '--repo-path', 
                       help='Path al repositorio Git a analizar')
    parser.add_argument('--commit-before', '--before',
                       help='Commit inicial (antes de los cambios)')
    parser.add_argument('--commit-after', '--after', 
                       help='Commit final (después de los cambios)')
    parser.add_argument('--case', 
                       help='Ejecutar solo un caso específico (ej: case_odoo_migration.yml)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Output detallado')
    
    args = parser.parse_args()
    
    # Configurar logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Validar parámetros
    if args.commit_before or args.commit_after or args.repo:
        if not (args.commit_before and args.commit_after and args.repo):
            print("❌ Error: Si usas --commit-before, --commit-after o --repo, debes especificar los tres")
            print("   Uso: --repo PATH --commit-before HASH --commit-after HASH")
            exit(1)
    
    print("🧪 Ejecutando tests de casos reales...")
    
    if args.repo:
        print(f"🔧 Configuración personalizada:")
        print(f"   📁 Repositorio: {args.repo}")
        print(f"   📌 Commit before: {args.commit_before[:8]}...")
        print(f"   📌 Commit after: {args.commit_after[:8]}...")
    else:
        print("📋 Usando configuración de archivos YAML")
    
    try:
        runner = TestRealCases(args.repo, args.commit_before, args.commit_after)
        
        # Determinar qué casos ejecutar
        if args.case:
            # Ejecutar solo el caso especificado
            case_name = args.case.replace('.yml', '')  # Permitir con o sin extensión
            test_method = getattr(runner, f"test_{case_name.replace('case_', '')}", None)
            
            if test_method is None:
                print(f"❌ Error: Caso '{args.case}' no encontrado")
                exit(1)
            
            test_cases = [(args.case, test_method)]
        else:
            # Ejecutar todos los casos disponibles
            test_cases = [
                ("case_odoo_migration.yml", runner.test_odoo_migration_case),
                ("case_qty_patterns.yml", runner.test_qty_patterns_case),
                ("case_count_patterns.yml", runner.test_count_patterns_case)
            ]
        
        passed = 0
        failed = 0
        
        for case_file, test_func in test_cases:
            try:
                test_func()
                passed += 1
            except FileNotFoundError:
                logger.info(f"⏭️  Saltando {case_file} (no existe)")
            except Exception as e:
                logger.error(f"❌ {case_file} FALLÓ: {e}")
                failed += 1
        
        print(f"\n📊 Resultados: {passed} pasaron, {failed} fallaron")
        
        if failed > 0:
            exit(1)
        else:
            print("🎉 Todos los tests pasaron!")
            
    except Exception as e:
        logger.error(f"💥 Error fatal: {e}")
        exit(1)