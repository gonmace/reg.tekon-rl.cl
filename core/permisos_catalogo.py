"""Catálogo de acciones cuyo permiso el superusuario puede configurar desde Usuarios.

Cada acción trae los roles que la tienen por defecto. Lo que se guarda en base
(`PermisoRol` / `PermisoUsuario`) son solo las diferencias con estos valores.
Fijo en código (no configurable): el superusuario puede todo, VISITA nunca escribe,
el alcance de datos (empresa / propios), las acciones solo-superusuario y «concluido = solo lectura».
Para agregar una acción basta una entrada en `ACCIONES`.
"""
from collections import namedtuple

Accion = namedtuple('Accion', 'label grupo roles')

ADMINISTRADOR, ITO, SEARCHER = 'ADMINISTRADOR', 'ITO', 'SEARCHER'

# Roles cuyas casillas se pueden editar (VISITA es siempre solo lectura).
ROLES_CONFIGURABLES = (ADMINISTRADOR, ITO, SEARCHER)

ACCIONES = {
    'cargar_datos': Accion(
        'Cargar datos (visitas, pasos, fotos, mapas, % actual, fecha)', 'Registros',
        frozenset({ADMINISTRADOR, ITO, SEARCHER})),
    'activar_registro': Accion(
        'Activar registros y sitios de obra', 'Registros',
        frozenset({ADMINISTRADOR})),
    'cambiar_responsable': Accion(
        'Cambiar el ITO/Buscador de un registro', 'Registros',
        frozenset({ADMINISTRADOR})),
    'concluir': Accion(
        'Concluir registros', 'Registros',
        frozenset({ADMINISTRADOR, ITO, SEARCHER})),
    'reabrir': Accion(
        'Reabrir registros concluidos', 'Registros',
        frozenset({ADMINISTRADOR})),
    'definir_items_obra': Accion(
        'Definir ítems de obra (plantilla, agregar, borrar)', 'Construcción',
        frozenset({ADMINISTRADOR})),
    'gestionar_usuarios': Accion(
        'Gestionar usuarios (ver, crear, invitar, editar)', 'Administración',
        frozenset({ADMINISTRADOR})),
    'editar_sitios_empresas': Accion(
        'Ver y editar Sitios y Empresas', 'Administración',
        frozenset({ADMINISTRADOR})),
}


def por_defecto(rol, accion):
    return rol in ACCIONES[accion].roles
