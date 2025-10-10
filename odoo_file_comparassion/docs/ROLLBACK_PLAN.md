# Plan de Rollback - Migración Odoo 19.0

## 🎯 Objetivo

Este documento describe el procedimiento de rollback (reversión) en caso de que la migración a Odoo 19.0 falle o presente problemas críticos que impidan la operación normal del sistema.

---

## 🚨 Criterios para Activar Rollback

Ejecutar el rollback si se cumple **uno o más** de los siguientes criterios:

### Criterios Técnicos

- [ ] **La base de datos no arranca** después de la migración
- [ ] **Módulos críticos fallan al cargar** (sale, purchase, stock)
- [ ] **Errores masivos en logs** (>100 errores por minuto)
- [ ] **Performance degradada** (>70% más lento que v18)
- [ ] **Pérdida de datos** detectada en tablas críticas

### Criterios de Negocio

- [ ] **Usuarios no pueden realizar ventas** (bloqueante total)
- [ ] **Usuarios no pueden realizar compras** (bloqueante total)
- [ ] **Usuarios no pueden validar inventario** (bloqueante total)
- [ ] **>30% de usuarios reportan bugs críticos** en primeras 2 horas
- [ ] **Tiempo de downtime excede 12 horas**

### Criterios de Decisión

**Responsable de decisión:** [Nombre - Project Lead]
**Contactos de emergencia:** [Lista de contactos]

**Proceso de decisión:**
1. Evaluar severidad del problema
2. Consultar con equipo técnico (estimación de tiempo de fix)
3. Consultar con stakeholders (impacto en negocio)
4. **Decisión:** Fix forward vs Rollback
   - Si fix estimado < 2 horas → Intentar fix
   - Si fix estimado > 2 horas → Ejecutar rollback

---

## 📋 Pre-requisitos para Rollback

### Backups Requeridos

Verificar que existan los siguientes backups **ANTES** de iniciar la migración:

- [ ] **Backup de base de datos** (formato .sql o .dump)
  - Ubicación: `/backups/odoo/db_backup_pre_migration_YYYYMMDD.sql`
  - Tamaño esperado: ~[XX GB]
  - Timestamp: [YYYY-MM-DD HH:MM:SS]
  - MD5 checksum: [hash]

- [ ] **Backup de filestore** (archivos adjuntos)
  - Ubicación: `/backups/odoo/filestore_backup_YYYYMMDD.tar.gz`
  - Tamaño esperado: ~[XX GB]
  - Timestamp: [YYYY-MM-DD HH:MM:SS]
  - MD5 checksum: [hash]

- [ ] **Backup de código v18.2-marin**
  - Branch git: `saas-18.2-marin`
  - Commit hash: [hash]
  - Tag: `pre-migration-v19-YYYYMMDD`

- [ ] **Backup de configuraciones**
  - Archivo de configuración Odoo: `odoo.conf`
  - Nginx/Apache configs
  - Variables de entorno
  - Ubicación: `/backups/odoo/configs_backup_YYYYMMDD.tar.gz`

### Verificación de Backups

**CRÍTICO:** Ejecutar estas verificaciones antes de la migración.

```bash
# 1. Verificar existencia de backups
ls -lh /backups/odoo/db_backup_pre_migration_*.sql
ls -lh /backups/odoo/filestore_backup_*.tar.gz
ls -lh /backups/odoo/configs_backup_*.tar.gz

# 2. Verificar integridad de backup de BD
pg_restore --list /backups/odoo/db_backup_pre_migration_YYYYMMDD.sql | head -20

# 3. Verificar integridad de filestore
tar -tzf /backups/odoo/filestore_backup_YYYYMMDD.tar.gz | head -20

# 4. Verificar checksums
md5sum /backups/odoo/db_backup_pre_migration_YYYYMMDD.sql
md5sum /backups/odoo/filestore_backup_YYYYMMDD.tar.gz
```

---

## ⏱ Tiempo Estimado de Rollback

| Componente | Tiempo Estimado |
|------------|-----------------|
| Detener servicios | 5 min |
| Restaurar base de datos | 30-60 min |
| Restaurar filestore | 15-30 min |
| Restaurar código | 10 min |
| Restaurar configuraciones | 5 min |
| Iniciar servicios | 10 min |
| Verificación | 15 min |
| **TOTAL** | **~2 horas** |

