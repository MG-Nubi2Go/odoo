# Módulo de Gestión de Usuarios Nybble

## Descripción General

El módulo **Nybble User Management** es una extensión personalizada de Odoo que
proporciona capacidades avanzadas de gestión de usuarios con controles de seguridad
mejorados y permisos de acceso granulares. Este módulo está diseñado para Odoo 18.0 y
sigue los principios de Desarrollo Dirigido por Pruebas (TDD).

## Características

### 🔐 Seguridad Mejorada

- **Control de Acceso Granular**: Grupo de usuarios personalizado con permisos
  específicos
- **Restricciones Administrativas**: Limita el acceso a configuraciones críticas del
  sistema
- **Modificaciones Dinámicas de Vistas**: Restringe automáticamente la visibilidad de
  grupos administrativos

### 👥 Gestión de Usuarios

- **Administración de Usuarios**: Gestión completa del ciclo de vida de usuarios
- **Campos de Token de Partner**: Modelo de partner extendido con capacidades de token
  de registro
- **Gestión de Plantillas de Email**: Administración integrada de plantillas de correo

### 🛡️ Grupos de Seguridad

- **Grupo de Gestión de Usuarios**: Grupo dedicado para administración de usuarios
- **Permisos Restringidos**: Permisos de lectura, escritura y creación sin derechos de
  eliminación
- **Organización por Categorías**: Categoría "Permisos adicionales" para mejor
  organización

## Instalación

### Prerrequisitos

- Odoo 18.0 o superior
- Base de datos PostgreSQL
- Python 3.8+

### Pasos de Instalación

1. **Clonar o Descargar** el módulo a tu ruta de addons de Odoo:

   ```bash
   cp -r nybble_user_management /ruta/a/odoo/addons/
   ```

2. **Actualizar Lista de Módulos** en Odoo:

   - Ir a Aplicaciones → Actualizar Lista de Aplicaciones
   - O reiniciar el servidor Odoo

3. **Instalar el Módulo**:

   - Buscar "Gestión de Usuarios" en el menú de Aplicaciones
   - Hacer clic en Instalar

4. **Configurar Seguridad**:
   - Asignar usuarios al grupo "Gestión de Usuarios"
   - Configurar derechos de acceso según sea necesario

## Estructura del Módulo

```
nybble_user_management/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── res_users.py
│   └── res_partner.py
├── security/
│   ├── ir.model.access.csv
│   └── user_group_views.xml
├── views/
│   ├── res_user_views.xml
│   └── user_management_menus.xml
├── tests/
│   ├── __init__.py
│   └── test_res_groups.py
└── static/
    └── description/
        └── icon.png
```

## Documentación Técnica

### Modelos

#### GroupsView (res.groups)

**Archivo**: `models/res_users.py`

Extiende el modelo `res.groups` para modificar dinámicamente las vistas de grupos de
usuarios.

**Métodos Principales**:

- `_update_user_groups_view()`: Modifica la vista de grupos de usuarios para excluir
  categorías de administración

**Características**:

- Manipulación dinámica de vistas XML usando lxml
- Restringe la visibilidad de grupos administrativos
- Mantiene la funcionalidad original mientras agrega capas de seguridad

#### ResPartner (res.partner)

**Archivo**: `models/res_partner.py`

Extiende el modelo `res.partner` con campos de token de registro.

**Nuevos Campos**:

- `signup_token`: Campo computado para tokens de registro
- `signup_type`: Clasificación del tipo de token
- `signup_expiration`: Fecha y hora de expiración del token

**Seguridad**: Todos los campos están restringidos a gerentes ERP y grupos de gestión de
usuarios.

### Configuración de Seguridad

#### Grupo de Gestión de Usuarios

- **Nombre**: "Gestión de Usuarios"
- **Categoría**: "Permisos adicionales"
- **Descripción**: Permite la administración de usuarios sin acceso crítico al sistema

#### Derechos de Acceso

- **Modelo**: res.users
- **Permisos**: Lectura (1), Escritura (1), Creación (1), Eliminación (0)
- **Grupo**: nybble_user_management.group_user_management

### Vistas

#### Estructura de Menús

- **Menú Principal**: "Ajustes Usuarios" (secuencia: 1000)
- **Submenús**:
  - Usuarios (redirige a gestión de usuarios base)
  - Plantillas de Correos (redirige a gestión de plantillas de correo)

#### Modificaciones de Vista de Formulario

- Hereda la vista de formulario de usuarios base
- Modifica las restricciones de grupo del campo partner_id
- Mejora la accesibilidad para el grupo de gestión de usuarios

## Uso

### Asignar Permisos de Gestión de Usuarios

