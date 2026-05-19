from django.db import models
from django.utils import timezone
from datetime import timedelta
from core.models.sites import Site
from reg_txtss.models import RegTxtss
from users.models import User


class DashboardMetric(models.Model):
    METRIC_TYPES = [
        ('sitios_totales', 'Sitios Totales'),
        ('registros_txtss', 'Registros TXTSS'),
        ('usuarios_activos', 'Usuarios Activos'),
    ]

    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES, unique=True)
    value = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Métrica del Dashboard'
        verbose_name_plural = 'Métricas del Dashboard'

    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.value}"


class SitioDashboard(models.Model):
    sitio = models.OneToOneField(Site, on_delete=models.CASCADE, related_name='dashboard_info')
    total_registros_txtss = models.IntegerField(default=0)
    ultimo_registro_txtss = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Información de Sitio para Dashboard'
        verbose_name_plural = 'Información de Sitios para Dashboard'

    def __str__(self):
        return f"Dashboard - {self.sitio.name}"

    def update_metrics(self):
        self.total_registros_txtss = RegTxtss.objects.filter(
            sitio=self.sitio,
            is_deleted=False,
        ).count()

        ultimo_txtss = RegTxtss.objects.filter(
            sitio=self.sitio,
            is_deleted=False,
        ).order_by('-created_at').first()
        if ultimo_txtss:
            self.ultimo_registro_txtss = ultimo_txtss.created_at

        self.save()


class DashboardStats:
    @staticmethod
    def get_sitios_stats():
        total_sitios = Site.objects.filter(is_deleted=False).count()
        sitios_con_txtss = RegTxtss.objects.filter(
            is_deleted=False
        ).values('sitio').distinct().count()

        return {
            'total_sitios': total_sitios,
            'sitios_con_registros': sitios_con_txtss,
        }

    @staticmethod
    def get_registros_stats():
        total_txtss = RegTxtss.objects.filter(is_deleted=False).count()
        ultimo_mes = timezone.now() - timedelta(days=30)
        txtss_ultimo_mes = RegTxtss.objects.filter(
            created_at__gte=ultimo_mes,
            is_deleted=False,
        ).count()

        return {
            'total_txtss': total_txtss,
            'txtss_ultimo_mes': txtss_ultimo_mes,
        }

    @staticmethod
    def get_usuarios_stats():
        total_usuarios = User.objects.filter(is_active=True, is_deleted=False).count()
        ultimo_mes = timezone.now() - timedelta(days=30)
        usuarios_activos = User.objects.filter(
            is_active=True,
            is_deleted=False,
            last_login__gte=ultimo_mes,
        ).count()

        return {
            'total_usuarios': total_usuarios,
            'usuarios_activos': usuarios_activos,
        }

    @staticmethod
    def get_sitios_detallados():
        sitios = Site.objects.filter(is_deleted=False).prefetch_related('reg_txtss')
        sitios_data = []
        for sitio in sitios:
            ultimo_txtss = sitio.reg_txtss.filter(is_deleted=False).order_by('-created_at').first()
            total_txtss = sitio.reg_txtss.filter(is_deleted=False).count()
            sitios_data.append({
                'sitio': sitio,
                'ultimo_registro_txtss': ultimo_txtss.created_at if ultimo_txtss else None,
                'total_txtss': total_txtss,
            })
        return sitios_data
