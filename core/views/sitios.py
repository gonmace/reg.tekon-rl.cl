from django.db.models import Q, Count
from django.views.generic import TemplateView
from django_tables2 import SingleTableView
from rest_framework import viewsets
from core.models.sites import Site
from core.serializers import SiteSerializer
from core.tables import SiteTable
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from core.utils.breadcrumbs import BreadcrumbsMixin
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from core.forms import SiteForm
from django.template.loader import render_to_string
import json


class SitiosView(LoginRequiredMixin, BreadcrumbsMixin, SingleTableView):
    model = Site
    table_class = SiteTable
    template_name = 'pages/sitios.html'
    paginate_by = 20

    def get_queryset(self):
        qs = Site.objects.filter(is_deleted=False)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(pti_cell_id__icontains=q)
                | Q(operator_id__icontains=q)
                | Q(name__icontains=q)
                | Q(region__icontains=q)
                | Q(comuna__icontains=q)
            )
        return qs

    def get_table_kwargs(self):
        return {'user': self.request.user}

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['partials/table_swap.html']
        return [self.template_name]

    def get_breadcrumbs(self):
        return [{'label': 'Sitios'}]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        counts = Site.objects.filter(is_deleted=False).aggregate(
            torres=Count('id', filter=Q(tipo_sitio=Site.TORRE)),
            postes=Count('id', filter=Q(tipo_sitio=Site.POSTE)),
        )
        context['site_counts'] = counts
        return context

