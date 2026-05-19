from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import DashboardStats
from core.models.sites import Site
from reg_txtss.models import RegTxtss
from users.models import User


@login_required
def dashboard_sitios(request):
    sitios = Site.objects.filter(is_deleted=False).prefetch_related('reg_txtss')

    region_filter = request.GET.get('region', '')
    search_query = request.GET.get('search', '')

    if region_filter:
        sitios = sitios.filter(region=region_filter)

    if search_query:
        sitios = sitios.filter(
            Q(name__icontains=search_query) |
            Q(pti_cell_id__icontains=search_query) |
            Q(operator_id__icontains=search_query) |
            Q(comuna__icontains=search_query)
        )

    sitios_data = []
    for sitio in sitios:
        ultimo_txtss = sitio.reg_txtss.filter(is_deleted=False).order_by('-created_at').first()
        total_txtss = sitio.reg_txtss.filter(is_deleted=False).count()
        sitios_data.append({
            'sitio': sitio,
            'ultimo_registro_txtss': ultimo_txtss,
            'total_txtss': total_txtss,
        })

    paginator = Paginator(sitios_data, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    regiones = Site.objects.filter(
        is_deleted=False
    ).values_list('region', flat=True).distinct().exclude(region__isnull=True)

    context = {
        'page_obj': page_obj,
        'region_filter': region_filter,
        'search_query': search_query,
        'regiones': regiones,
    }

    return render(request, 'dashboard/dashboard_sitios.html', context)


@login_required
def dashboard_txtss(request):
    registros = RegTxtss.objects.filter(
        is_deleted=False
    ).select_related('sitio', 'user')

    sitio_filter = request.GET.get('sitio', '')
    user_filter = request.GET.get('user', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    if sitio_filter:
        registros = registros.filter(sitio__name__icontains=sitio_filter)
    if user_filter:
        registros = registros.filter(user__username__icontains=user_filter)
    if fecha_desde:
        registros = registros.filter(created_at__date__gte=fecha_desde)
    if fecha_hasta:
        registros = registros.filter(created_at__date__lte=fecha_hasta)

    paginator = Paginator(registros, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'sitio_filter': sitio_filter,
        'user_filter': user_filter,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }

    return render(request, 'dashboard/dashboard_txtss.html', context)


@login_required
def api_dashboard_stats(request):
    try:
        sitios_stats = DashboardStats.get_sitios_stats()
        registros_stats = DashboardStats.get_registros_stats()
        usuarios_stats = DashboardStats.get_usuarios_stats()

        meses_stats = []
        for i in range(6):
            fecha = timezone.now() - timedelta(days=30 * i)
            mes = fecha.strftime('%Y-%m')
            txtss_count = RegTxtss.objects.filter(
                created_at__year=fecha.year,
                created_at__month=fecha.month,
                is_deleted=False,
            ).count()
            meses_stats.append({'mes': mes, 'txtss': txtss_count})

        return JsonResponse({
            'success': True,
            'sitios': sitios_stats,
            'registros': registros_stats,
            'usuarios': usuarios_stats,
            'meses': meses_stats,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def api_sitio_detail(request, sitio_id):
    try:
        sitio = Site.objects.get(id=sitio_id, is_deleted=False)

        ultimo_txtss = RegTxtss.objects.filter(
            sitio=sitio, is_deleted=False
        ).order_by('-created_at').first()

        total_txtss = RegTxtss.objects.filter(sitio=sitio, is_deleted=False).count()

        return JsonResponse({
            'success': True,
            'sitio': {
                'id': sitio.id,
                'name': sitio.name,
                'pti_cell_id': sitio.pti_cell_id,
                'operator_id': sitio.operator_id,
                'region': sitio.region,
                'comuna': sitio.comuna,
                'lat_base': sitio.lat_base,
                'lon_base': sitio.lon_base,
            },
            'ultimo_txtss': {
                'id': ultimo_txtss.id,
                'created_at': ultimo_txtss.created_at.isoformat(),
                'user': ultimo_txtss.user.username,
            } if ultimo_txtss else None,
            'stats': {'total_txtss': total_txtss},
        })

    except Site.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sitio no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