---

## 📝 Procedimiento de Rollback

### Fase 1: Preparación (5 min)

#### 1.1 Notificar al Equipo

```bash
# Enviar notificación a todos los canales
# - Email a usuarios
# - Mensaje en Slack/WhatsApp
# - Actualizar página de status
```

**Mensaje template:**
```
🚨 ALERTA: Iniciando proceso de rollback de Odoo 19.0

Debido a [razón breve], estamos revirtiendo a Odoo 18.2.

Tiempo estimado: 2 horas
Estado actual: Preparando rollback
Próxima actualización: [HH:MM]

Equipo Técnico
```

#### 1.2 Acceder al Servidor

```bash
# SSH al servidor de producción
ssh usuario@servidor-produccion

# Verificar usuario y permisos
whoami
sudo -l

# Ir al directorio de trabajo
cd /opt/odoo
```

#### 1.3 Crear Snapshot de Estado Actual (Opcional pero recomendado)

```bash
# Por si necesitamos analizar qué falló
sudo mkdir -p /backups/odoo/failed_migration_YYYYMMDD
sudo cp -r /opt/odoo/odoo.conf /backups/odoo/failed_migration_YYYYMMDD/
sudo tail -1000 /var/log/odoo/odoo-server.log > /backups/odoo/failed_migration_YYYYMMDD/last_1000_logs.txt
```

---

### Fase 2: Detener Servicios (5 min)

#### 2.1 Activar Modo Mantenimiento

```bash
# Si Odoo está arriba, activar modo mantenimiento desde UI
# Alternativamente, desde línea de comandos:
sudo systemctl stop odoo
```

#### 2.2 Detener Servicios Relacionados

```bash
# Detener Nginx/Apache
sudo systemctl stop nginx
# O si usas Apache:
# sudo systemctl stop apache2

# Detener workers de Odoo (si existen)
sudo pkill -f "openerp-gevent"

# Verificar que no hay procesos de Odoo corriendo
ps aux | grep odoo
ps aux | grep python | grep openerp
```

#### 2.3 Verificar que Servicios Estén Detenidos

```bash
sudo systemctl status odoo
sudo systemctl status nginx

# No debe haber procesos de Odoo
ps aux | grep odoo | grep -v grep
# Resultado esperado: ninguna línea
```

---

### Fase 3: Restaurar Base de Datos (30-60 min)

#### 3.1 Desconectar Usuarios de la BD (si aplica)

```bash
# Conectar a PostgreSQL
sudo -u postgres psql

# Terminar conexiones activas a la BD
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'odoo_production'
  AND pid <> pg_backend_pid();

# Salir de psql
\q
```

#### 3.2 Hacer Backup de BD Migrada (por si necesitamos analizarla)

```bash
# Backup de la BD que falló (para debugging)
sudo -u postgres pg_dump odoo_production > /backups/odoo/failed_migration_YYYYMMDD/db_failed.sql
```

#### 3.3 Eliminar BD Actual

```bash
# Conectar a PostgreSQL
sudo -u postgres psql

# Eliminar la base de datos
DROP DATABASE odoo_production;

# Verificar que fue eliminada
\l

# Salir
\q
```

#### 3.4 Recrear BD Vacía

```bash
sudo -u postgres psql

# Crear BD vacía
CREATE DATABASE odoo_production OWNER odoo ENCODING 'UTF8';

# Verificar
\l

# Salir
\q
```

#### 3.5 Restaurar Backup

```bash
# Restaurar desde backup
sudo -u postgres psql odoo_production < /backups/odoo/db_backup_pre_migration_YYYYMMDD.sql

# Esto puede tardar 30-60 minutos dependiendo del tamaño de la BD
# Monitorear progreso en otra terminal:
# watch -n 10 'sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname = '"'odoo_production'"';"'
```

#### 3.6 Verificar Restauración

