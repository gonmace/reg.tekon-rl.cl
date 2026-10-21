from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy

# Definición de permisos por rol
_COORD_PERMS = [
    'core.view_company',
    'core.add_company',
    'core.change_company',
    'core.delete_company',
    'core.view_user',
    'core.add_user',
    'core.change_user',
    'core.delete_user',
    'core.view_country',
    'core.add_country',
    'core.change_country',
    'core.delete_country',
    'visits.can_approve_visits',
    'visits.can_schedule_visits',
]
_ITO_PERMS = [
    'core.view_company',
    'core.view_user',
    'visits.can_approve_visits',
    'visits.can_schedule_visits',
]

ROLE_PERMISSIONS = {
    'ADMINISTRADOR': _COORD_PERMS,
    'COORD': _COORD_PERMS,
    'ITO': _ITO_PERMS,
    'SEARCHER': _ITO_PERMS,
    'VISITA': [
        'visits.can_schedule_visits',
    ],
}

def role_required(allowed_roles):
    """
    Decorador para verificar si el usuario tiene uno de los roles permitidos.
    Uso: @role_required(['COORD', 'ENCARGADO'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Debe iniciar sesión para acceder a esta página.")
                return redirect('users:login')
            
            if request.user.user_type not in allowed_roles:
                messages.error(request, "No tiene permisos para acceder a esta página.")
                return redirect('dashboard:dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def permission_required(permission):
    """
    Decorador para verificar si el usuario tiene un permiso específico.
    Uso: @permission_required('core.view_company')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Debe iniciar sesión para acceder a esta página.")
                return redirect('users:login')
            
            if not request.user.has_perm(permission):
                messages.error(request, "No tiene permisos para acceder a esta página.")
                return redirect('dashboard:dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

class RoleRequiredMixin:
    """
    Mixin para vistas basadas en clases que requieren roles específicos.
    Uso: class MyView(RoleRequiredMixin, View):
         allowed_roles = ['COORD', 'ENCARGADO']
    """
    allowed_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debe iniciar sesión para acceder a esta página.")
            return redirect('users:login')
        
        if request.user.user_type not in self.allowed_roles:
            messages.error(request, "No tiene permisos para acceder a esta página.")
            return redirect('dashboard:dashboard')
        
        return super().dispatch(request, *args, **kwargs)

class PermissionRequiredMixin:
    """
    Mixin para vistas basadas en clases que requieren permisos específicos.
    Uso: class MyView(PermissionRequiredMixin, View):
         required_permission = 'core.view_company'
    """
    required_permission = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debe iniciar sesión para acceder a esta página.")
            return redirect('users:login')

        if self.required_permission and not request.user.has_perm(self.required_permission):
            messages.error(request, "No tiene permisos para acceder a esta página.")
            return redirect('dashboard:dashboard')

        return super().dispatch(request, *args, **kwargs)


# ── Criterios unificados por nivel de usuario (ver ROLES.md) ──────────────────

def _is_ajax(request):
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'api' in request.path
    )