class SiteViewSet(viewsets.ModelViewSet):
    serializer_class = SiteSerializer
    
    def get_queryset(self):
        return Site.objects.filter(is_deleted=False)

    def update(self, request, *args, **kwargs):
        """Actualizar sitio, incluyendo soft delete."""
        instance = self.get_object()
        
        # Verificar si solo se está modificando is_deleted
        only_is_deleted = len(request.data) == 1 and 'is_deleted' in request.data
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        if only_is_deleted:
            message = 'Registro eliminado'
        else:
            message = f'Sitio "{instance.name}" actualizado correctamente.'
            
        return Response({'success': True, 'message': message}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Soft delete: marcar is_deleted=True en lugar de eliminar."""
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()
        return Response({'success': True, 'message': f'Sitio "{instance.name}" eliminado correctamente.'}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class SiteEditModalView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_supermanager

    def get(self, request, site_id):
        site = get_object_or_404(Site, id=site_id)
        form = SiteForm(instance=site)
        
        # Renderizar el formulario usando Crispy Forms
        form_html = render_to_string('sites/update_site_form.html', {
            'form': form,
            'site': site
        }, request=request)
        
        return JsonResponse({
            'success': True,
            'form_html': form_html,
            'site_data': {
                'id': site.id,
                'pti_cell_id': site.pti_cell_id or '',
                'operator_id': site.operator_id or '',
                'name': site.name,
                'tipo_sitio': site.tipo_sitio,
                'lat_man': site.lat_man,
                'lon_man': site.lon_man,
                'lat_ing': site.lat_ing,
                'lon_ing': site.lon_ing,
                'lat_con': site.lat_con,
                'lon_con': site.lon_con,
                'alt': site.alt or '',
                'region': site.region or '',
                'comuna': site.comuna or '',
            }
        })

    def post(self, request, site_id):
        try:
            site = get_object_or_404(Site, id=site_id)
            
            # Parsear el JSON del body
            data = json.loads(request.body.decode('utf-8'))
            
            # Convertir valores vacíos a None para campos numéricos
            for k in ('lat', 'lon', 'lat_man', 'lon_man', 'lat_ing', 'lon_ing',
                      'lat_con', 'lon_con'):
                if data.get(k) == '':
                    data[k] = None
            
            # Manejar el campo user correctamente
            if 'user' in data:
                if data['user'] == '' or data['user'] is None:
                    # Si el campo está vacío, establecer como None
                    data['user'] = None
                else:
                    try:
                        # Convertir a entero si es string
                        user_id = int(data['user'])
                        # Verificar que el usuario existe
                        from users.models import User
                        user = User.objects.get(id=user_id)
                        data['user'] = user_id
                        
                    except (ValueError, TypeError, User.DoesNotExist) as e:
                        
                        # Si no se puede convertir o el usuario no existe, eliminar el campo
                        del data['user']
                        
            form = SiteForm(data, instance=site)
            
            if form.is_valid():
                form.save()
                return JsonResponse({
                    'success': True,
                    'message': f'Sitio "{site.name}" actualizado correctamente.'
                })
            else:
                print(f"Form errors: {form.errors}")
                return JsonResponse({
                    'success': False,
                    'message': 'Error en el formulario.',
                    'errors': form.errors
                }, status=400)
                
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'message': 'Error al parsear los datos JSON.',
                'error': str(e)
            }, status=400)
        except Exception as e:
            print(f"Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor.',
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SiteCreateModalView(LoginRequiredMixin, UserPassesTestMixin, View):
    """GET: devuelve form HTML para crear sitio. POST: crea el sitio."""

    def test_func(self):
        return self.request.user.is_supermanager

    def get(self, request):
        form = SiteForm()
        form_html = render_to_string(
            'sites/update_site_form.html',
            {'form': form, 'site': None},
            request=request,
        )
        return JsonResponse({'success': True, 'form_html': form_html})

    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            if data.get('lat') == '':
                data['lat'] = None
            if data.get('lon') == '':
                data['lon'] = None

            form = SiteForm(data)
            if form.is_valid():
                site = form.save()
                return JsonResponse({
                    'success': True,
                    'message': f'Sitio "{site.name}" creado correctamente.',
                    'site_id': site.id,
                })
            return JsonResponse({
                'success': False,
                'message': 'Error en el formulario.',
                'errors': form.errors,
            }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Error al parsear los datos JSON.',
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor.',
                'error': str(e),
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SiteImportView(LoginRequiredMixin, UserPassesTestMixin, View):
    """POST con archivo Excel/CSV: importa sitios usando SiteResource."""

    def test_func(self):
        return self.request.user.is_supermanager

    def post(self, request):
        from core.resources import SiteResource
        from import_export.formats.base_formats import CSV, XLSX

        upload = request.FILES.get('file')
        if not upload:
            return JsonResponse({
                'success': False,
                'message': 'No se recibió ningún archivo.',
            }, status=400)

        ext = upload.name.lower().rsplit('.', 1)[-1]
        if ext == 'xlsx':
            file_format = XLSX()
        elif ext == 'csv':
            file_format = CSV()
        else:
            return JsonResponse({
                'success': False,
                'message': 'Formato no soportado. Usá .xlsx o .csv.',
            }, status=400)

        try:
            data = file_format.create_dataset(upload.read())
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'No se pudo leer el archivo: {e}',
            }, status=400)

        resource = SiteResource()
        result = resource.import_data(data, dry_run=False, raise_errors=False)

        if result.has_errors() or result.has_validation_errors():
            errors = []
            for row_errors in result.row_errors():
                row_num, row_err_list = row_errors
                for err in row_err_list:
                    errors.append(f'Fila {row_num}: {err.error}')
            for inv in result.invalid_rows:
                errors.append(f'Fila {inv.number}: {inv.error_dict}')
            return JsonResponse({
                'success': False,
                'message': 'Errores al importar.',
                'errors': errors[:20],
                'totals': dict(result.totals),
            }, status=400)

        return JsonResponse({
            'success': True,
            'message': f'Importación completa: {result.total_rows} filas procesadas.',
            'totals': dict(result.totals),
        })


class SiteImportTemplateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Descarga un Excel vacío (solo headers) como plantilla de importación."""

    def test_func(self):
        return self.request.user.is_supermanager

    def get(self, request):
        from core.resources import SiteResource
        from django.http import HttpResponse
        resource = SiteResource()
        # dataset.headers viene de los column_name definidos en el resource
        dataset = resource.export(Site.objects.none())
        xlsx_bytes = dataset.export('xlsx')
        response = HttpResponse(
            xlsx_bytes,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename="plantilla_sitios.xlsx"'
        return response