```bash
sudo -u postgres psql odoo_production

-- Verificar tablas principales
SELECT count(*) FROM res_partner;
SELECT count(*) FROM sale_order;
SELECT count(*) FROM purchase_order;
SELECT count(*) FROM stock_move;

-- Verificar versión de módulos (debe ser 18.2)
SELECT name, state, latest_version
FROM ir_module_module
WHERE name IN ('sale', 'purchase', 'stock')
AND state = 'installed';

-- Salir
\q
```

---

### Fase 4: Restaurar Filestore (15-30 min)

#### 4.1 Hacer Backup de Filestore Migrado (para análisis)

```bash
# Renombrar filestore actual
sudo mv /opt/odoo/.local/share/Odoo/filestore/odoo_production \
        /opt/odoo/.local/share/Odoo/filestore/odoo_production_failed_YYYYMMDD
```

#### 4.2 Restaurar Filestore desde Backup

```bash
# Extraer backup de filestore
sudo tar -xzf /backups/odoo/filestore_backup_YYYYMMDD.tar.gz \
         -C /opt/odoo/.local/share/Odoo/filestore/

# Verificar extracción
ls -lh /opt/odoo/.local/share/Odoo/filestore/odoo_production/ | head -20
```

#### 4.3 Ajustar Permisos

```bash
# Asegurar que Odoo tenga permisos
sudo chown -R odoo:odoo /opt/odoo/.local/share/Odoo/filestore/odoo_production
sudo chmod -R 755 /opt/odoo/.local/share/Odoo/filestore/odoo_production

# Verificar permisos
ls -la /opt/odoo/.local/share/Odoo/filestore/odoo_production/
```

---

### Fase 5: Restaurar Código (10 min)

#### 5.1 Volver a Código v18.2-marin

```bash
# Core Odoo
cd /opt/odoo/odoo
git fetch --all
git checkout saas-18.2-marin
git pull origin saas-18.2-marin

# Verificar commit
git log -1

# Enterprise
cd /opt/odoo/enterprise
git checkout saas-18.2-marin
git pull origin saas-18.2-marin

# Add-ons custom
cd /opt/odoo/custom-addons
git checkout saas-18.2-marin
git pull origin saas-18.2-marin
```

#### 5.2 Verificar Versión de Código

```bash
# Verificar que estemos en v18
cd /opt/odoo/odoo
grep "^version" odoo/release.py
# Resultado esperado: version = '18.0'

# Verificar hash del commit
git rev-parse HEAD
# Debe coincidir con el hash pre-migración
```

---

### Fase 6: Restaurar Configuraciones (5 min)

#### 6.1 Restaurar odoo.conf

```bash
# Extraer backup de configuraciones
sudo tar -xzf /backups/odoo/configs_backup_YYYYMMDD.tar.gz -C /tmp/

# Restaurar odoo.conf
sudo cp /tmp/odoo.conf /opt/odoo/odoo.conf

# Verificar contenido
cat /opt/odoo/odoo.conf | grep "^db_name"
# Debe mostrar: db_name = odoo_production
```

#### 6.2 Restaurar Configs de Nginx/Apache

```bash
# Nginx
sudo cp /tmp/nginx/sites-available/odoo /etc/nginx/sites-available/odoo
sudo nginx -t  # Verificar sintaxis

# Apache (si aplica)
# sudo cp /tmp/apache2/sites-available/odoo.conf /etc/apache2/sites-available/odoo.conf
# sudo apache2ctl configtest
```

---

### Fase 7: Iniciar Servicios (10 min)

#### 7.1 Iniciar Odoo

```bash
# Iniciar servicio de Odoo
sudo systemctl start odoo

# Monitorear logs en tiempo real
sudo tail -f /var/log/odoo/odoo-server.log

# Buscar líneas como:
# "odoo.modules.loading: Modules loaded."
# "odoo.service.server: HTTP service (werkzeug) running on..."
```

#### 7.2 Verificar que Odoo Arrancó Correctamente

```bash
# Verificar status del servicio
sudo systemctl status odoo

# Verificar que está escuchando en el puerto correcto
sudo netstat -tlnp | grep 8069

# Verificar que no hay errores críticos en logs
sudo tail -100 /var/log/odoo/odoo-server.log | grep -i error
sudo tail -100 /var/log/odoo/odoo-server.log | grep -i critical
```

