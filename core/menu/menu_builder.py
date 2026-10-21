from django.urls import reverse


class MenuItem:
    def __init__(self, name='', url=None, icon=None, children=None, permissions=None, module=None, divider=False, section_label=None, report_code=None, elevated_only=False, supermanager_only=False, hide_visita=False, super_or_admin_only=False, hide_administrador=False):
        self.name = name
        self.url = url
        self.icon = icon or 'fa-solid fa-circle'
        self.children = children or []
        self.permissions = permissions or []
        self.module = module
        self.divider = divider
        self.section_label = section_label
        self.report_code = report_code
        self.elevated_only = elevated_only  # Oculta a ITO, Buscador y Visita
        self.supermanager_only = supermanager_only  # Solo superusuario (sin empresa)
        self.hide_visita = hide_visita  # Oculta solo a Visita
        self.super_or_admin_only = super_or_admin_only  # Solo superusuario y ADMINISTRADOR
        self.hide_administrador = hide_administrador  # Oculta al ADMINISTRADOR

    def has_permission(self, user):
        if self.super_or_admin_only and not (user.is_supermanager or user.is_administrador):
            return False
        if self.hide_administrador and getattr(user, 'is_administrador', False):
            return False
        if self.supermanager_only and hasattr(user, 'is_supermanager') and not user.is_supermanager:
            return False
        if self.elevated_only and hasattr(user, 'is_limited') and user.is_limited:
            return False
        if self.hide_visita and hasattr(user, 'is_visita') and user.is_visita:
            return False
        if self.report_code:
            return user.has_report_access(self.report_code)
        if not self.permissions:
            return True
        return any(user.has_perm(perm) for perm in self.permissions)

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
        elif module_code == 'postes':
            return reverse('pole_site:dashboard')
        return None

    @staticmethod
    def get_menu(user, current_url, request):
        if user.is_anonymous:
            return []

        # is_admin = user.is_admin
        # is_supervisor = user.is_supervisor
        # module_code = MenuBuilder.get_active_module(request) or 'supervision'
        # menu = []
        # request.session['active_module'] = module_code

        menu = [
            MenuItem('Dashboard', 'dashboard:dashboard', 'fa-solid fa-tachometer-alt', module='supervision'),
            MenuItem('Sitios', 'sitios:sitios_list', 'fa-solid fa-map-marker-alt', module='supervision', super_or_admin_only=True),
            MenuItem('Empresas', 'contractors:contractors_list', 'fa-solid fa-building', module='supervision', super_or_admin_only=True),
            MenuItem('Usuarios', 'users:list', 'fa-solid fa-users', module='supervision', elevated_only=True, hide_administrador=True),
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
        # elif module_code == 'postes':
        #     menu = [
        #         MenuItem('Dashboard', 'pole_site:dashboard', 'fa-solid fa-tachometer-alt', module='postes'),
        #         MenuItem('Postes', 'pole_site:list', 'fa-solid fa-building-flag', module='postes'),
        #     ]

        # if is_supervisor:
        #     menu += [
        #         MenuItem(
        #             'Configuración',
        #             icon='fa-solid fa-cog',
        #             children=[
        #                 MenuItem(
        #                     'Usuarios',
        #                     # 'users:list',
        #                     'fa-solid fa-users',
        #                     permissions=['core.view_user']
        #                 ),
        #             ]
        #         ),
        #     ]
        # if is_admin:
        #     menu += [
        #         MenuItem(
        #             'Configuración',
        #             icon='fa-solid fa-cog',
        #             permissions=['core.view_company'] if not is_admin else [],
        #             children=[
        #                 MenuItem(
        #                     'Empresas',
        #                     'company:company_list',
        #                     'fa-solid fa-building',
        #                     permissions=['core.view_company']
        #                 ),
        #                 MenuItem(
        #                     'Usuarios',
        #                     # 'users:list',
        #                     'fa-solid fa-users',
        #                     permissions=['core.view_user']
        #                 ),
        #                 MenuItem(
        #                     'Países',
        #                     'country:list',
        #                     'fa-solid fa-globe',
        #                     permissions=['core.view_country']
        #                 ),
        #             ]
        #         ),
        #     ]

        return [item for item in menu if item.has_permission(user)]
