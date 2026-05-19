from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib import messages
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