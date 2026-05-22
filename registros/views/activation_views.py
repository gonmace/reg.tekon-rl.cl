"""
Vistas genéricas para registros.
"""

from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from registros.forms.activar import create_activar_registro_form
from core.permissions import CoordOrAboveMixin
from typing import Dict, Any


class GenericActivarRegistroView(LoginRequiredMixin, CoordOrAboveMixin, FormView):
    """
    Vista genérica para activar registros.
    Puede ser usada por cualquier aplicación que herede de RegistroBase.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.registro_config = self.get_registro_config()
        self.template_name = 'pages/activar_registro.html'
    
    def get_registro_config(self):
        """Obtiene la configuración del registro. Debe ser sobrescrito."""
        raise NotImplementedError("Debe implementar get_registro_config()")

    def get_success_url_after_activation(self, registro):
        """URL de redirección tras activar. Sobreescribir para personalizar."""
        return f'/{self.registro_config.app_namespace}/{registro.id}/'

    def get_form_class(self):
        """Retorna el formulario configurado para el modelo específico."""
        allow_multiple = getattr(self.registro_config, 'allow_multiple_per_site', False)
        project = getattr(self.registro_config, 'project', False)
        return create_activar_registro_form(
            registro_model=self.registro_config.registro_model,
            title_default=self.registro_config.title,
            description_default=f'Registro {self.registro_config.title} activado desde el formulario',
            allow_multiple_per_site=allow_multiple,
            project=project
        )
    
    def post(self, request, *args, **kwargs):
        if request.POST.get('multi_site') == 'true':
            return self._handle_multi_site(request)
        return super().post(request, *args, **kwargs)

    def _handle_multi_site(self, request):
        from django.db import transaction
        from datetime import date
        from core.models.sites import Site
        from users.models import User

        sitio_ids = request.POST.getlist('sitios')
        user_id = request.POST.get('user')

        if not sitio_ids:
            return JsonResponse({'success': False, 'message': 'Selecciona al menos un sitio.'}, status=400)
        if not user_id:
            return JsonResponse({'success': False, 'message': 'Selecciona un usuario.'}, status=400)

        try:
            user = User.objects.get(pk=user_id, is_active=True, is_deleted=False)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Usuario no válido.'}, status=400)

        fecha = date.today()
        created_count = 0
        skipped_count = 0
        model = self.registro_config.registro_model

        with transaction.atomic():
            for sitio_id in sitio_ids:
                try:
                    sitio = Site.objects.get(pk=sitio_id, is_deleted=False)
                except Site.DoesNotExist:
                    continue

                existing = model.objects.filter(sitio=sitio, user=user, fecha=fecha).first()
                if existing:
                    if hasattr(existing, 'is_deleted') and existing.is_deleted:
                        existing.is_deleted = False
                        existing.save()
                        created_count += 1
                    else:
                        skipped_count += 1
                else:
                    registro_data = {
                        'sitio': sitio,
                        'user': user,
                        'fecha': fecha,
                        'is_active': True,
                        'is_deleted': False,
                    }
                    if hasattr(model, 'title'):
                        registro_data['title'] = self.registro_config.title
                    if hasattr(model, 'description'):
                        registro_data['description'] = f'Registro {self.registro_config.title} activado desde el formulario'
                    model.objects.create(**registro_data)
                    created_count += 1

        msg_parts = []
        if created_count:
            msg_parts.append(f'{created_count} registro{"s" if created_count != 1 else ""} activado{"s" if created_count != 1 else ""}')
        if skipped_count:
            msg_parts.append(f'{skipped_count} ya existía{"n" if skipped_count != 1 else ""}')
        message = ' · '.join(msg_parts) or 'Sin cambios'

        return JsonResponse({
            'success': True,
            'message': message,
            'redirect_url': f'/{self.registro_config.app_namespace}/',
        })

    def form_valid(self, form):
        try:
            # Debug: imprimir los datos del formulario
            print(f"Datos del formulario: {form.cleaned_data}")
            
            # Verificar si ya existe un registro para este sitio, usuario y fecha
            sitio = form.cleaned_data['sitio']
            user = form.cleaned_data['user']
            fecha = form.cleaned_data['fecha']
            
            # Validar que la fecha no esté vacía
            if not fecha:
                from datetime import date
                fecha = date.today()
                print(f"Fecha vacía, usando fecha actual: {fecha}")
            
            # Si no hay campo fecha en el formulario, usar fecha actual
            if 'fecha' not in form.cleaned_data:
                from datetime import date
                fecha = date.today()
                print(f"No hay campo fecha en formulario, usando fecha actual: {fecha}")
            
            print(f"Sitio: {sitio}, User: {user}, Fecha: {fecha}")
            
            existing_registro = self.registro_config.registro_model.objects.filter(
                sitio=sitio, 
                user=user,
                fecha=fecha
            ).first()
            
            if existing_registro:
                if hasattr(existing_registro, 'is_deleted') and existing_registro.is_deleted:
                    # Si existe pero está marcado como eliminado, reactivarlo
                    existing_registro.is_deleted = False
                    existing_registro.save()
                    registro = existing_registro
                else:
                    # Si ya existe y está activo, mostrar error
                    error_message = f'Ya existe un registro activo para el sitio {sitio.name}, usuario {user.username} y fecha {fecha.strftime("%d/%m/%Y")}'
                    if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': error_message
                        }, status=400)
                    else:
                        messages.error(self.request, error_message)
                        return self.form_invalid(form)
            else:
                # Crear nuevo registro
                try:
                    # Obtener el grupo de actividades seleccionado
                    grupo_actividades = form.cleaned_data.get('grupo_actividades')
                    
                    # Crear el registro usando el modelo dinámico
                    registro_data = {
                        'sitio': sitio,
                        'user': user,
                        'fecha': fecha,
                        'is_active': True,
                        'is_deleted': False
                    }
                    model = self.registro_config.registro_model
                    if hasattr(model, 'title'):
                        registro_data['title'] = form.cleaned_data.get('title', '')
                    if hasattr(model, 'description'):
                        registro_data['description'] = form.cleaned_data.get('description', '')
                    
                    # Agregar grupo_actividades si el modelo lo soporta
                    if hasattr(self.registro_config.registro_model, 'grupo_actividades'):
                        registro_data['grupo_actividades'] = grupo_actividades
                    
                    # Agregar estructura si el modelo lo soporta
                    estructura = form.cleaned_data.get('estructura')
                    if hasattr(self.registro_config.registro_model, 'estructura'):
                        registro_data['estructura'] = estructura
                    
                    registro = self.registro_config.registro_model.objects.create(**registro_data)
                    print(f"Registro creado exitosamente: {registro}")

                except Exception as save_error:
                    print(f"Error al guardar: {save_error}")
                    raise save_error
            
            messages.success(self.request, f'Registro activado exitosamente para {registro.sitio.name} - {registro.fecha.strftime("%d/%m/%Y")}')
            
            success_url = self.get_success_url_after_activation(registro)
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Registro activado exitosamente para {registro.sitio.name} - {registro.fecha.strftime("%d/%m/%Y")}',
                    'redirect_url': success_url,
                })
            else:
                return redirect(success_url)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error completo: {error_details}")
            
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Error al activar registro: {str(e)}',
                    'details': error_details
                }, status=400)
            else:
                messages.error(self.request, f'Error al activar registro: {str(e)}')
                return self.form_invalid(form)
    
    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Error en el formulario',
                'errors': form.errors
            }, status=400)
        else:
            return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': self.registro_config.title,
            'app_namespace': self.registro_config.app_namespace,
            'activar_url': self.request.build_absolute_uri(f'/{self.registro_config.app_namespace}/activar/'),
            'allow_multiple_per_site': getattr(self.registro_config, 'allow_multiple_per_site', False),
            'project': getattr(self.registro_config, 'project', False),
        })
        if getattr(self.registro_config, 'header_title', None):
            context['header_title'] = self.registro_config.header_title
        return context
    
