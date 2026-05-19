"""
Vistas para contratistas.
"""

import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.forms import modelform_factory
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django_tables2 import SingleTableView
from core.models.contractors import Contractor
from core.tables import ContractorTable
from core.utils.breadcrumbs import BreadcrumbsMixin


class ContractorsView(LoginRequiredMixin, BreadcrumbsMixin, SingleTableView):
    model = Contractor
    table_class = ContractorTable
    template_name = 'pages/contractors.html'
    paginate_by = 20

    def get_queryset(self):
        qs = Contractor.objects.filter(is_deleted=False)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q))
        return qs

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['partials/contractors_table_swap.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        counts = Contractor.objects.filter(is_deleted=False).aggregate(
            activos=Count('id', filter=Q(is_active=True)),
            inactivos=Count('id', filter=Q(is_active=False)),
        )
        context['contractor_counts'] = counts
        return context

    def get_breadcrumbs(self):
        return [{'label': 'Contratistas'}]


class ContractorViewSet(View):
    """ViewSet para operaciones CRUD de contratistas."""
    
    def get(self, request):
        """Obtener lista de contratistas."""
        contractors = Contractor.objects.filter(is_active=True).order_by('name')
        data = []
        
        for contractor in contractors:
            data.append({
                'id': contractor.id,
                'name': contractor.name,
                'code': contractor.code,
                'is_active': contractor.is_active,
                'created_at': contractor.created_at.strftime('%d/%m/%Y %H:%M'),
                'updated_at': contractor.updated_at.strftime('%d/%m/%Y %H:%M'),
            })
        
        return JsonResponse(data, safe=False)

    def post(self, request):
        """Crear nuevo contratista."""
        try:
            data = json.loads(request.body.decode('utf-8'))

            # Crear el formulario dinámicamente
            ContractorForm = modelform_factory(Contractor, fields=['name', 'code'])
            form = ContractorForm(data)
            
            if form.is_valid():
                contractor = form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Contratista creado correctamente',
                    'contractor': {
                        'id': contractor.id,
                        'name': contractor.name,
                        'code': contractor.code,
                        'is_active': contractor.is_active,
                        'created_at': contractor.created_at.strftime('%d/%m/%Y %H:%M'),
                        'updated_at': contractor.updated_at.strftime('%d/%m/%Y %H:%M'),
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Error en los datos del formulario',
                    'errors': form.errors
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al crear contratista: {str(e)}'
            }, status=500)

    def put(self, request, contractor_id):
        """Actualizar contratista existente."""
        try:
            contractor = Contractor.objects.get(id=contractor_id)
            data = json.loads(request.body.decode('utf-8'))

            # Crear el formulario dinámicamente
            ContractorForm = modelform_factory(Contractor, fields=['name', 'code'])
            form = ContractorForm(data, instance=contractor)
            
            if form.is_valid():
                contractor = form.save(commit=False)
                if 'is_active' in data:
                    contractor.is_active = bool(data['is_active'])
                contractor.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Contratista actualizado correctamente',
                    'contractor': {
                        'id': contractor.id,
                        'name': contractor.name,
                        'code': contractor.code,
                        'is_active': contractor.is_active,
                        'created_at': contractor.created_at.strftime('%d/%m/%Y %H:%M'),
                        'updated_at': contractor.updated_at.strftime('%d/%m/%Y %H:%M'),
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Error en los datos del formulario',
                    'errors': form.errors
                }, status=400)
                
        except Contractor.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Contratista no encontrado'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar contratista: {str(e)}'
            }, status=500)

    def delete(self, request, contractor_id):
        """Soft-delete de contratista."""
        try:
            contractor = Contractor.objects.get(id=contractor_id, is_deleted=False)
            contractor.is_deleted = True
            contractor.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Contratista eliminado correctamente'
            })
                
        except Contractor.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Contratista no encontrado'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al eliminar contratista: {str(e)}'
            }, status=500)


class ContractorEditModalView(View):
    """Vista para mostrar/editar contratista en modal."""
    
    def get(self, request, contractor_id=None):
        """Mostrar formulario de contratista."""
        if contractor_id:
            try:
                contractor = Contractor.objects.get(id=contractor_id)
                action = 'edit'
            except Contractor.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Contratista no encontrado'
                }, status=404)
        else:
            contractor = None
            action = 'create'
        
        # Crear el formulario dinámicamente
        fields = ['name', 'code', 'is_active'] if action == 'edit' else ['name', 'code']
        ContractorForm = modelform_factory(Contractor, fields=fields)
        form = ContractorForm(instance=contractor)

        # Aplicar clases de DaisyUI a los campos
        for field_name, field in form.fields.items():
            if field_name == 'is_active':
                field.widget.attrs.update({'class': 'toggle toggle-success'})
            else:
                field.widget.attrs.update({
                    'class': 'input input-bordered w-full',
                    'placeholder': f'Ingrese {field.label.lower()}'
                })

        form_html = render(request, 'components/contractor_form_modal.html', {
            'form': form,
            'contractor': contractor,
            'action': action
        }).content.decode('utf-8')
        
        return JsonResponse({
            'success': True,
            'form_html': form_html
        })

    def post(self, request, contractor_id=None):
        """Procesar formulario de contratista."""
        if contractor_id:
            try:
                contractor = Contractor.objects.get(id=contractor_id)
                action = 'edit'
            except Contractor.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Contratista no encontrado'
                }, status=404)
        else:
            contractor = None
            action = 'create'
        
        # Crear el formulario dinámicamente
        ContractorForm = modelform_factory(Contractor, fields=['name', 'code'])
        form = ContractorForm(request.POST, instance=contractor)
        
        # Aplicar clases de DaisyUI a los campos
        for field_name, field in form.fields.items():
            field.widget.attrs.update({
                'class': 'input input-bordered w-full',
                'placeholder': f'Ingrese {field.label.lower()}'
            })
        
        if form.is_valid():
            contractor = form.save()
            return JsonResponse({
                'success': True,
                'message': f'Contratista {"actualizado" if action == "edit" else "creado"} correctamente',
                'contractor': {
                    'id': contractor.id,
                    'name': contractor.name,
                    'code': contractor.code,
                    'is_active': contractor.is_active,
                    'created_at': contractor.created_at.strftime('%d/%m/%Y %H:%M'),
                    'updated_at': contractor.updated_at.strftime('%d/%m/%Y %H:%M'),
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Error en los datos del formulario',
                'errors': form.errors
            }, status=400)
