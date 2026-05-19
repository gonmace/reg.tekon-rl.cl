from django.core.management.base import BaseCommand
from django.db import transaction
from dashboard.models import DashboardMetric, SitioDashboard
from core.models.sites import Site
from reg_txtss.models import RegTxtss
from users.models import User
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Pobla las métricas del dashboard con datos actuales'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Forzar la actualización de todas las métricas')

    def handle(self, *args, **options):
        self.stdout.write('Iniciando población de métricas del dashboard...')

        with transaction.atomic():
            self.update_general_metrics()
            self.update_site_metrics()

        self.stdout.write(self.style.SUCCESS('Métricas del dashboard actualizadas exitosamente'))

    def update_general_metrics(self):
        self.stdout.write('Actualizando métricas generales...')

        total_sitios = Site.objects.filter(is_deleted=False).count()
        self.update_metric('sitios_totales', total_sitios)

        total_txtss = RegTxtss.objects.filter(is_deleted=False).count()
        self.update_metric('registros_txtss', total_txtss)

        ultimo_mes = timezone.now() - timedelta(days=30)
        usuarios_activos = User.objects.filter(
            is_active=True,
            is_deleted=False,
            last_login__gte=ultimo_mes,
        ).count()
        self.update_metric('usuarios_activos', usuarios_activos)

    def update_site_metrics(self):
        self.stdout.write('Actualizando métricas de sitios...')

        sitios = Site.objects.filter(is_deleted=False)
        updated_count = 0

        for sitio in sitios:
            sitio_dashboard, _ = SitioDashboard.objects.get_or_create(sitio=sitio)
            sitio_dashboard.update_metrics()
            updated_count += 1
            if updated_count % 10 == 0:
                self.stdout.write(f'Procesados {updated_count} sitios...')

        self.stdout.write(f'Procesados {updated_count} sitios en total')

    def update_metric(self, metric_type, value):
        metric, created = DashboardMetric.objects.get_or_create(
            metric_type=metric_type,
            defaults={'value': value},
        )
        if not created:
            metric.value = value
            metric.save()
        self.stdout.write(f'  - {metric_type}: {value}')