def not_visita(view_func):
    """Bloquea usuarios VISITA. JSON 403 para AJAX, redirect para páginas.
    Usar en endpoints que ITO/SEARCHER/COORD/ADMINISTRADOR pueden ejecutar."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_visita:
            if _is_ajax(request):
                return JsonResponse({'success': False, 'message': 'Acceso de solo lectura'}, status=403)
            messages.error(request, 'Sin permisos para esta acción.')
            return redirect('dashboard:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


def superuser_required(view_func):
    """Solo superusuario (sin empresa). JSON 403 para AJAX, redirect para páginas.
    Usar en endpoints de administración o acciones destructivas."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_supermanager:
            if _is_ajax(request):
                return JsonResponse({'success': False, 'message': 'Acción restringida al superusuario'}, status=403)
            messages.error(request, 'Sin permisos suficientes.')
            return redirect('dashboard:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


def es_super_o_admin(user):
    """Superusuario (sin empresa) o ADMINISTRADOR: los únicos que gestionan Sitios y Empresas."""
    return bool(user and user.is_authenticated and (user.is_supermanager or user.is_administrador))


class SuperOrAdminRequiredMixin:
    """CBV mixin: solo superusuario y ADMINISTRADOR. JSON 403 en endpoints AJAX, redirect en páginas.
    Un anónimo también se rechaza (lo manda a iniciar sesión)."""
    def dispatch(self, request, *args, **kwargs):
        if not es_super_o_admin(request.user):
            if _is_ajax(request):
                return JsonResponse({'success': False, 'message': 'Acción restringida al superusuario y al administrador'}, status=403)
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            messages.error(request, 'Sin permisos suficientes.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)


def puede_gestionar_usuarios(user):
    """Superusuario y COORD gestionan usuarios; el ADMINISTRADOR no tiene acceso a Usuarios."""
    return bool(user and user.is_authenticated and (user.is_supermanager or user.is_coord))


class UsuariosAccessMixin:
    """CBV mixin de Usuarios: solo superusuario y COORD. JSON 403 en AJAX, redirect en páginas."""
    def dispatch(self, request, *args, **kwargs):
        if not puede_gestionar_usuarios(request.user):
            if _is_ajax(request):
                return JsonResponse({'success': False, 'message': 'Sin acceso a la gestión de usuarios'}, status=403)
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            messages.error(request, 'Sin permisos suficientes.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)


class NotVisitaMixin:
    """CBV mixin: bloquea VISITA. Siempre devuelve JSON 403 (usar en endpoints AJAX)."""
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_visita:
            return JsonResponse({'success': False, 'message': 'Acceso de solo lectura'}, status=403)
        return super().dispatch(request, *args, **kwargs)


class SuperuserRequiredMixin:
    """CBV mixin: solo superusuario. Siempre devuelve JSON 403 (usar en endpoints AJAX)."""
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_supermanager:
            return JsonResponse({'success': False, 'message': 'Acción restringida al superusuario'}, status=403)
        return super().dispatch(request, *args, **kwargs)


def coord_or_above_required(view_func):
    """Solo COORD, ADMINISTRADOR y supermanager. JSON 403 para AJAX, redirect para páginas."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not (user.is_supermanager or user.is_coord or user.is_administrador):
            if _is_ajax(request):
                return JsonResponse({'success': False, 'message': 'Sin permisos para esta acción'}, status=403)
            messages.error(request, 'Sin permisos para esta acción.')
            return redirect('dashboard:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


class ItoLikeMixin:
    """POST solo para ITO, SEARCHER y supermanager. GET libre para todos."""
    def dispatch(self, request, *args, **kwargs):
        if (request.user.is_authenticated
                and request.method not in ('GET', 'HEAD', 'OPTIONS')
                and not (request.user.is_supermanager or request.user.is_ito_like)):
            return JsonResponse({'success': False, 'message': 'Sin permisos para esta acción'}, status=403)
        return super().dispatch(request, *args, **kwargs)


class CoordOrAboveMixin:
    """CBV mixin: solo COORD, ADMINISTRADOR y supermanager. JSON 403 para AJAX, redirect para páginas."""
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and not (user.is_supermanager or user.is_coord or user.is_administrador):
            if _is_ajax(request):
                return JsonResponse({'success': False, 'message': 'Sin permisos para esta acción'}, status=403)
            messages.error(request, 'Sin permisos para esta acción.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)


class OwnedByUserMixin:
    """Filtra el queryset al usuario actual. Superuser y VISITA ven todos los registros.

    Usar en ListViews/TableViews que necesiten acotar los datos por propietario.
    Requiere que el modelo tenga un campo `user` FK al usuario.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_supermanager or user.is_visita:
            return qs
        return qs.filter(user=self.request.user)


def can_access_registro(user, registro):
    """Ownership a nivel de objeto para registros con FK `user`.

    Supermanager, ADMINISTRADOR y VISITA acceden a todos los registros (consistente
    con `OwnedByUserMixin`); el resto solo a los registros propios. Los permisos de
    escritura (rol, no-visita) se controlan aparte con los mixins/decoradores.
    """
    if not getattr(user, 'is_authenticated', False):
        return False
    if user.is_supermanager or user.is_visita or user.is_administrador:
        return True
    return getattr(registro, 'user_id', None) == user.id


def registro_access_denied(request, registro):
    """Para endpoints AJAX/API: devuelve un `JsonResponse` 403 si el usuario no
    puede acceder al registro, o `None` si sí puede.

    Uso: `resp = registro_access_denied(request, reg)` ; `if resp: return resp`.
    """
    if can_access_registro(request.user, registro):
        return None
    return JsonResponse({'success': False, 'message': 'Sin permisos para este registro'}, status=403)


def alcance_registros(qs, user):
    """Restringe un queryset de registros (con FK `user`) a lo que `user` puede ver.

    Supermanager, ADMINISTRADOR y VISITA ven todo; COORD, los de su contratista; el
    resto (ITO/Buscador), solo los suyos. Es la misma regla de los listados.
    """
    if user is None or user.is_supermanager or user.is_visita or user.is_administrador:
        return qs
    if user.is_coord and user.contractor_id:
        return qs.filter(user__contractor_id=user.contractor_id)
    return qs.filter(user=user)


# ── Registro concluido ───────────────────────────────────────────────────────
# Un registro concluido es de solo lectura (incluso para el superusuario): para
# corregirlo hay que reabrirlo. Todo endpoint que escriba datos de un registro
# debe llamar a `registro_bloqueado_response`.

MENSAJE_BLOQUEADO = (
    'El registro está concluido y ya no se puede modificar. '
    'Pide a un administrador que lo reabra.'
)
MENSAJE_SOLO_ADMIN_REABRE = 'Solo un administrador o el superusuario puede reabrir un registro concluido.'


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
    """Concluir: supermanager o ITO/Buscador. Reabrir: solo supermanager o ADMINISTRADOR."""
    if not getattr(user, 'is_authenticated', False):
        return False
    if registro_bloqueado(registro):
        return bool(user.is_supermanager or user.is_administrador)
    return bool(user.is_supermanager or user.is_ito_like)


class RegistroOwnerMixin:
    """CBV mixin: exige ownership sobre `self.registro` en cada request.

    La vista debe exponer el registro vía `get_registro_for_permission()`
    (o tener el atributo `self.registro` ya poblado). Lanza `PermissionDenied`
    (HTTP 403) si el usuario no es dueño. Combinar con `LoginRequiredMixin`.
    """
    def get_registro_for_permission(self):
        return getattr(self, 'registro', None)

    def dispatch(self, request, *args, **kwargs):
        registro = self.get_registro_for_permission()
        if registro is not None and not can_access_registro(request.user, registro):
            raise PermissionDenied('No tienes acceso a este registro.')
        return super().dispatch(request, *args, **kwargs)