from functools import wraps

from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect

from core.permisos_catalogo import ACCIONES, por_defecto

# Toda decisión de permisos pasa por este módulo (ver ROLES.md): `tiene_permiso` para
# lo configurable por rol/usuario, y el alcance (`alcance_registros`, `can_access_registro`)
# que es fijo según el rol y la empresa.

SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


def _is_ajax(request):
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'api' in request.path
    )


def _rechazar(request, mensaje_json, siempre_json=False):
    """Respuesta de acceso denegado: anónimo → login; JSON 403 en AJAX; redirect en páginas."""
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    if siempre_json or _is_ajax(request):
        return JsonResponse({'success': False, 'message': mensaje_json}, status=403)
    messages.error(request, 'Sin permisos suficientes.')
    return redirect('dashboard:dashboard')


# ── Permisos configurables (por rol y por usuario) ───────────────────────────

def _mapa_roles():
    """{(rol, accion): permitido} con las diferencias guardadas; cacheado e invalidado al guardar."""
    from core.models.permisos import CACHE_KEY_ROLES, PermisoRol
    mapa = cache.get(CACHE_KEY_ROLES)
    if mapa is None:
        mapa = {(r.rol, r.accion): r.permitido for r in PermisoRol.objects.all()}
        cache.set(CACHE_KEY_ROLES, mapa, 300)
    return mapa


def _excepciones_usuario(user):
    """{accion: permitido} de las excepciones del usuario; una consulta por instancia de `user`."""
    excepciones = getattr(user, '_permisos_extra', None)
    if excepciones is None:
        from core.models.permisos import PermisoUsuario
        excepciones = {} if user.pk is None else dict(
            PermisoUsuario.objects.filter(user_id=user.pk).values_list('accion', 'permitido'))
        user._permisos_extra = excepciones
    return excepciones


def tiene_permiso(user, accion):
    """Orden: superusuario sí → VISITA no → excepción del usuario → permiso del rol → valor por defecto."""
    if accion not in ACCIONES:
        raise KeyError(f'Acción desconocida: {accion}')
    if not user or not user.is_authenticated:
        return False
    if user.is_supermanager:
        return True
    if user.is_visita:
        return False
    excepciones = _excepciones_usuario(user)
    if accion in excepciones:
        return excepciones[accion]
    return permiso_de_rol(user.user_type, accion)


def permiso_de_rol(rol, accion):
    """Lo que el rol puede hacer con `accion`: lo configurado o, si no, el valor por defecto."""
    return _mapa_roles().get((rol, accion), por_defecto(rol, accion))


# ── Decoradores y mixins ─────────────────────────────────────────────────────

def not_visita(view_func):
    """Bloquea usuarios VISITA. JSON 403 para AJAX, redirect para páginas."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if getattr(request.user, 'is_visita', False):
            if _is_ajax(request):
                return JsonResponse({'success': False, 'message': 'Acceso de solo lectura'}, status=403)
            messages.error(request, 'Sin permisos para esta acción.')
            return redirect('dashboard:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


def superuser_required(view_func):
    """Solo superusuario (sin empresa). JSON 403 para AJAX, redirect para páginas."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not getattr(request.user, 'is_supermanager', False):
            return _rechazar(request, 'Acción restringida al superusuario')
        return view_func(request, *args, **kwargs)
    return _wrapped