#### 7.3 Iniciar Nginx/Apache

```bash
# Iniciar Nginx
sudo systemctl start nginx
sudo systemctl status nginx

# Verificar configuración
sudo nginx -t
```

---

### Fase 8: Verificación Funcional (15 min)

#### 8.1 Tests de Humo Automatizados

```bash
# Verificar que la BD responde
sudo -u postgres psql odoo_production -c "SELECT count(*) FROM res_users;"

# Verificar que Odoo responde HTTP
curl -I http://localhost:8069/web/database/selector
# Debe retornar: HTTP/1.1 200 OK

# Verificar que módulos están cargados
curl -s http://localhost:8069/web/webclient/version_info | python3 -m json.tool
```

#### 8.2 Verificación Manual UI

**Abrir navegador y verificar:**

1. **Login funciona**
   - URL: https://odoo.empresa.com
   - Usuario: admin
   - Debe poder iniciar sesión

2. **Menú principal carga**
   - Verificar que aparecen módulos: Ventas, Compras, Inventario

3. **Datos visibles**
   - Ir a Ventas → Órdenes
   - Verificar que se muestran órdenes recientes
   - Abrir una orden → Verificar datos completos

4. **Funcionalidad básica**
   - Crear una cotización de prueba
   - Agregar producto
   - Guardar
   - Si funciona → Rollback exitoso

#### 8.3 Verificar Versión

```bash
# Desde la UI de Odoo:
# Ir a Settings (Configuración)
# Scroll hasta abajo
# Verificar versión: "Odoo 18.0" (debe decir 18, NO 19)
```

---

### Fase 9: Comunicación y Cierre (5 min)

#### 9.1 Notificar Finalización

**Mensaje template:**
```
✅ ROLLBACK COMPLETADO

El sistema ha sido revertido exitosamente a Odoo 18.2.

Estado: Operacional
Versión: Odoo 18.2-marin
Tiempo de rollback: [HH:MM]

Pueden reanudar sus operaciones normales.

Disculpas por las molestias.
Equipo Técnico
```

#### 9.2 Desactivar Modo Mantenimiento

```bash
# Desde UI de Odoo o configuración
# O reiniciar servicios si fue necesario
```

#### 9.3 Documentar el Incidente

Crear reporte post-mortem con:

- **Timestamp de eventos:**
  - Inicio de migración: [YYYY-MM-DD HH:MM]
  - Detección de problema: [YYYY-MM-DD HH:MM]
  - Decisión de rollback: [YYYY-MM-DD HH:MM]
  - Inicio de rollback: [YYYY-MM-DD HH:MM]
  - Finalización de rollback: [YYYY-MM-DD HH:MM]

- **Causa raíz del problema:**
  - [Descripción detallada]

- **Logs relevantes:**
  - [Adjuntar extractos de logs]

- **Acciones correctivas:**
  - [Qué se hará diferente la próxima vez]

---

## 🧪 Prueba de Rollback (Obligatoria)

**IMPORTANTE:** Ejecutar una prueba de rollback en ambiente QA **ANTES** de la migración en producción.

### Procedimiento de Prueba

```bash
# 1. En ambiente QA
# 2. Hacer backup de BD y filestore
# 3. Migrar a v19 (simular migración)
# 4. INMEDIATAMENTE ejecutar rollback siguiendo este plan
# 5. Verificar que el rollback funciona en < 2 horas
# 6. Documentar tiempo real vs estimado
# 7. Ajustar plan si es necesario
```

### Checklist de Prueba

- [ ] Backup se crea correctamente
- [ ] Restauración de BD funciona
- [ ] Restauración de filestore funciona
- [ ] Código se revierte correctamente
- [ ] Servicios arrancan sin errores
- [ ] UI es accesible
- [ ] Datos están intactos
- [ ] Tiempo total < 2 horas

---

## 📞 Contactos de Emergencia

| Rol | Nombre | Teléfono | Email | Disponibilidad |
|-----|--------|----------|-------|----------------|
| Project Lead | [Nombre] | [Phone] | [Email] | 24/7 durante migración |
| DevOps Lead | [Nombre] | [Phone] | [Email] | 24/7 durante migración |
| DBA | [Nombre] | [Phone] | [Email] | 24/7 durante migración |
| Sysadmin | [Nombre] | [Phone] | [Email] | 24/7 durante migración |

