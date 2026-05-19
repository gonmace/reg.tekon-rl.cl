"""
Vistas base para registros.
"""

from django.views.generic import TemplateView, ListView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from core.utils.breadcrumbs import BreadcrumbsMixin
from typing import Dict, Any, List


class RegistroListView(LoginRequiredMixin, BreadcrumbsMixin, ListView):
    """
    Vista base para listar registros.
    """
    template_name = 'registros/list.html'
    context_object_name = 'registros'
    
    def get_queryset(self):
        """Obtiene los registros activos."""
        return self.model.objects.filter(is_active=True, is_deleted=False)
    
    def get_context_data(self, **kwargs):
        """Obtiene el contexto con estadísticas."""
        context = super().get_context_data(**kwargs)
        context['total_registros'] = self.get_queryset().count()
        return context


class RegistroStepsView(LoginRequiredMixin, BreadcrumbsMixin, TemplateView):
    """
    Vista base para mostrar los pasos de un registro.
    """
    template_name = 'registros/steps.html'
    
    def get_context_data(self, **kwargs):
        """Obtiene el contexto con los pasos configurados."""
        context = super().get_context_data(**kwargs)
        
        registro_id = self.kwargs.get('registro_id')
        registro = get_object_or_404(self.model, id=registro_id)
        
        # Obtener configuración de pasos
        steps_config = self.get_steps_config()
        steps_context = self._generate_steps_context(registro, steps_config)
        
        # Generar URL del PDF
        pdf_url = self.get_pdf_url(registro_id)
        
        context.update({
            'registro': registro,
            'steps': steps_context,
            'steps_config': steps_config,
            'pdf_url': pdf_url,
        })
        return context
    
    def get_steps_config(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene la configuración de pasos. Debe ser sobrescrito."""
        return {}
    
    def get_pdf_url(self, registro_id):
        """Obtiene la URL para generar el PDF. Debe ser sobrescrito."""
        return None
    
    def _generate_steps_context(self, registro, steps_config):
        """Genera el contexto para cada paso."""
        steps_context = []
        
        for step_name, config in steps_config.items():
            elemento_class = config.get('elemento_class')
            if elemento_class:
                elemento = elemento_class(registro)
                instance = elemento.get_or_create()
                if instance:
                    elemento = elemento_class(registro, instance)
                
                step_data = {
                    'elemento': elemento,
                    'instance': instance,
                    'title': config.get('title', step_name.title()),
                    'description': config.get('description', ''),
                    'url': f'/{self.app_namespace}/registros/{registro.id}/{step_name}/',
                    'has_data': instance is not None,
                    'step_name': step_name,
                    'registro_id': registro.id,
                    'elements': {
                        'form': {
                            'url': f'/{self.app_namespace}/registros/{registro.id}/{step_name}/',
                            'color': 'primary' if instance else 'warning'
                        },
                        'photos': {
                            'enabled': False,
                            'url': '',
                            'color': 'warning',
                            'count': 0,
                            'required': False,
                            'min_count': 0
                        },
                        'map': {
                            'enabled': False,
                            'status': 'warning',
                            'coordinates': {},
                            'etapa': step_name
                        }
                    }
                }
                
                steps_context.append((step_name, step_data))
        
        return steps_context


class ElementoView(LoginRequiredMixin, View):
    """
    Vista base para manejar elementos de registro.
    """
    
    def get(self, request, registro_id, paso_nombre):
        """Maneja peticiones GET."""
        try:
            registro = get_object_or_404(self.model, id=registro_id)
            elemento_class = self.get_elemento_class(paso_nombre)
            
            if not elemento_class:
                return JsonResponse({'error': f'Paso no válido: {paso_nombre}'}, status=400)
            
            elemento = elemento_class(registro)
            instance = elemento.get_or_create()
            if instance:
                elemento = elemento_class(registro, instance)
            
            form = elemento.get_form()
            sub_elementos = elemento.get_all_sub_elementos()
            
            context = {
                'elemento': elemento,
                'form': form,
                'instance': instance,
                'sub_elementos': sub_elementos,
                'registro': registro,
            }
            
            return self.render_response(request, context)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    def post(self, request, registro_id, paso_nombre):
        """Maneja peticiones POST."""
        try:
            registro = get_object_or_404(self.model, id=registro_id)
            elemento_class = self.get_elemento_class(paso_nombre)
            
            if not elemento_class:
                return JsonResponse({'error': f'Paso no válido: {paso_nombre}'}, status=400)
            
            elemento = elemento_class(registro)
            instance = elemento.get_or_create()
            if instance:
                elemento = elemento_class(registro, instance)
            
            form = elemento.get_form(data=request.POST, files=request.FILES)
            
            if form.is_valid():
                saved_instance = elemento.save(form)
                return JsonResponse({
                    'success': True,
                    'message': elemento.success_message,
                    'object_id': saved_instance.id if saved_instance else None,
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': elemento.error_message,
                    'errors': form.errors,
                }, status=400)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    def get_elemento_class(self, paso_nombre):
        """Obtiene la clase del elemento. Debe ser sobrescrito."""
        return None
    
    def render_response(self, request, context):
        """Renderiza la respuesta. Puede ser sobrescrito."""
        from django.shortcuts import render
        template_name = context['elemento'].template_name or 'registros/elemento_form.html'
        return render(request, template_name, context) 