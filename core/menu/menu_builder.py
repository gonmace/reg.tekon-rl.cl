from django.urls import reverse

from core.permissions import puede_editar_sitios_empresas, puede_gestionar_usuarios


class MenuItem:
    def __init__(self, name='', url=None, icon=None, children=None, module=None, divider=False, section_label=None, report_code=None, supermanager_only=False, check=None):
        self.name = name
        self.url = url
        self.icon = icon or 'fa-solid fa-circle'
        self.children = children or []
        self.module = module
        self.divider = divider
        self.section_label = section_label
        self.report_code = report_code
        self.supermanager_only = supermanager_only  # Solo superusuario (sin empresa)
        self.check = check  # callable(user) -> bool, de core.permissions

    def has_permission(self, user):
        if self.supermanager_only and not user.is_supermanager:
            return False
        if self.check and not self.check(user):
            return False
        if self.report_code:
            return user.has_report_access(self.report_code)
        return True

    def get_url(self):
        return reverse(self.url) if self.url else '#'

    @property
    def is_active(self):
        return self.url

    def __str__(self):
        return self.name


class MenuBuilder:
    @staticmethod
    def get_active_module(request):
        return request.session.get('active_module', None)

    @staticmethod
    def set_active_module(request, module_code):
        request.session['active_module'] = module_code
        # Cuando se cambia el módulo, redirigir al dashboard correcto
        if module_code == 'torres':
            return reverse('dashboard:dashboard')
        return None

    @staticmethod
    def get_menu(user, current_url, request):
        if user.is_anonymous:
            return []

        menu = [
            MenuItem('Dashboard', 'dashboard:dashboard', 'fa-solid fa-tachometer-alt', module='supervision'),
            MenuItem('Sitios', 'sitios:sitios_list', 'fa-solid fa-map-marker-alt', module='supervision', check=puede_editar_sitios_empresas),
            MenuItem('Empresas', 'contractors:contractors_list', 'fa-solid fa-building', module='supervision', check=puede_editar_sitios_empresas),
            MenuItem('Usuarios', 'users:list', 'fa-solid fa-users', module='supervision', check=puede_gestionar_usuarios),
            MenuItem('Imágenes', 'photos:gallery', 'fa-solid fa-images', module='supervision'),
            MenuItem(divider=True, section_label='Reportes'),
            MenuItem('TX/TSS Postes', 'reg_txtss:list_postes', 'fa-solid fa-wifi', module='registros', report_code='txtss_postes'),
            MenuItem('TX/TSS Ingenieria', 'reg_txtss:list_torres', 'fa-solid fa-broadcast-tower', module='registros', report_code='txtss_torres'),
            MenuItem('Construcción Sitios', 'reg_construccion:list', 'fa-solid fa-helmet-safety', module='registros', report_code='construccion'),
            MenuItem(divider=True, section_label='Configuración', supermanager_only=True),
            MenuItem('Pasos', 'actividades:paso_list', 'fa-solid fa-list-check', module='configuracion', supermanager_only=True),
            MenuItem('Widgets', 'widgets:catalog', 'fa-solid fa-puzzle-piece', module='configuracion', supermanager_only=True),
            MenuItem('Correo', 'correo:config', 'fa-solid fa-envelope', module='configuracion', supermanager_only=True),
        ]
        return [item for item in menu if item.has_permission(user)]
