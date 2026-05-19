"""
Vistas para registros Reporte de construcción.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from .models import RegConstruccion, AvanceComponente, EjecucionPorcentajes
from .forms import AvanceComponenteForm, RegConstruccionForm
from proyectos.models import Componente
from registros.views.steps_views import (
    GenericRegistroStepsView,
    GenericElementoView,
    GenericRegistroTableListView
)
from registros.views.activation_views import GenericActivarRegistroView
from registros.config import RegistroConfig
from .config import REGISTRO_CONFIG
from datetime import date
import json


@require_POST
def guardar_ejecucion(request, registro_id):
    """Guardar los cambios de ejecución actual desde la tabla."""
    print(f"DEBUG: guardar_ejecucion - registro_id={registro_id}, usuario_actual={request.user.username} (ID: {request.user.id})")
    
    try:
        # Primero intentar obtener el registro sin filtro de usuario
        registro = RegConstruccion.objects.get(pk=registro_id)
        print(f"DEBUG: Registro encontrado - ID: {registro.id}, Usuario del registro: {registro.user.username if registro.user else 'None'}")
        
        # Verificar permisos
        if registro.user != request.user and not request.user.is_superuser:
            print(f"DEBUG: Usuario {request.user.username} no tiene permisos para el registro {registro_id}")
            messages.error(request, 'No tienes permisos para modificar este registro.')
            return redirect('reg_construccion:steps', registro_id=registro.pk)
            
    except RegConstruccion.DoesNotExist:
        print(f"DEBUG: Registro con ID {registro_id} no existe")
        messages.error(request, f'Registro con ID {registro_id} no existe.')
        return redirect('reg_construccion:list')
    
    try:
        cambios_realizados = 0
        
        # Procesar cada campo de ejecución actual
        for key, value in request.POST.items():
            if key.startswith('ejec_actual_'):
                componente_id = key.split('_')[2]
                nuevo_valor = int(value) if value else 0
                
                print(f"DEBUG: Procesando componente {componente_id} con valor {nuevo_valor}")
                
                # Validar que el valor esté entre 0 y 100
                if nuevo_valor < 0 or nuevo_valor > 100:
                    messages.error(request, f'El valor para el componente {componente_id} debe estar entre 0 y 100.')
                    return redirect('reg_construccion:steps', registro_id=registro.pk)
                
                # Obtener el componente
                componente = get_object_or_404(Componente, pk=componente_id)
                
                # Obtener el último avance para calcular el porcentaje acumulado
                ultimo_avance = AvanceComponente.objects.filter(
                    registro=registro,
                    componente=componente
                ).order_by('-fecha', '-created_at').first()
                
                # Calcular el porcentaje anterior y acumulado
                if ultimo_avance:
                    # El porcentaje anterior es: ejec_anterior = ultimo_avance.porcentaje_acumulado - ultimo_avance.porcentaje_actual
                    porcentaje_anterior = ultimo_avance.porcentaje_acumulado - ultimo_avance.porcentaje_actual
                    if porcentaje_anterior < 0:
                        porcentaje_anterior = 0
                    # El porcentaje acumulado es: ejec_anterior + ejec_actual
                    porcentaje_acumulado = porcentaje_anterior + nuevo_valor
                    # Asegurar que no exceda 100%
                    porcentaje_acumulado = min(porcentaje_acumulado, 100)
                else:
                    # Si no hay avances previos, el anterior es 0 y el acumulado es igual al actual
                    porcentaje_anterior = 0
                    porcentaje_acumulado = nuevo_valor
                
                # Crear o actualizar el avance de componente
                avance, created = AvanceComponente.objects.update_or_create(
                    registro=registro,
                    componente=componente,
                    fecha=date.today(),
                    defaults={
                        'porcentaje_anterior': porcentaje_anterior,
                        'porcentaje_actual': nuevo_valor,
                        'porcentaje_acumulado': porcentaje_acumulado,
                        'comentarios': f'Actualización desde tabla - {date.today()}'
                    }
                )
                
                avance.save()
                
                cambios_realizados += 1
                print(f"DEBUG: Avance {'creado' if created else 'actualizado'} para componente {componente_id}")
        
        if cambios_realizados > 0:
            messages.success(request, f'Se guardaron {cambios_realizados} cambios de ejecución exitosamente.')
            print(f"DEBUG: Se guardaron {cambios_realizados} cambios exitosamente")
        else:
            messages.warning(request, 'No se realizaron cambios.')
            print("DEBUG: No se realizaron cambios")
            
    except Exception as e:
        print(f"DEBUG: Error en guardar_ejecucion: {str(e)}")
        messages.error(request, f'Error al guardar los cambios: {str(e)}')
    
    return redirect('reg_construccion:steps', registro_id=registro.pk)


@login_required
@csrf_exempt
def actualizar_ejecucion_ajax(request, registro_id):
    """Actualizar ejecución vía AJAX."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            registro = get_object_or_404(RegConstruccion, pk=registro_id, user=request.user)
            
            cambios_realizados = 0
            
            for item in data.get('ejecuciones', []):
                componente_id = item.get('componente_id')
                nuevo_valor = int(item.get('valor', 0))
                
                if nuevo_valor < 0 or nuevo_valor > 100:
                    return JsonResponse({
                        'success': False,
                        'error': f'El valor para el componente {componente_id} debe estar entre 0 y 100.'
                    })
                
                componente = get_object_or_404(Componente, pk=componente_id)
                
                # Obtener el último avance para calcular el porcentaje acumulado
                ultimo_avance = AvanceComponente.objects.filter(
                    registro=registro,
                    componente=componente
                ).order_by('-fecha', '-created_at').first()
                
                # Calcular el porcentaje anterior y acumulado
                if ultimo_avance:
                    # El porcentaje anterior es: ejec_anterior = ultimo_avance.porcentaje_acumulado - ultimo_avance.porcentaje_actual
                    porcentaje_anterior = ultimo_avance.porcentaje_acumulado - ultimo_avance.porcentaje_actual
                    if porcentaje_anterior < 0:
                        porcentaje_anterior = 0
                    # El porcentaje acumulado es: ejec_anterior + ejec_actual
                    porcentaje_acumulado = porcentaje_anterior + nuevo_valor
                    # Asegurar que no exceda 100%
                    porcentaje_acumulado = min(porcentaje_acumulado, 100)
                else:
                    # Si no hay avances previos, el anterior es 0 y el acumulado es igual al actual
                    porcentaje_anterior = 0
                    porcentaje_acumulado = nuevo_valor
                
                avance, created = AvanceComponente.objects.update_or_create(
                    registro=registro,
                    componente=componente,
                    fecha=date.today(),
                    defaults={
                        'porcentaje_actual': nuevo_valor,
                        'porcentaje_acumulado': porcentaje_acumulado,
                        'comentarios': f'Actualización AJAX - {date.today()}'
                    }
                )
                
                avance.save()
                
                cambios_realizados += 1
            
            return JsonResponse({
                'success': True,
                'message': f'Se guardaron {cambios_realizados} cambios exitosamente.',
                'cambios_realizados': cambios_realizados
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al procesar los cambios: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


# Vistas genéricas para registros
class ListRegistrosView(GenericRegistroTableListView):
    """Vista para listar registros Reporte de construcción usando tabla genérica."""
    
    def get_registro_config(self):
        return REGISTRO_CONFIG
    
    def get_breadcrumbs(self):
        """Genera breadcrumbs para la página de listado."""
        return [
            {'label': 'Inicio', 'url': reverse('dashboard:dashboard')},
            {'label': 'Reporte de construcción'}  # Página actual sin URL
        ]


class StepsRegistroView(GenericRegistroStepsView):
    """Vista para mostrar los pasos de un registro Reporte de construcción."""
    
    def get_registro_config(self):
        return REGISTRO_CONFIG
    
    def get_context_data(self, **kwargs):
        """Obtiene el contexto y establece el registro."""
        registro_id = self.kwargs.get('registro_id')
        self.registro = get_object_or_404(self.registro_config.registro_model, id=registro_id)
        context = super().get_context_data(**kwargs)
        return context
    
    def get_header_title(self):
        """Obtiene el título del header basado en PTI ID o Operador ID."""
        if hasattr(self, 'registro') and self.registro:
            # Intentar obtener PTI ID primero
            pti_id = getattr(getattr(self.registro, 'sitio', None), 'pti_cell_id', None)
            if pti_id:
                return pti_id
            
            # Si no hay PTI ID, intentar Operador ID
            operador_id = getattr(getattr(self.registro, 'sitio', None), 'operator_id', None)
            if operador_id:
                return operador_id
        
        return super().get_header_title()
    
    def get_pdf_url(self, registro_id):
        """Obtiene la URL para generar el PDF."""
        return reverse('reg_construccion:pdf', kwargs={'registro_id': registro_id})


class ElementoRegistroView(GenericElementoView):
    """Vista para manejar elementos de registro Reporte de construcción."""
    
    def get_registro_config(self):
        return REGISTRO_CONFIG
    
    def get(self, request, registro_id, paso_nombre):
        """Establece el registro antes de procesar la petición."""
        self.registro = self.registro_config.registro_model.objects.get(id=registro_id)
        return super().get(request, registro_id, paso_nombre)
    
    def get_header_title(self):
        """Obtiene el título del header basado en el nombre del sitio."""
        if hasattr(self, 'registro') and self.registro:
            name = getattr(getattr(self.registro, 'sitio', None), 'name', 'Sin PTI')
            return name
        return super().get_header_title()


class ActivarRegistroView(GenericActivarRegistroView):
    """Vista para activar registros Reporte de construcción."""
    
    def get_registro_config(self):
        return REGISTRO_CONFIG


class TableOnlyView(GenericElementoView):
    template_name = 'pages/tabla_avance.html'

    def get_registro_config(self):
        from .config import REGISTRO_CONFIG
        return REGISTRO_CONFIG

    def get(self, request, registro_id, paso_nombre):
        registro = self.registro_config.registro_model.objects.get(id=registro_id)
        paso_config = self.registro_config.pasos.get(paso_nombre)
        elemento_config = paso_config.elemento
        instance = None
        if hasattr(elemento_config, 'model'):
            instance = elemento_config.model.objects.filter(registro=registro).first()
        # Busca el subelemento tipo 'table'
        table_sub = next((s for s in elemento_config.sub_elementos if s.tipo == 'table'), None)
        data = self._get_table_data(registro, table_sub, instance) if table_sub else []
        context = {
            'registro': registro,
            'paso_config': paso_config,
            'elemento_config': elemento_config,
            'breadcrumbs': self.get_breadcrumbs(),
            'header_title': self.get_header_title(),
            'config': table_sub.config if table_sub else {},
            'data': data,
        }
        return render(request, self.template_name, context)


# Nuevas vistas para CRUD completo
class RegConstruccionCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear nuevos registros de construcción."""
    model = RegConstruccion
    form_class = RegConstruccionForm
    template_name = 'reg_construccion/registro_form.html'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Reporte de construcción creado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('reg_construccion:steps', kwargs={'registro_id': self.object.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'label': 'Inicio', 'url': reverse('dashboard:dashboard')},
            {'label': 'Reportes de Construcción', 'url': reverse('reg_construccion:list')},
            {'label': 'Nuevo Reporte'}
        ]
        context['header_title'] = 'Nuevo Reporte de Construcción'
        return context


class RegConstruccionUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar registros de construcción existentes."""
    model = RegConstruccion
    form_class = RegConstruccionForm
    template_name = 'reg_construccion/registro_form.html'
    
    def get_queryset(self):
        return RegConstruccion.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Reporte de construcción actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('reg_construccion:steps', kwargs={'registro_id': self.object.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'label': 'Inicio', 'url': reverse('dashboard:dashboard')},
            {'label': 'Reportes de Construcción', 'url': reverse('reg_construccion:list')},
            {'label': 'Editar Reporte'}
        ]
        context['header_title'] = f'Editar Reporte: {self.object.title}'
        return context


class RegConstruccionDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar registros de construcción."""
    model = RegConstruccion
    template_name = 'reg_construccion/registro_confirm_delete.html'
    
    def get_queryset(self):
        return RegConstruccion.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        messages.success(self.request, 'Reporte de construcción eliminado exitosamente.')
        return reverse('reg_construccion:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'label': 'Inicio', 'url': reverse('dashboard:dashboard')},
            {'label': 'Reportes de Construcción', 'url': reverse('reg_construccion:list')},
            {'label': 'Eliminar Reporte'}
        ]
        context['header_title'] = f'Eliminar Reporte: {self.object.title}'
        return context


@login_required
def dashboard_construccion(request):
    """Dashboard específico para reportes de construcción."""
    # Obtener estadísticas
    total_registros = RegConstruccion.objects.filter(user=request.user).count()
    registros_hoy = RegConstruccion.objects.filter(
        user=request.user,
        created_at__date=date.today()
    ).count()

    # Últimos registros
    ultimos_registros = RegConstruccion.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]

    # Componentes más activos
    componentes_activos = Componente.objects.filter(
        avances_componente__registro__user=request.user
    ).distinct()[:10]

    context = {
        'total_registros': total_registros,
        'registros_hoy': registros_hoy,
        'ultimos_registros': ultimos_registros,
        'componentes_activos': componentes_activos,
        'breadcrumbs': [
            {'label': 'Inicio', 'url': reverse('dashboard:dashboard')},
            {'label': 'Dashboard Construcción'}
        ],
        'header_title': 'Dashboard de Construcción'
    }

    return render(request, 'reg_construccion/dashboard.html', context)


@login_required
def get_contractors(request):
    """Obtener lista de contratistas activos."""
    try:
        from core.models.contractors import Contractor
        contractors = Contractor.objects.filter(is_active=True).values('id', 'name', 'code')
        return JsonResponse(list(contractors), safe=False)
    except Exception as e:
        return JsonResponse({
            'error': f'Error al obtener contratistas: {str(e)}'
        }, status=400)


@login_required
def get_users_ito(request):
    """Obtener lista de usuarios ITO."""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users = User.objects.filter(is_active=True, is_deleted=False, user_type__in=User.ITO_LIKE_ROLES).values('id', 'username', 'first_name', 'last_name')
        return JsonResponse(list(users), safe=False)
    except Exception as e:
        return JsonResponse({
            'error': f'Error al obtener usuarios ITO: {str(e)}'
        }, status=400)


@login_required
@require_POST
def update_contratista(request, registro_id):
    """Actualizar el contratista de un registro de construcción."""
    try:
        registro = get_object_or_404(RegConstruccion, pk=registro_id, user=request.user)
        data = json.loads(request.body)
        contratista_id = data.get('contractor_id') or data.get('contratista_id')
        
        if contratista_id:
            from core.models.contractors import Contractor
            contratista = get_object_or_404(Contractor, pk=contratista_id)
            registro.contratista = contratista
        else:
            registro.contratista = None
        
        registro.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Constructor actualizado correctamente',
            'contratista_name': registro.contratista.name if registro.contratista else 'Sin asignar'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al actualizar constructor: {str(e)}'
        }, status=400)


@login_required
@require_POST
def update_ito(request, registro_id):
    """Actualizar el ITO de un registro de construcción."""
    try:
        registro = get_object_or_404(RegConstruccion, pk=registro_id, user=request.user)
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = get_object_or_404(User, pk=user_id)
            registro.user = user
        else:
            registro.user = None
        
        registro.save()
        
        return JsonResponse({
            'success': True,
            'message': 'ITO actualizado correctamente',
            'user_name': registro.user.username if registro.user else 'Sin asignar'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al actualizar ITO: {str(e)}'
        }, status=400)


@login_required
@require_POST
def update_estado(request, registro_id):
    """Actualizar el estado de un registro de construcción."""
    try:
        print(f"DEBUG: Actualizando estado para registro_id={registro_id}, usuario={request.user.id}")
        
        # Verificar si el registro existe
        try:
            registro = RegConstruccion.objects.get(pk=registro_id)
            print(f"DEBUG: Registro encontrado: {registro.id}, usuario del registro: {registro.user.id if registro.user else 'None'}")
        except RegConstruccion.DoesNotExist:
            print(f"DEBUG: Registro con ID {registro_id} no existe")
            return JsonResponse({
                'success': False,
                'message': f'Registro con ID {registro_id} no existe'
            }, status=404)
        
        # Verificar si el usuario tiene permisos
        if registro.user != request.user and not request.user.is_superuser:
            print(f"DEBUG: Usuario {request.user.id} no tiene permisos para el registro {registro_id}")
            return JsonResponse({
                'success': False,
                'message': 'No tienes permisos para modificar este registro'
            }, status=403)
        
        data = json.loads(request.body)
        estado = data.get('estado')
        print(f"DEBUG: Estado recibido: {estado}")
        
        if estado:
            # Validar que el estado sea válido
            estados_validos = ['construccion', 'paralizado', 'cancelado', 'concluido']
            if estado not in estados_validos:
                print(f"DEBUG: Estado no válido: {estado}")
                return JsonResponse({
                    'success': False,
                    'message': f'Estado no válido: {estado}'
                }, status=400)
            
            registro.estado = estado
        else:
            registro.estado = 'construccion'  # Estado por defecto
        
        registro.save()
        print(f"DEBUG: Estado actualizado exitosamente a: {registro.estado}")
        
        # Obtener el texto del estado para la respuesta
        estado_map = {
            'construccion': 'Construcción',
            'paralizado': 'Paralizado',
            'cancelado': 'Cancelado',
            'concluido': 'Concluido',
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Estado actualizado correctamente',
            'estado_name': estado_map.get(registro.estado, registro.estado)
        })
        
    except Exception as e:
        print(f"DEBUG: Error en update_estado: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error al actualizar estado: {str(e)}'
        }, status=400)