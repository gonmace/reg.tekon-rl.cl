from django.db import models
from django.db.models import Q, Count, Prefetch, Max
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
        total_postes = Site.objects.filter(is_deleted=False, tipo_sitio='POSTE').count()
        total_torres = Site.objects.filter(is_deleted=False, tipo_sitio='TORRE').count()
        sitios_con_txtss = RegTxtss.objects.filter(
            is_deleted=False
        ).values('sitio').distinct().count()
        sitios_sin_registros = total_sitios - sitios_con_txtss

        return {
            'total_sitios': total_sitios,
            'total_postes': total_postes,
            'total_torres': total_torres,
            'sitios_con_registros': sitios_con_txtss,
            'sitios_sin_registros': sitios_sin_registros,
        }

    @staticmethod
    def _get_estado_counts(tipo_sitio):
        agg = (
            RegTxtss.objects
            .filter(is_deleted=False, sitio__tipo_sitio=tipo_sitio)
            .with_estado()
            .aggregate(
                total=Count('id'),
                completados=Count('id', filter=Q(concluido=True)),
                en_proceso=Count('id', filter=Q(concluido=False, has_widgets=True)),
                pendientes=Count('id', filter=Q(concluido=False, has_widgets=False)),
            )
        )
        return agg

    @staticmethod
    def get_registros_stats():
        ultimo_mes = timezone.now() - timedelta(days=30)
        hoy = timezone.now().date()
        txtss_ultimo_mes = RegTxtss.objects.filter(
            created_at__gte=ultimo_mes,
            is_deleted=False,
        ).count()
        txtss_hoy = RegTxtss.objects.filter(
            created_at__date=hoy,
            is_deleted=False,
        ).count()

        postes = DashboardStats._get_estado_counts('POSTE')
        torres = DashboardStats._get_estado_counts('TORRE')

        return {
            'total_txtss': (postes['total'] or 0) + (torres['total'] or 0),
            'txtss_ultimo_mes': txtss_ultimo_mes,
            'txtss_hoy': txtss_hoy,
            'total_postes': postes['total'] or 0,
            'postes_completados': postes['completados'] or 0,
            'postes_en_proceso': postes['en_proceso'] or 0,
            'postes_pendientes': postes['pendientes'] or 0,
            'total_torres': torres['total'] or 0,
            'torres_completados': torres['completados'] or 0,
            'torres_en_proceso': torres['en_proceso'] or 0,
            'torres_pendientes': torres['pendientes'] or 0,
        }

    @staticmethod
    def get_usuarios_stats():
        total_usuarios = User.objects.filter(is_active=True, is_deleted=False).count()
        ultimo_mes = timezone.now() - timedelta(days=30)
        ultima_semana = timezone.now() - timedelta(days=7)
        usuarios_activos = User.objects.filter(
            is_active=True,
            is_deleted=False,
            last_login__gte=ultimo_mes,
        ).count()
        usuarios_semana = User.objects.filter(
            is_active=True,
            is_deleted=False,
            last_login__gte=ultima_semana,
        ).count()

        return {
            'total_usuarios': total_usuarios,
            'usuarios_activos': usuarios_activos,
            'usuarios_semana': usuarios_semana,
        }

    @staticmethod
    def get_sitios_detallados():
        # Prefetch filtrado + Count anotado: evita el N+1 previo (2 queries por
        # sitio) que se producía al re-filtrar `sitio.reg_txtss` dentro del loop.
        sitios = (
            Site.objects.filter(is_deleted=False)
            .prefetch_related(Prefetch(
                'reg_txtss',
                queryset=RegTxtss.objects.filter(is_deleted=False).order_by('-created_at'),
                to_attr='registros_activos',
            ))
            .annotate(total_txtss=Count('reg_txtss', filter=Q(reg_txtss__is_deleted=False)))
        )
        sitios_data = []
        for sitio in sitios:
            activos = sitio.registros_activos
            ultimo_txtss = activos[0] if activos else None
            sitios_data.append({
                'sitio': sitio,
                'ultimo_registro_txtss': ultimo_txtss.created_at if ultimo_txtss else None,
                'total_txtss': sitio.total_txtss,
            })
        return sitios_data
