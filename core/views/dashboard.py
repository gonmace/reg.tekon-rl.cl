from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from core.utils.breadcrumbs import BreadcrumbsMixin
from dashboard.models import DashboardStats
from datetime import datetime


class DashboardView(LoginRequiredMixin, BreadcrumbsMixin, TemplateView):
    template_name = 'pages/dashboard.html'

    class Meta:
        title = 'Dashboard'
        header_title = 'Dashboard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sitios_stats = DashboardStats.get_sitios_stats()
        registros_stats = DashboardStats.get_registros_stats()
        usuarios_stats = DashboardStats.get_usuarios_stats()

        fecha_actual = datetime.now()
        numero_semana = fecha_actual.isocalendar()[1]

        context.update({
            'sitios_stats': sitios_stats,
            'registros_stats': registros_stats,
            'usuarios_stats': usuarios_stats,
            'fecha_actual': fecha_actual,
            'numero_semana': numero_semana,
        })

        return context