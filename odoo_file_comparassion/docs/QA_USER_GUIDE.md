# Guía de Validación QA - Migración Odoo 19.0

## 👋 Introducción

¡Bienvenido/a al proceso de validación de la nueva versión de Odoo!

Tu participación es fundamental para asegurar que la migración a Odoo 19.0 sea exitosa. Esta guía te ayudará a validar que todas las funcionalidades que usas diariamente sigan funcionando correctamente.

**⏱ Tiempo estimado:** 4-6 horas (puedes distribuirlo en varios días)

**📅 Periodo de validación:** [Fecha inicio] - [Fecha fin]

---

## 🎯 Objetivos de esta Validación

1. **Verificar que tus procesos diarios funcionen correctamente**
2. **Identificar cualquier cambio o problema en las funcionalidades**
3. **Reportar bugs o comportamientos inesperados**
4. **Confirmar que los datos se muestran correctamente**

---

## 🚀 Antes de Comenzar

### Acceso al Ambiente QA

- **URL:** [https://qa.empresa.com]
- **Usuario:** [tu_usuario_habitual]
- **Contraseña:** [tu_contraseña_habitual]

### Importante

- ✅ **SÍ** puedes crear, modificar y eliminar datos de prueba
- ✅ **SÍ** puedes probar todos los flujos que normalmente usas
- ❌ **NO** estás en el sistema de producción (tus cambios no afectan datos reales)
- ❌ **NO** uses datos reales de clientes/proveedores sensibles

### Reporte de Problemas

**Canal de comunicación:** [Slack #qa-migracion / Email / WhatsApp]

**Contacto técnico:**
- Nombre: [Responsable QA]
- Teléfono: [Número]
- Horario: [Lunes-Viernes 9am-6pm]

---

## 📋 Casos de Uso a Validar

### Área: VENTAS

#### CU-V-001: Crear y confirmar una cotización

**📝 Descripción:** Crear una cotización nueva y confirmarla para convertirla en orden de venta.

**👣 Pasos:**

1. Ir a Ventas → Órdenes → Cotizaciones
2. Clic en "Crear"
3. Seleccionar cliente: [Cliente de prueba]
4. Agregar producto(s):
   - Producto: [Producto de prueba]
   - Cantidad: 5
   - Precio debe calcularse automáticamente
5. Revisar que los totales sean correctos
6. Clic en "Confirmar"
7. Verificar que el estado cambie a "Orden de venta"

**✅ Criterios de Aceptación:**

- [ ] La cotización se crea sin errores
- [ ] Los precios se calculan correctamente
- [ ] Los impuestos se aplican correctamente
- [ ] La confirmación cambia el estado correctamente
- [ ] Se genera el número de orden automáticamente

**❌ ¿Qué reportar si falla?**

- Si hay algún error al guardar
- Si los precios no se calculan
- Si el botón "Confirmar" no funciona
- Si el estado no cambia

---

#### CU-V-002: Crear factura desde orden de venta

**📝 Descripción:** Generar una factura a partir de una orden de venta confirmada.

**👣 Pasos:**

1. Abrir la orden de venta creada en CU-V-001
2. **IMPORTANTE:** Verificar el estado de facturación (este es un cambio nuevo en v19)
3. Clic en "Crear factura"
4. Seleccionar "Factura regular"
5. Clic en "Crear y ver factura"
6. Revisar que los datos coincidan con la orden
7. Clic en "Confirmar"

**✅ Criterios de Aceptación:**

- [ ] El botón "Crear factura" está disponible
- [ ] **El estado de facturación se muestra correctamente** (NUEVO)
- [ ] La factura se genera con los datos correctos
- [ ] Los montos coinciden con la orden de venta
- [ ] La confirmación de la factura funciona

**❌ ¿Qué reportar si falla?**

- Si el estado de facturación no aparece o es incorrecto
- Si no se puede crear la factura
- Si los montos no coinciden
- Cualquier error en pantalla

---

#### CU-V-003: Cancelar una orden de venta

**📝 Descripción:** Cancelar una orden de venta y verificar que el proceso funcione correctamente.

**👣 Pasos:**

1. Crear una nueva cotización (seguir pasos CU-V-001)
2. Confirmarla
3. Clic en "Cancelar"
4. Verificar que aparezca confirmación
5. Confirmar la cancelación
6. Verificar el estado final

**✅ Criterios de Aceptación:**

- [ ] El botón "Cancelar" está disponible
- [ ] Aparece mensaje de confirmación
- [ ] El estado cambia a "Cancelado"
- [ ] No se puede modificar la orden cancelada

**❌ ¿Qué reportar si falla?**

- Si no aparece el botón de cancelar
- Si la cancelación no funciona
- Si aún se puede editar después de cancelar

---

### Área: COMPRAS

#### CU-C-001: Crear solicitud de cotización

**📝 Descripción:** Crear una solicitud de cotización a proveedor.

**👣 Pasos:**

1. Ir a Compras → Órdenes → Solicitudes de cotización
2. Clic en "Crear"
3. Seleccionar proveedor: [Proveedor de prueba]
4. Agregar producto:
   - Producto: [Producto de prueba]
   - Cantidad: 10
5. Guardar
6. Clic en "Confirmar orden"

**✅ Criterios de Aceptación:**

- [ ] La solicitud se crea correctamente
- [ ] Los precios del proveedor se cargan automáticamente
- [ ] La confirmación funciona sin errores
- [ ] El estado cambia correctamente

**❌ ¿Qué reportar si falla?**

- Errores al crear la solicitud
- Precios que no se cargan
- Problemas al confirmar

---

#### CU-C-002: Cancelar orden de compra (CRÍTICO)

**📝 Descripción:** Intentar cancelar una orden de compra en diferentes estados.

**⚠️ IMPORTANTE:** Este proceso tiene validaciones nuevas que debemos verificar.

**👣 Pasos - Escenario 1 (Debe permitir cancelar):**

1. Crear orden de compra (CU-C-001)
2. Confirmarla
3. **NO recibir productos**
4. Clic en "Cancelar"
5. Verificar que se puede cancelar

**✅ Criterios de Aceptación Escenario 1:**

- [ ] El botón "Cancelar" está disponible
- [ ] La cancelación se completa sin errores
- [ ] El estado cambia a "Cancelado"

**👣 Pasos - Escenario 2 (Puede tener restricciones):**

1. Crear orden de compra
2. Confirmarla
3. **Recibir parcialmente los productos**
4. Intentar cancelar
5. **Anotar el comportamiento:** ¿Permite cancelar? ¿Muestra algún mensaje?

**✅ Criterios de Aceptación Escenario 2:**

- [ ] El sistema muestra un comportamiento claro
- [ ] Si bloquea, muestra mensaje explicativo
- [ ] Si permite, la cancelación funciona correctamente

**❌ ¿Qué reportar?**

- Si no aparece el botón de cancelar cuando debería
- Si permite cancelar cuando no debería
- Mensajes de error confusos
- Comportamientos diferentes a lo esperado

---

### Área: INVENTARIO

#### CU-I-001: Crear movimiento interno

**📝 Descripción:** Mover productos entre ubicaciones.

**👣 Pasos:**

1. Ir a Inventario → Operaciones → Transferencias
2. Clic en "Crear"
3. Tipo de operación: Transferencia interna
4. Ubicación origen: [WH/Stock]
5. Ubicación destino: [WH/Stock/Shelf 1]
6. Agregar producto y cantidad
7. Validar

**✅ Criterios de Aceptación:**

- [ ] El movimiento se crea correctamente
- [ ] Las ubicaciones se seleccionan sin problemas
- [ ] La validación funciona
- [ ] Los stocks se actualizan correctamente

---

#### CU-I-002: Ajuste de inventario

**📝 Descripción:** Realizar un ajuste de inventario.

**👣 Pasos:**

1. Ir a Inventario → Operaciones → Ajustes de inventario
2. Clic en "Crear"
3. Seleccionar producto
4. Ingresar cantidad contada
5. Validar ajuste

**✅ Criterios de Aceptación:**

- [ ] El ajuste se crea sin errores
- [ ] La cantidad se puede modificar
- [ ] La validación actualiza el stock
- [ ] El historial de movimientos se registra

---

#### CU-I-003: Consultar disponibilidad de producto

**📝 Descripción:** Verificar stock disponible de un producto.

**👣 Pasos:**

1. Ir a Inventario → Productos → Productos
2. Buscar producto: [Producto de prueba]
3. Abrir el producto
4. Revisar campos:
   - Cantidad disponible
   - Cantidad prevista
   - Ubicaciones
5. Clic en "Historial de movimientos"

**✅ Criterios de Aceptación:**

- [ ] Las cantidades se muestran correctamente
- [ ] El historial es accesible
- [ ] Los datos son coherentes con movimientos realizados

---

### Área: REPORTES

#### CU-R-001: Reporte de ventas

**📝 Descripción:** Generar y visualizar reporte de ventas.

**👣 Pasos:**

1. Ir a Ventas → Reportes → Ventas
2. Seleccionar filtro por fecha: [Último mes]
3. Agrupar por: Vendedor
4. Verificar que se muestren datos
5. Exportar a Excel

**✅ Criterios de Aceptación:**

- [ ] El reporte se genera correctamente
- [ ] Los filtros funcionan
- [ ] Los datos son coherentes
- [ ] La exportación funciona

---

#### CU-R-002: Valorización de inventario

**📝 Descripción:** Consultar valorización del inventario.

**👣 Pasos:**

1. Ir a Inventario → Reportes → Valorización de inventario
2. Verificar que se carguen los datos
3. Revisar totales
4. Exportar a PDF

**✅ Criterios de Aceptación:**

- [ ] El reporte carga sin errores
- [ ] Los montos son coherentes
- [ ] La exportación funciona

---

## 🐛 Formulario de Reporte de Bugs

Cuando encuentres un problema, repórtalo con la siguiente información:

### Información Básica

- **Fecha y hora:** [YYYY-MM-DD HH:MM]
- **Tu nombre:** [Nombre]
- **Caso de uso:** [CU-X-XXX]
- **Severidad:**
  - [ ] 🔴 **Crítico:** No puedo realizar mi trabajo
  - [ ] 🟡 **Alto:** Puedo hacer mi trabajo pero con dificultad
  - [ ] 🟢 **Medio:** Es un inconveniente menor
  - [ ] ⚪ **Bajo:** Es solo cosmético o poco frecuente

### Descripción del Problema

**¿Qué intentabas hacer?**
[Descripción]

**¿Qué pasó?**
[Descripción del error o comportamiento incorrecto]

**¿Qué esperabas que pasara?**
[Descripción del comportamiento esperado]

### Reproducir el Problema

**Pasos para reproducirlo:**
1. [Paso 1]
2. [Paso 2]
3. [Paso 3]

**¿Ocurre siempre o solo a veces?**
- [ ] Siempre
- [ ] A veces
- [ ] Solo ocurrió una vez

### Evidencia

**Captura de pantalla:**
[Adjuntar imagen si es posible]

**Mensaje de error (si aparece):**
```
[Copiar el mensaje exacto]
```

### Datos de Prueba Usados

**Cliente/Proveedor:** [Nombre]
**Producto:** [Nombre]
**Orden/Documento:** [Número de referencia]

---

## ✅ Checklist Final de Validación

### Antes de Finalizar

- [ ] Completé al menos 8 de los 11 casos de uso
- [ ] Reporté todos los problemas que encontré
- [ ] Adjunté capturas de pantalla a los bugs críticos
- [ ] Probé mis procesos más frecuentes
- [ ] Verifiqué que los datos se muestren correctamente

### Formulario de Confirmación

**Nombre:** [Tu nombre]
**Área:** [Ventas / Compras / Inventario / Administración]
**Fecha de finalización:** [YYYY-MM-DD]

**Resultado General:**
- [ ] ✅ **Aprobado:** Todo funciona correctamente, puedo trabajar sin problemas
- [ ] ⚠️ **Aprobado con observaciones:** Funciona, pero hay detalles menores a mejorar
- [ ] ❌ **No aprobado:** Hay problemas críticos que me impiden trabajar

**Comentarios adicionales:**
[Tus comentarios o sugerencias]

---

## 🙋 Preguntas Frecuentes

**P: ¿Qué pasa si no entiendo algún paso?**
R: Contacta al equipo técnico inmediatamente. No hay preguntas tontas.

**P: ¿Puedo crear datos de prueba?**
R: ¡Sí! Crea todos los que necesites. Este ambiente es para probar.

**P: ¿Qué hago si encuentro un error crítico?**
R: Repórtalo inmediatamente por WhatsApp/llamada al contacto técnico.

**P: ¿Necesito validar TODO en un solo día?**
R: No, puedes distribuir la validación en varios días durante el periodo establecido.

**P: ¿Qué pasa si no tengo tiempo de validar?**
R: Avisa al equipo QA para ajustar el cronograma o asignar a otra persona.

---

## 📞 Contactos de Soporte

| Rol | Nombre | Contacto | Horario |
|-----|--------|----------|---------|
| QA Lead | [Nombre] | [Email/Phone] | [Horario] |
| Soporte Técnico | [Nombre] | [Email/Phone] | [Horario] |
| Project Manager | [Nombre] | [Email/Phone] | [Horario] |

---

**¡Gracias por tu participación en este proceso! Tu validación es fundamental para el éxito de la migración. 🚀**
