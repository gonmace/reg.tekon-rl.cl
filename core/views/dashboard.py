from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from core.permissions import puede_gestionar_usuarios, tiene_permiso
from core.utils.breadcrumbs import BreadcrumbsMixin
from reg_construccion import dashboard as obra


class DashboardView(LoginRequiredMixin, BreadcrumbsMixin, TemplateView):
    """Inicio: panel de Construcción Sitios (KPIs, estado de obras, mapa, contratistas, actividad)."""
    template_name = 'pages/dashboard.html'

    class Meta:
        title = 'Dashboard'
        header_title = 'Dashboard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        fecha_actual = datetime.now()
        acceso_construccion = user.has_report_access('construccion')

        context.update({
            'acceso_construccion': acceso_construccion,
            'fecha_actual': fecha_actual,
            'numero_semana': fecha_actual.isocalendar()[1],
            'puede_activar': tiene_permiso(user, 'activar_registro'),
            'dias_sin_visita': obra.DIAS_SIN_VISITA,
        })

        if acceso_construccion:
            context.update(obra.panel(user))
            context['actividad_reciente'] = obra.cached(
                'actividad', user, lambda: obra.actividad_reciente(user), ttl=30)
            context['pendientes'] = obra.cached(
                'pendientes', user, lambda: obra.pendientes(user), ttl=30)
        else:
            context.update({
                'acceso_postes': user.has_report_access('txtss_postes'),
                'acceso_ingenieria': user.has_report_access('txtss_torres'),
                've_usuarios': puede_gestionar_usuarios(user),
            })

        return context
