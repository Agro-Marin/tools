# XML Formatter - Vauxoo Standard

## Migración a Prettier + plugin-xml

El formateador XML ha sido actualizado para seguir el estándar de **pre-commit-vauxoo**, utilizando **Prettier** con el plugin XML oficial.

## Configuración

### Dependencias
```bash
npm install prettier@2.7.1 @prettier/plugin-xml@2.2.0 --save-dev
```

### Configuración (.prettierrc.yml)
```yaml
bracketSpacing: false
printWidth: 119                    # Máximo 119 caracteres por línea
proseWrap: always
semi: true
trailingComma: "es5"
xmlWhitespaceSensitivity: "strict"  # Preserva espacios exactos
xmlSelfClosingSpace: true          # Espacio antes de /> 
```

## Uso

### Formatear archivo específico
```bash
python format_odoo_xml.py archivo.xml
```

### Formatear todos los XMLs
```bash
python format_odoo_xml.py --all
```

### Integración automática
El formatter se ejecuta automáticamente después del script de renaming para todos los archivos XML modificados.

## Ejemplo de formato

**Antes:**
```xml
<field name="move_sent_values" string="Sent" widget="badge" decoration-success="move_sent_values == 'sent'" decoration-danger="move_sent_values == 'not_sent'" column_invisible="context.get('default_move_type') not in ('out_invoice', 'out_refund', 'out_receipt')" optional="hide"/>
```

**Después (Prettier):**
```xml
<field
    name="move_sent_values"
    string="Sent"
    widget="badge"
    decoration-success="move_sent_values == 'sent'"
    decoration-danger="move_sent_values == 'not_sent'"
    column_invisible="context.get('default_move_type') not in ('out_invoice', 'out_refund', 'out_receipt')"
    optional="hide"
/>
```

## Ventajas del estándar Vauxoo

- ✅ **Compatibilidad**: Mismos estándares que pre-commit-vauxoo
- ✅ **Consistencia**: Formato uniforme en toda la organización
- ✅ **Mantenimiento**: Utiliza herramientas estándar de la industria
- ✅ **Flexibilidad**: Configuración a través de .prettierrc.yml
- ✅ **Performance**: Prettier es más rápido que nuestro parser personalizado

## Migración completada

- [x] Instalación de Prettier + plugin-xml
- [x] Configuración .prettierrc.yml según estándar Vauxoo
- [x] Actualización del script format_odoo_xml.py
- [x] Integración en el script de renaming
- [x] Pruebas con archivos reales de Odoo