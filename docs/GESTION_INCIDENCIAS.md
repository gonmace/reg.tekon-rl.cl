# Gestión de Incidencias de Componentes

## 📋 Descripción

Este documento explica cómo gestionar las incidencias (pesos) de los componentes dentro de los grupos en la aplicación `proyectos`. La incidencia representa el porcentaje de importancia de cada componente dentro de un grupo y debe sumar 100%.

## 🏗️ Estructura de Modelos

### Componente
- **Propósito**: Componente base reutilizable
- **Campos**: `nombre`
- **Uso**: Se puede usar en múltiples grupos con diferentes incidencias

### GrupoComponentes
- **Propósito**: Grupo de componentes (estructura reutilizable)
- **Campos**: `nombre`
- **Uso**: Define una estructura de componentes con sus incidencias

### ComponenteGrupo
- **Propósito**: Relación entre grupo y componente con incidencia
- **Campos**: 
  - `grupo`: ForeignKey a GrupoComponentes
  - `componente`: ForeignKey a Componente
  - `incidencia`: DecimalField (porcentaje 0-100)
- **Validación**: La suma de incidencias debe ser 100%

## 🎯 Dónde Configurar las Incidencias

### 1. Django Admin (Interfaz Web)

**URL**: `/admin/proyectos/grupocomponentes/`

#### Ventajas:
- ✅ Interfaz visual intuitiva
- ✅ Validación automática
- ✅ Vista previa del balance
- ✅ Gestión completa de grupos y componentes

#### Cómo usar:
1. Ir a **Admin > Proyectos > Grupos de componentes**
2. Crear nuevo grupo o editar existente
3. Agregar componentes con sus incidencias
4. El sistema valida automáticamente que sume 100%

### 2. Comandos de Gestión (Línea de Comandos)

#### Listar Grupos Existentes
```bash
# Listar todos los grupos
python manage.py listar_grupos

# Listar grupo específico
python manage.py listar_grupos --grupo "Fundaciones"

# Información detallada
python manage.py listar_grupos --detallado

# Ver componentes disponibles
python manage.py listar_grupos --componentes
```

#### Configurar Nuevo Grupo
```bash
# Crear grupo con componentes existentes
python manage.py configurar_grupo \
  --grupo "Mi Grupo" \
  --componentes "Componente A:30" "Componente B:40" "Componente C:30"

# Crear grupo con componentes nuevos
python manage.py configurar_grupo \
  --grupo "Nuevo Grupo" \
  --componentes "Nuevo A:25" "Nuevo B:35" "Nuevo C:40" \
  --crear-componentes

# Forzar configuración sin validar 100%
python manage.py configurar_grupo \
  --grupo "Grupo Incompleto" \
  --componentes "A:50" "B:30" \
  --forzar
```

### 3. Código Python (Programáticamente)

```python
from proyectos.models import Componente, GrupoComponentes, ComponenteGrupo

# Crear componentes
componente_a = Componente.objects.create(nombre="Componente A")
componente_b = Componente.objects.create(nombre="Componente B")

# Crear grupo
grupo = GrupoComponentes.objects.create(nombre="Mi Grupo")

# Asignar incidencias
ComponenteGrupo.objects.create(
    grupo=grupo,
    componente=componente_a,
    incidencia=60.0
)
ComponenteGrupo.objects.create(
    grupo=grupo,
    componente=componente_b,
    incidencia=40.0
)
```

## 🔍 Validaciones y Control de Calidad

### Validaciones Automáticas
- ✅ **Rango**: Incidencia entre 0% y 100%
- ✅ **Suma total**: Debe sumar exactamente 100%
- ✅ **Unicidad**: Un componente solo puede aparecer una vez por grupo
- ✅ **Integridad**: Validación de claves foráneas

### Estados de Balance
- 🟢 **Balanceado**: Suma exactamente 100%
- 🟡 **Incompleto**: Suma menos de 100%
- 🔴 **Excede**: Suma más de 100%

### Indicadores Visuales
En el admin de Django, cada grupo muestra:
- **Estado del Balance**: Color-coded (verde/amarillo/rojo)
- **Porcentaje Total**: Suma actual de incidencias
- **Número de Componentes**: Cantidad de componentes en el grupo

## 📊 Ejemplos de Configuración

### Grupo "Fundaciones"
```
• Replanteo y Trazado: 10%
• Excavación para la fundación: 25%
• Enferradura de la fundación: 35%
• Hormigonado de la fundación: 30%
Total: 100% ✅
```

### Grupo "Sistemas Eléctricos"
```
• Sistema Eléctrico: 40%
• Linea Electica definitiva: 30%
• Sistema puesta a tierra: 30%
Total: 100% ✅
```

### Grupo "Torres Completas"
```
• Cierre perimetral: 5%
• Replanteo y Trazado: 5%
• Excavación para la fundación: 5%
• Enferradura de la fundación: 15%
• Hormigonado de la fundación: 15%
• Relleno y compactado: 5%
• Instalación de faenas: 5%
• Losa Radier de Equipos: 5%
• Montaje de la Torre: 15%
• Sistema Eléctrico: 5%
• Linea Electica definitiva: 10%
• Sistema puesta a tierra: 5%
• Trabajos Finales / Adicionales: 5%
Total: 100% ✅
```

## 🚀 Mejores Prácticas

### 1. Planificación
- ✅ Definir todos los componentes antes de crear grupos
- ✅ Establecer incidencias basadas en criterios técnicos
- ✅ Documentar el razonamiento de cada incidencia

### 2. Validación
- ✅ Verificar que la suma sea exactamente 100%
- ✅ Revisar que las incidencias sean realistas
- ✅ Validar que los componentes sean apropiados para el grupo

### 3. Mantenimiento
- ✅ Revisar periódicamente el balance de los grupos
- ✅ Actualizar incidencias según cambios en el proyecto
- ✅ Documentar cambios en la configuración

### 4. Nomenclatura
- ✅ Usar nombres descriptivos para grupos
- ✅ Mantener consistencia en nombres de componentes
- ✅ Evitar duplicados o nombres confusos

## 🔧 Comandos Útiles

### Verificar Estado del Sistema
```bash
# Verificar que no hay errores
python manage.py check

# Listar grupos con problemas
python manage.py listar_grupos --detallado

# Ver componentes no utilizados
python manage.py listar_grupos --componentes
```

### Crear Datos de Ejemplo
```bash
# Crear componentes básicos
python manage.py crear_datos_ejemplo

# Configurar grupo de prueba
python manage.py configurar_grupo \
  --grupo "Grupo de Prueba" \
  --componentes "Componente 1:50" "Componente 2:50" \
  --crear-componentes
```

## 📝 Notas Importantes

1. **Cambios en Producción**: Los cambios en grupos afectan a todos los registros que usan esa estructura
2. **Backup**: Siempre hacer backup antes de modificar grupos existentes
3. **Testing**: Probar cambios en desarrollo antes de aplicar en producción
4. **Documentación**: Mantener documentación actualizada de las configuraciones

## 🆘 Solución de Problemas

### Error: "La suma total de incidencias debe ser 100%"
- **Causa**: La suma de incidencias no es exactamente 100%
- **Solución**: Ajustar las incidencias para que sumen 100%

### Error: "Componente no existe"
- **Causa**: Intentando usar un componente que no está creado
- **Solución**: Usar `--crear-componentes` o crear el componente primero

### Error: "IntegrityError: UNIQUE constraint failed"
- **Causa**: Intentando agregar el mismo componente dos veces al grupo
- **Solución**: Verificar que cada componente aparezca solo una vez por grupo
