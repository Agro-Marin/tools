"""
Field Method Renaming Tool
==========================

Herramienta complementaria a field_method_detector que aplica automáticamente
los cambios de nombres de campos y métodos detectados en repositorios Odoo.

Características principales:
- Aplicación automática de cambios desde CSV
- Cobertura completa: Python (modelos, controllers) y XML (vistas, data, demo, templates)
- Convenciones OCA para localización de archivos
- Respaldos automáticos
- Validación de sintaxis
- Modo interactivo

Ejemplo de uso:
    python apply_field_method_changes.py --csv-file changes.csv --repo-path /path/to/odoo

Para más información, consultar:
    docs/README.md
    docs/USAGE.md
    docs/ARCHITECTURE.md
    docs/EXAMPLES.md
"""

__version__ = "1.0.0"
__author__ = "AgroMarin Tools"
__description__ = "Automatic field and method renaming tool for Odoo repositories"