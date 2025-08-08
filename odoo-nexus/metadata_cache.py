# metadata_cache.py
"""
Sistema de caché inteligente para metadatos de tabla.
Mejora el rendimiento evitando consultas repetitivas al esquema.
"""

import json
import os
from datetime import datetime, timedelta
from database import get_column_type

CACHE_FILE = "table_metadata_cache.json"
CACHE_DURATION_HOURS = 24

class MetadataCache:
    def __init__(self):
        self.cache = self._load_cache()
    
    def _load_cache(self):
        """Carga el caché desde el archivo"""
        if not os.path.exists(CACHE_FILE):
            return {}
        
        try:
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                
            # Verificar si el caché está vigente
            cache_time = datetime.fromisoformat(cache_data.get('timestamp', '1900-01-01'))
            if datetime.now() - cache_time > timedelta(hours=CACHE_DURATION_HOURS):
                return {}
                
            return cache_data.get('data', {})
        except:
            return {}
    
    def _save_cache(self):
        """Guarda el caché al archivo"""
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': self.cache
        }
        
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except:
            pass  # Fallar silenciosamente si no se puede escribir
    
    def get_field_type(self, table_name: str, field_name: str) -> str:
        """Obtiene el tipo de campo, usando caché cuando es posible"""
        cache_key = f"{table_name}.{field_name}"
        
        if cache_key not in self.cache:
            field_type = get_column_type(table_name, field_name)
            self.cache[cache_key] = field_type
            self._save_cache()
        
        return self.cache[cache_key]
    
    def is_jsonb_field(self, table_name: str, field_name: str) -> bool:
        """Determina si un campo es JSONB"""
        return self.get_field_type(table_name, field_name).lower() == 'jsonb'
    
    def get_name_field_selector(self, table_name: str, alias: str = None) -> str:
        """
        Genera el selector apropiado para el campo 'name' según su tipo.
        
        Args:
            table_name: Nombre de la tabla
            alias: Alias de la tabla en la consulta (opcional)
        
        Returns:
            String SQL para seleccionar el campo name apropiadamente
        """
        prefix = f"{alias}." if alias else ""
        
        if self.is_jsonb_field(table_name, 'name'):
            return f"COALESCE({prefix}name->>'es_ES', {prefix}name->>'en_US')"
        else:
            return f"{prefix}name"

# Instancia global del caché
metadata_cache = MetadataCache()