---

## 📚 Scripts de Rollback

### Script Completo de Rollback (Usar con precaución)

```bash
#!/bin/bash
# rollback_odoo_v19.sh
# USO: sudo bash rollback_odoo_v19.sh YYYYMMDD
# YYYYMMDD = fecha del backup a restaurar

set -e  # Exit on error

BACKUP_DATE=$1
if [ -z "$BACKUP_DATE" ]; then
    echo "ERROR: Debe proporcionar fecha de backup (YYYYMMDD)"
    exit 1
fi

echo "🚨 INICIANDO ROLLBACK - Fecha backup: $BACKUP_DATE"
echo "Presione CTRL+C en los próximos 10 segundos para cancelar..."
sleep 10

# 1. Detener servicios
echo "⏸ Deteniendo servicios..."
sudo systemctl stop odoo
sudo systemctl stop nginx

# 2. Hacer snapshot de estado fallido
echo "📸 Creando snapshot de estado fallido..."
sudo mkdir -p /backups/odoo/failed_migration_$(date +%Y%m%d_%H%M%S)
sudo cp /opt/odoo/odoo.conf /backups/odoo/failed_migration_$(date +%Y%m%d_%H%M%S)/
sudo tail -1000 /var/log/odoo/odoo-server.log > /backups/odoo/failed_migration_$(date +%Y%m%d_%H%M%S)/last_logs.txt

# 3. Restaurar BD
echo "💾 Restaurando base de datos..."
sudo -u postgres psql -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'odoo_production' AND pid <> pg_backend_pid();"
sudo -u postgres psql -c "DROP DATABASE IF EXISTS odoo_production;"
sudo -u postgres psql -c "CREATE DATABASE odoo_production OWNER odoo ENCODING 'UTF8';"
sudo -u postgres psql odoo_production < /backups/odoo/db_backup_pre_migration_${BACKUP_DATE}.sql

# 4. Restaurar filestore
echo "📁 Restaurando filestore..."
sudo mv /opt/odoo/.local/share/Odoo/filestore/odoo_production /opt/odoo/.local/share/Odoo/filestore/odoo_production_failed_$(date +%Y%m%d_%H%M%S)
sudo tar -xzf /backups/odoo/filestore_backup_${BACKUP_DATE}.tar.gz -C /opt/odoo/.local/share/Odoo/filestore/
sudo chown -R odoo:odoo /opt/odoo/.local/share/Odoo/filestore/odoo_production

# 5. Restaurar código
echo "📦 Restaurando código v18.2-marin..."
cd /opt/odoo/odoo && git checkout saas-18.2-marin
cd /opt/odoo/enterprise && git checkout saas-18.2-marin
cd /opt/odoo/custom-addons && git checkout saas-18.2-marin

# 6. Iniciar servicios
echo "▶️ Iniciando servicios..."
sudo systemctl start odoo
sleep 10
sudo systemctl start nginx

# 7. Verificar
echo "✅ Verificando..."
sudo systemctl status odoo --no-pager
curl -I http://localhost:8069/web/database/selector

echo "✅ ROLLBACK COMPLETADO"
echo "⚠️ Verificar manualmente que la UI funciona correctamente"
```

---

## ✅ Checklist Final de Rollback

- [ ] Backups verificados antes de migración
- [ ] Equipo notificado del inicio de rollback
- [ ] Servicios detenidos correctamente
- [ ] Base de datos restaurada y verificada
- [ ] Filestore restaurado y verificado
- [ ] Código revertido a v18.2-marin
- [ ] Configuraciones restauradas
- [ ] Servicios iniciados sin errores
- [ ] Tests de humo pasaron
- [ ] Verificación manual UI exitosa
- [ ] Versión confirmada: Odoo 18.0
- [ ] Usuarios notificados de finalización
- [ ] Post-mortem documentado
- [ ] Lecciones aprendidas registradas

---

**Última actualización:** 2025-10-07
**Versión del documento:** 1.0
**Responsable:** [Nombre]