1. **Navegar a Configuración** → Usuarios y Empresas → Usuarios
2. **Seleccionar un usuario** para modificar
3. **Agregar a Grupos**: Seleccionar "Gestión de Usuarios" de Permisos adicionales
4. **Guardar** el registro de usuario

### Gestionar Usuarios

1. **Acceder a Gestión de Usuarios**:

   - Ir a Ajustes Usuarios → Usuarios
   - Solo visible para usuarios con grupo de Gestión de Usuarios

2. **Crear Nuevos Usuarios**:

   - Hacer clic en botón "Crear"
   - Completar campos requeridos
   - Asignar grupos apropiados
   - Guardar el registro

3. **Editar Usuarios Existentes**:
   - Seleccionar usuario de la lista
   - Modificar campos según sea necesario
   - Guardar cambios

### Gestión de Plantillas de Email

1. **Acceder a Plantillas**:
   - Ir a Ajustes Usuarios → Plantillas de Correos
   - Gestionar plantillas de correo para comunicaciones de usuarios

## Pruebas

El módulo incluye pruebas unitarias completas siguiendo los principios TDD.

### Ejecutar Pruebas

```bash
# Ejecutar archivo de prueba específico
python -m pytest /ruta/a/odoo/addons/nybble_user_management/tests/

# Ejecutar con framework de pruebas de Odoo
./odoo-bin -d tu_base_de_datos -i nybble_user_management --test-enable
```

### Cobertura de Pruebas

- **Pruebas de Seguridad**: Verificar control de acceso y permisos
- **Pruebas de Vistas**: Validar modificaciones dinámicas de vistas
- **Pruebas de Grupos**: Asegurar restricciones apropiadas de grupos

## Configuración

### Opciones de Personalización

1. **Modificar Permisos de Grupo**:

   - Editar `security/ir.model.access.csv`
   - Ajustar niveles de permisos según sea necesario

2. **Agregar Nuevos Elementos de Menú**:

   - Modificar `views/user_management_menus.xml`
   - Agregar nuevos registros de menuitem

3. **Extender Campos de Partner**:
   - Modificar `models/res_partner.py`
   - Agregar nuevos campos computados o métodos

## Solución de Problemas

### Problemas Comunes

1. **Módulo No Se Instala**:

   - Verificar compatibilidad de versión de Odoo (18.0+)
   - Verificar permisos de archivos
   - Asegurar que todas las dependencias estén instaladas

2. **Errores de Permisos**:

   - Verificar que el usuario esté asignado al grupo de Gestión de Usuarios
   - Verificar configuración de derechos de acceso
   - Revisar asignaciones de grupos de seguridad

3. **Vista No Se Carga**:
   - Limpiar caché del navegador
   - Reiniciar servidor Odoo
   - Verificar errores de sintaxis XML

### Modo Debug

Habilitar modo debug para información detallada de errores:

```bash
./odoo-bin -d tu_base_de_datos --dev=all
```

## Desarrollo

### Agregar Nuevas Funcionalidades

1. **Seguir Enfoque TDD**:

   - Escribir pruebas primero
   - Implementar funcionalidad
   - Verificar cobertura de pruebas

2. **Usar unittest.mock**:

   - Aislar componentes para pruebas
   - Mockear dependencias externas
   - Seguir convenciones de pruebas de Odoo

3. **Mantener Estándares de Código**:
   - Seguir PEP 8 para Python
   - Usar nombres descriptivos
   - Agregar docstrings completos

### Estilo de Código

- **Python**: Compatible con PEP 8
- **XML**: Indentación y formato apropiados
- **Documentación**: Docstrings estilo Google
- **Pruebas**: Patrón Arrange-Act-Assert

## Dependencias

- **Odoo**: 18.0.1.0.0
- **Python**: 3.8+
- **PostgreSQL**: 12+
- **lxml**: Para manipulación XML

## Licencia

Este módulo está licenciado bajo LGPL-3.

## Soporte

Para soporte técnico o solicitudes de funcionalidades:

- **Autor**: Nybble Group
- **Sitio Web**: https://www.nybblegroup.com
- **Documentación**: Este archivo README

## Registro de Cambios

### Versión 18.0.1.0.0

- Lanzamiento inicial
- Implementación de grupo de gestión de usuarios
- Modificaciones dinámicas de vistas
- Campos de token de partner
- Suite completa de pruebas

## Contribución

1. Hacer fork del repositorio
2. Crear rama de funcionalidad
3. Seguir enfoque TDD
4. Agregar pruebas completas
5. Enviar pull request

---

**Nota**: Este módulo está diseñado para entornos empresariales que requieren
capacidades mejoradas de gestión de usuarios con controles de seguridad estrictos.