def permiso_required(accion):
    """Decorador: exige `tiene_permiso(user, accion)`. JSON 403 para AJAX, redirect para páginas."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not tiene_permiso(request.user, accion):
                return _rechazar(request, 'Sin permisos para esta acción')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


class NotVisitaMixin:
    """CBV mixin: bloquea VISITA. Siempre devuelve JSON 403 (usar en endpoints AJAX)."""
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_visita:
            return JsonResponse({'success': False, 'message': 'Acceso de solo lectura'}, status=403)
        return super().dispatch(request, *args, **kwargs)


class SuperuserRequiredMixin:
    """CBV mixin: solo superusuario. JSON 403 (usar en endpoints AJAX); un anónimo va al login."""
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_supermanager):
            return _rechazar(request, 'Acción restringida al superusuario', siempre_json=True)
        return super().dispatch(request, *args, **kwargs)


class PermisoRequiredMixin:
    """CBV mixin: exige `tiene_permiso(user, accion)`.

    `solo_escritura=True` deja pasar GET/HEAD/OPTIONS (lectura libre) y exige el permiso en el resto.
    `siempre_json=True` responde JSON 403 también en páginas (endpoints AJAX)."""
    accion = None
    solo_escritura = False
    siempre_json = False

    def dispatch(self, request, *args, **kwargs):
        exigir = not (self.solo_escritura and request.method in SAFE_METHODS)
        if exigir and not tiene_permiso(request.user, self.accion):
            return _rechazar(request, 'Sin permisos para esta acción', siempre_json=self.siempre_json)
        return super().dispatch(request, *args, **kwargs)


class CargaDatosMixin(PermisoRequiredMixin):
    """Endpoints que guardan datos de un registro: POST solo con el permiso `cargar_datos`."""
    accion = 'cargar_datos'
    solo_escritura = True
    siempre_json = True


class ActivarRegistroMixin(PermisoRequiredMixin):
    accion = 'activar_registro'


# ── Sitios, Empresas y Usuarios ──────────────────────────────────────────────

def puede_editar_sitios_empresas(user):
    """Superusuario y ADMINISTRADOR global (sin empresa) con el permiso `editar_sitios_empresas`.
    Crear, importar y eliminar sitios/empresas queda solo para el superusuario."""
    if not (user and user.is_authenticated):
        return False
    return bool(user.is_supermanager or (user.is_admin_global and tiene_permiso(user, 'editar_sitios_empresas')))


class SitiosEmpresasAccessMixin:
    """CBV mixin: ver/editar Sitios y Empresas. JSON 403 en AJAX, redirect en páginas."""
    def dispatch(self, request, *args, **kwargs):
        if not puede_editar_sitios_empresas(request.user):
            return _rechazar(request, 'Acción restringida al superusuario y al administrador global')
        return super().dispatch(request, *args, **kwargs)


def puede_gestionar_usuarios(user):
    return tiene_permiso(user, 'gestionar_usuarios')


class UsuariosAccessMixin:
    """CBV mixin de Usuarios: superusuario y quien tenga el permiso `gestionar_usuarios`."""
    def dispatch(self, request, *args, **kwargs):
        if not puede_gestionar_usuarios(request.user):
            return _rechazar(request, 'Sin acceso a la gestión de usuarios')
        return super().dispatch(request, *args, **kwargs)


def puede_editar_usuario(actor, target):
    """Quién puede modificar/eliminar a `target` desde Usuarios.

    Superusuario: a cualquiera. ADMINISTRADOR global: a cualquiera salvo superusuarios y
    administradores globales. Con empresa (ADMINISTRADOR u otro rol con el permiso):
    solo usuarios de su empresa que no sean ADMINISTRADOR.
    """
    if not actor or not actor.is_authenticated or not tiene_permiso(actor, 'gestionar_usuarios'):
        return False
    if (target.is_superuser or target.is_supermanager) and not actor.is_superuser:
        return False
    if actor.is_supermanager:
        return True
    if actor.is_admin_global:
        return not target.is_admin_global
    return (
        actor.contractor_id is not None
        and target.contractor_id == actor.contractor_id
        and not target.is_administrador
    )


# ── Alcance de registros (fijo según rol y empresa) ──────────────────────────

def _ve_todo(user):
    """Superusuario, ADMINISTRADOR global y VISITA ven los registros de todas las empresas."""
    return user.is_supermanager or user.is_visita or user.is_admin_global


def _codigo_reporte(registro):
    """Código de `User.report_access` del reporte al que pertenece el registro (None si no aplica)."""
    app = registro._meta.app_label
    if app == 'reg_construccion':
        return 'construccion'
    if app == 'reg_txtss':
        tipo = getattr(getattr(registro, 'sitio', None), 'tipo_sitio', None)
        return 'txtss_postes' if tipo == 'POSTE' else 'txtss_torres'
    return None


def _solo_reportes_con_acceso(qs, user):
    """Quita del queryset los reportes a los que `user` no tiene acceso (`User.report_access`)."""
    app = qs.model._meta.app_label
    if app == 'reg_construccion':
        return qs if user.has_report_access('construccion') else qs.none()
    if app == 'reg_txtss':
        if not user.has_report_access('txtss_postes'):
            qs = qs.exclude(sitio__tipo_sitio='POSTE')
        if not user.has_report_access('txtss_torres'):
            qs = qs.exclude(sitio__tipo_sitio='TORRE')
    return qs


def alcance_registros(qs, user):
    """Restringe un queryset de registros (con FK `user`) a lo que `user` puede ver.

    Superusuario, ADMINISTRADOR global y VISITA ven todo; ADMINISTRADOR de empresa, los de su
    empresa; el resto (ITO/Buscador), solo los suyos. Además, solo los reportes a los que el
    usuario tiene acceso (`report_access`). Es la misma regla de los listados.
    """
    if user is None:
        return qs
    qs = _solo_reportes_con_acceso(qs, user)
    if _ve_todo(user):
        return qs
    if user.is_admin_empresa:
        return qs.filter(user__contractor_id=user.contractor_id)
    return qs.filter(user=user)


def can_access_registro(user, registro):
    """Alcance a nivel de objeto; misma regla que `alcance_registros`. Los permisos de
    escritura se controlan aparte (`tiene_permiso`, `puede_escribir_registro`)."""
    if not getattr(user, 'is_authenticated', False):
        return False
    codigo = _codigo_reporte(registro)
    if codigo and not user.has_report_access(codigo):
        return False
    if _ve_todo(user):
        return True
    if user.is_admin_empresa:
        dueno = getattr(registro, 'user', None)
        return dueno is not None and dueno.contractor_id == user.contractor_id
    return getattr(registro, 'user_id', None) == user.id


def registro_access_denied(request, registro):
    """Para endpoints AJAX/API: devuelve un `JsonResponse` 403 si el usuario no
    puede acceder al registro, o `None` si sí puede.

    Uso: `resp = registro_access_denied(request, reg)` ; `if resp: return resp`.
    """
    if can_access_registro(request.user, registro):
        return None
    return JsonResponse({'success': False, 'message': 'Sin permisos para este registro'}, status=403)


def puede_escribir_registro(user, registro):
    """Cargar datos en el registro: permiso `cargar_datos` y alcance sobre él.
    El bloqueo por «concluido» se aplica aparte (`registro_bloqueado_response`)."""
    return tiene_permiso(user, 'cargar_datos') and can_access_registro(user, registro)


# ── Registro concluido ───────────────────────────────────────────────────────
# Un registro concluido es de solo lectura (incluso para el superusuario): para
# corregirlo hay que reabrirlo. Todo endpoint que escriba datos de un registro
# debe llamar a `registro_bloqueado_response`.

MENSAJE_BLOQUEADO = (
    'El registro está concluido y ya no se puede modificar. '
    'Pide a un administrador que lo reabra.'
)
MENSAJE_SOLO_ADMIN_REABRE = 'No tienes permiso para reabrir un registro concluido.'


def registro_bloqueado(registro):
    """True si el registro está concluido (solo lectura)."""
    return bool(getattr(registro, 'concluido', False))


def registro_bloqueado_response(registro):
    """403 JSON si el registro está concluido, o None si se puede modificar.

    Uso: `resp = registro_bloqueado_response(reg)` ; `if resp: return resp`.
    """
    if not registro_bloqueado(registro):
        return None
    return JsonResponse(
        {'success': False, 'locked': True, 'message': MENSAJE_BLOQUEADO}, status=403,
    )


def puede_cambiar_concluido(user, registro):
    """Concluir (permiso `concluir`) o, si ya está concluido, reabrir (permiso `reabrir`), dentro del alcance."""
    if not getattr(user, 'is_authenticated', False):
        return False
    accion = 'reabrir' if registro_bloqueado(registro) else 'concluir'
    return tiene_permiso(user, accion) and can_access_registro(user, registro)
