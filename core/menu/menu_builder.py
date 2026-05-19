from django.urls import reverse


class MenuItem:
    def __init__(self, name='', url=None, icon=None, children=None, permissions=None, module=None, divider=False, section_label=None, report_code=None, elevated_only=False):
        self.name = name
        self.url = url
        self.icon = icon or 'fas fa-circle'
        self.children = children or []
        self.permissions = permissions or []
        self.module = module
        self.divider = divider
        self.section_label = section_label
        self.report_code = report_code
        self.elevated_only = elevated_only  # Si True, se oculta a ITO, Buscador y Visita

    def has_permission(self, user):
        if self.elevated_only and hasattr(user, 'is_limited') and user.is_limited:
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
            MenuItem('Dashboard', 'dashboard:dashboard', 'fas fa-tachometer-alt', module='supervision'),
            MenuItem('Sitios', 'sitios:sitios_list', 'fas fa-map-marker-alt', module='supervision', elevated_only=True),
            MenuItem('Empresas', 'contractors:contractors_list', 'fas fa-building', module='supervision', elevated_only=True),
            MenuItem('Usuarios', 'users:list', 'fas fa-users', module='supervision', elevated_only=True),
            MenuItem(divider=True, section_label='Reportes'),
            MenuItem('TX/TSS Postes', 'reg_txtss:list_postes', 'fas fa-wifi', module='registros', report_code='txtss_postes'),
            MenuItem('TX/TSS Torres', 'reg_txtss:list_torres', 'fa-solid fa-broadcast-tower', module='registros', report_code='txtss_torres'),
            MenuItem(divider=True, section_label='Configuración', elevated_only=True),
            MenuItem('Pasos', 'actividades:paso_list', 'fas fa-list-check', module='configuracion', elevated_only=True),
            MenuItem('Widgets', 'widgets:catalog', 'fa-solid fa-puzzle-piece', module='configuracion', elevated_only=True),
        ]
        # elif module_code == 'postes':
        #     menu = [
        #         MenuItem('Dashboard', 'pole_site:dashboard', 'fas fa-tachometer-alt', module='postes'),
        #         MenuItem('Postes', 'pole_site:list', 'fa-solid fa-building-flag', module='postes'),
        #     ]

        # if is_supervisor:
        #     menu += [
        #         MenuItem(
        #             'Configuración',
        #             icon='fas fa-cog',
        #             children=[
        #                 MenuItem(
        #                     'Usuarios',
        #                     # 'users:list',
        #                     'fas fa-users',
        #                     permissions=['core.view_user']
        #                 ),
        #             ]
        #         ),
        #     ]
        # if is_admin:
        #     menu += [
        #         MenuItem(
        #             'Configuración',
        #             icon='fas fa-cog',
        #             permissions=['core.view_company'] if not is_admin else [],
        #             children=[
        #                 MenuItem(
        #                     'Empresas',
        #                     'company:company_list',
        #                     'fas fa-building',
        #                     permissions=['core.view_company']
        #                 ),
        #                 MenuItem(
        #                     'Usuarios',
        #                     # 'users:list',
        #                     'fas fa-users',
        #                     permissions=['core.view_user']
        #                 ),
        #                 MenuItem(
        #                     'Países',
        #                     'country:list',
        #                     'fas fa-globe',
        #                     permissions=['core.view_country']
        #                 ),
        #             ]
        #         ),
        #     ]

        return [item for item in menu if item.has_permission(user)]
