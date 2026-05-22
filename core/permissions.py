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
    'GERENCIA': _COORD_PERMS,
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
    Usar en endpoints que ITO/SEARCHER/COORD/GERENCIA pueden ejecutar."""
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
    """Solo COORD, GERENCIA y supermanager. JSON 403 para AJAX, redirect para páginas."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not (user.is_supermanager or user.is_coord or user.is_gerencia):
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
    """CBV mixin: solo COORD, GERENCIA y supermanager. JSON 403 para AJAX, redirect para páginas."""
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and not (user.is_supermanager or user.is_coord or user.is_gerencia):
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