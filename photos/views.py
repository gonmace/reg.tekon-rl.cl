from django.views.generic import ListView
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from core.utils.breadcrumbs import BreadcrumbsMixin
from core.permissions import NotVisitaMixin, SuperuserRequiredMixin, ItoLikeMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
import json
import os
from .models import Photos
from django.apps import apps
from django.http import Http404

# Diccionario global para almacenar templates personalizados
PHOTOS_TEMPLATES = {}

def set_photos_template(app_name, step_name, template_name):
    """
    Configura el template personalizado para una combinación específica de app_name y step_name.
    
    Args:
        app_name: Nombre de la aplicación
        step_name: Nombre del paso/etapa
        template_name: Nombre del template a usar
    """
    template_key = f"{app_name}_{step_name}"
    PHOTOS_TEMPLATES[template_key] = template_name

def set_photos_template_for_step(step_name, template_name):
    """
    Configura el template personalizado para un step_name específico, 
    independientemente del app_name.
    
    Args:
        step_name: Nombre del paso/etapa
        template_name: Nombre del template a usar
    """
    # Usar un patrón que funcione para cualquier app_name
    PHOTOS_TEMPLATES[f"*_{step_name}"] = template_name

def get_registro_from_id(registro_id):
    """
    Función helper para obtener el registro basado en el ID.
    """
    try:
        from reg_txtss.models import RegTxtss
        return RegTxtss.objects.get(id=registro_id)
    except Exception:
        pass

    return None


def get_app_name_from_registro(registro):
    """
    Función helper para determinar el app_name basado en el tipo de registro.
    """
    if not registro:
        return None
    
    app_label = registro._meta.app_label
    
    # Mapeo de app_label a app_name
    app_mapping = {
        'reg_txtss': 'txtss',
        'registros_txtss': 'txtss',
    }
    
    return app_mapping.get(app_label)


def get_app_name_from_registro_id(registro_id):
    """
    Función helper para obtener el app_name basado en el ID del registro.
    """
    registro = get_registro_from_id(registro_id)
    return get_app_name_from_registro(registro)

def get_app_name_from_request(request, registro):
    """Obtiene el app_name desde la request o del registro."""
    # Intentar obtener app_name desde la URL
    resolved_url = request.resolver_match
    if resolved_url and hasattr(resolved_url, 'kwargs'):
        app_name = resolved_url.kwargs.get('app_name')
        if app_name:
            return app_name
    
    # Si no se encuentra en la URL, usar get_reg_app_name del registro
    if registro and hasattr(registro, 'get_reg_app_name'):
        return registro.get_reg_app_name()
    
    # Si no se puede detectar desde la URL, obtenerlo del registro como fallback
    return get_app_name_from_registro(registro)

def get_url_params_from_request(request):
    """Obtiene los parámetros de URL desde la request, incluyendo los de la URL padre."""
    resolved_url = request.resolver_match
    if resolved_url and hasattr(resolved_url, 'kwargs'):
        # Obtener parámetros de la URL actual
        params = resolved_url.kwargs.copy()
        
        if 'app_name' not in params:
            if request.path.startswith('/reg_txtss/'):
                params['app_name'] = 'reg_txtss'
        
        return params
    
    return {}

def get_params_from_request(request, **kwargs):
    """Obtiene los parámetros necesarios desde la request o kwargs."""
    # Obtener parámetros desde la request
    params = get_url_params_from_request(request)
    
    # Combinar con kwargs
    registro_id = kwargs.get('registro_id') or params.get('registro_id')
    step_name = kwargs.get('step_name') or params.get('step_name')
    paso_nombre = kwargs.get('paso_nombre') or params.get('paso_nombre')
    app_name = kwargs.get('app_name') or params.get('app_name')
    
    # Si no tenemos registro_id, intentar obtenerlo de la URL
    if not registro_id:
        # Extraer registro_id de la URL
        path_parts = request.path.split('/')
        for i, part in enumerate(path_parts):
            if part.isdigit() and i < len(path_parts) - 1:
                registro_id = int(part)
                break
    
    # Si no tenemos step_name, usar paso_nombre
    if not step_name:
        step_name = paso_nombre
    
    # Si no tenemos app_name, obtenerlo del registro usando get_reg_app_name
    if not app_name and registro_id:
        try:
            # Intentar obtener el registro y usar get_reg_app_name
            registro = get_registro_from_id(registro_id)
            if registro and hasattr(registro, 'get_reg_app_name'):
                app_name = registro.get_reg_app_name()
        except Exception:
            pass
    
    if not app_name:
        if request.path.startswith('/reg_txtss/'):
            app_name = 'reg_txtss'
    
    return {
        'registro_id': registro_id,
        'step_name': step_name,
        'app_name': app_name
    }


class ListPhotosView(BreadcrumbsMixin, ListView):
    model = Photos
    context_object_name = 'photos'
    template_name = 'widgets/camera_widget_page.html'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            photos = self.get_queryset()
            data = [
                {
                    'id': p.id,
                    'url': p.imagen.url,
                    'descripcion': p.descripcion or '',
                    'exif_lat': p.exif_lat,
                    'exif_lon': p.exif_lon,
                    'exif_datetime': p.exif_datetime.strftime('%d/%m/%Y %H:%M') if p.exif_datetime else None,
                }
                for p in photos
            ]
            return JsonResponse({'success': True, 'photos': data})
        return super().get(request, *args, **kwargs)

    def get_template_names(self):
        """Retorna el template a usar, priorizando el template personalizado"""
        # Obtener el template personalizado del diccionario global
        app_name = self.kwargs.get('app_name')
        step_name = self.kwargs.get('step_name')
        paso_nombre = self.kwargs.get('paso_nombre')
        
        if not step_name:
            step_name = paso_nombre
            
        # Buscar template personalizado por app_name y step_name
        if app_name and step_name:
            # Primero buscar coincidencia exacta
            template_key = f"{app_name}_{step_name}"
            if template_key in PHOTOS_TEMPLATES:
                return [PHOTOS_TEMPLATES[template_key]]
            
            # Luego buscar patrón con wildcard
            wildcard_key = f"*_{step_name}"
            if wildcard_key in PHOTOS_TEMPLATES:
                return [PHOTOS_TEMPLATES[wildcard_key]]
        
        # Si no hay template personalizado, usar el por defecto
        return [self.template_name]

    def get_queryset(self):
        # Obtener parámetros desde la request
        params = get_url_params_from_request(self.request)
        app_name = params.get('app_name') or self.kwargs.get('app_name')
        step_name = params.get('step_name') or self.kwargs.get('step_name')
        paso_nombre = params.get('paso_nombre') or self.kwargs.get('paso_nombre')
        registro_id = params.get('registro_id') or self.kwargs.get('registro_id')

        if not registro_id:
            resolved_url = self.request.resolver_match
            if resolved_url and hasattr(resolved_url, 'kwargs'):
                registro_id = resolved_url.kwargs.get('registro_id')
                paso_nombre = resolved_url.kwargs.get('paso_nombre')

        # Determinar app_name dinámicamente si no está
        if not app_name:
            # Intentar obtener el registro y usar get_reg_app_name
            try:
                registro = get_registro_from_id(registro_id)
                if registro and hasattr(registro, 'get_reg_app_name'):
                    app_name = registro.get_reg_app_name()
                else:
                    app_name = get_app_name_from_registro_id(registro_id)
            except Exception:
                app_name = get_app_name_from_registro_id(registro_id)
            
            if not app_name:
                raise Http404("No se pudo determinar la aplicación")

        # Determinar step_name dinámicamente si no está
        if not step_name:
            step_name = paso_nombre
        if not step_name:
            raise Http404("No se pudo determinar la etapa")

        registro = get_registro_from_id(registro_id)
        if not registro:
            raise Http404("Registro no encontrado")

        if step_name == 'sitio':
            model_class = type(registro)
            object_id = registro.id
            etapa = 'sitio'
        else:
            try:
                # Usar el app_label real del registro, no el app_name mapeado
                app_label = registro._meta.app_label
                model_class = apps.get_model(app_label, f"R{step_name.capitalize()}")
                etapa = model_class.get_etapa()
                try:
                    etapa_obj = model_class.objects.get(registro_id=registro_id)
                    object_id = etapa_obj.id
                except model_class.DoesNotExist:
                    object_id = None
            except LookupError:
                # Si no se encuentra el modelo de la etapa, usar el registro principal
                # Esto es útil para pasos que solo tienen componentes (como fotos)
                model_class = type(registro)
                object_id = registro.id
                etapa = step_name

        content_type = ContentType.objects.get_for_model(model_class)

        if object_id is None:
            # Si no existe el objeto de la etapa, no deberíamos mostrar fotos
            # porque las fotos están asociadas al objeto de la etapa específica
            return Photos.objects.none()

        # Buscar fotos asociadas al modelo específico de la etapa
        queryset = Photos.objects.filter(
            app=registro._meta.app_label,
            object_id=object_id,
            etapa=etapa,
            content_type=content_type
        )
        
        # Si no hay fotos, buscar también en el registro principal (compatibilidad con fotos existentes)
        if queryset.count() == 0 and step_name != 'sitio':
            registro_content_type = ContentType.objects.get_for_model(type(registro))
            queryset = Photos.objects.filter(
                app=registro._meta.app_label,
                object_id=registro.id,
                etapa=etapa,
                content_type=registro_content_type
            )
        
        # Debug: imprimir información para diagnóstico
        print(f"DEBUG - ListPhotosView.get_queryset:")
        print(f"  app: {registro._meta.app_label}")
        print(f"  object_id: {object_id}")
        print(f"  etapa: {etapa}")
        print(f"  step_name: {step_name}")
        print(f"  registro_id: {registro_id}")
        print(f"  queryset count: {queryset.count()}")
        
        return queryset

    def get_breadcrumbs(self):
        """Genera breadcrumbs dinámicos basados en el registro y etapa"""
        breadcrumbs = [
            {'label': 'Inicio', 'url_name': 'dashboard:dashboard'},
        ]
        registro_id = self.kwargs.get('registro_id')
        if registro_id:
            registro = get_registro_from_id(registro_id)
            if registro:
                try:
                    sitio_cod = registro.sitio.pti_cell_id
                except Exception:
                    sitio_cod = getattr(registro.sitio, 'operator_id', 'Sitio')
                app_namespace = registro._meta.app_label  # namespace real
                app_label = get_app_name_from_registro(registro) or app_namespace
                breadcrumbs.append({'label': app_label.upper() if app_label else 'Registro', 'url_name': f'{app_namespace}:list'})
                breadcrumbs.append({
                    'label': sitio_cod,
                    'url_name': f'{app_namespace}:steps',
                    'url_kwargs': {'registro_id': registro_id}
                })
                breadcrumbs.append({'label': 'Imágenes'})
            else:
                breadcrumbs.append({'label': 'Registro'})
        else:
            breadcrumbs.append({'label': 'Registro'})
        return self._resolve_breadcrumbs(breadcrumbs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener parámetros desde la request
        params = get_url_params_from_request(self.request)
        app_name = params.get('app_name') or self.kwargs.get('app_name')
        step_name = params.get('step_name') or self.kwargs.get('step_name')
        paso_nombre = params.get('paso_nombre') or self.kwargs.get('paso_nombre')
        registro_id = params.get('registro_id') or self.kwargs.get('registro_id')
        
        if not registro_id:
            resolved_url = self.request.resolver_match
            if resolved_url and hasattr(resolved_url, 'kwargs'):
                registro_id = resolved_url.kwargs.get('registro_id')
                paso_nombre = resolved_url.kwargs.get('paso_nombre')
        context['registro_id'] = registro_id
        context['upload_url'] = self.request.path.rstrip('/') + '/upload/'
        if not app_name:
            # Intentar obtener el registro y usar get_reg_app_name
            try:
                registro = get_registro_from_id(registro_id)
                if registro and hasattr(registro, 'get_reg_app_name'):
                    app_name = registro.get_reg_app_name()
                else:
                    app_name = get_app_name_from_registro_id(registro_id)
            except Exception:
                app_name = get_app_name_from_registro_id(registro_id)
            
            if not app_name:
                raise Http404("No se pudo determinar la aplicación")
        if not step_name:
            step_name = paso_nombre
        context['app_name'] = app_name
        context['step_name'] = step_name
        title = self.kwargs.get('title')
        if not title:
            title = step_name or 'sitio'
        context['title'] = title
        if registro_id:
            registro = get_registro_from_id(registro_id)
            if registro:
                context['registro_txtss'] = registro
                context['sitio'] = registro.sitio
            else:
                context['error'] = 'Registro no encontrado'
        return context

    def get_header_title(self):
        step_name = self.kwargs.get('step_name')
        if not step_name:
            paso_nombre = self.kwargs.get('paso_nombre')
            step_name = paso_nombre
        if step_name:
            return step_name.capitalize()
        return super().get_header_title()

@method_decorator(csrf_exempt, name='dispatch')
class UploadPhotosView(LoginRequiredMixin, ItoLikeMixin, View):
    def post(self, request, registro_id=None, paso_nombre=None, app_name=None, step_name=None):
        if not registro_id:
            resolved_url = request.resolver_match
            if resolved_url and hasattr(resolved_url, 'kwargs'):
                registro_id = resolved_url.kwargs.get('registro_id')
                paso_nombre = resolved_url.kwargs.get('paso_nombre')
        if not step_name:
            step_name = paso_nombre
        try:
            registro = get_registro_from_id(registro_id)
            if not registro:
                return JsonResponse({
                    'success': False,
                    'message': f'Registro con ID {registro_id} no encontrado'
                }, status=400)
            files = request.FILES.getlist('photos')
            if not files:
                return JsonResponse({
                    'success': False,
                    'message': 'No se recibieron archivos'
                }, status=400)
            descripcion = request.POST.get('descripcion', '')
            from django.contrib.contenttypes.models import ContentType
            
            # Determinar el content_type y object_id según la etapa
            if step_name == 'sitio':
                model_class = type(registro)
                content_type = ContentType.objects.get_for_model(model_class)
                object_id = registro.id
            else:
                # Intentar buscar un modelo específico para el paso
                try:
                    app_label = registro._meta.app_label
                    model_class = apps.get_model(app_label, f"R{step_name.capitalize()}")
                    content_type = ContentType.objects.get_for_model(model_class)
                    try:
                        etapa_obj = model_class.objects.get(registro_id=registro_id)
                        object_id = etapa_obj.id
                    except model_class.DoesNotExist:
                        return JsonResponse({
                            'success': False,
                            'message': f'No existe el registro de la etapa {step_name}. Debes crear primero el registro.'
                        }, status=400)
                except LookupError:
                    # Si no se encuentra el modelo específico, usar el registro principal
                    # Esto maneja pasos que solo tienen sub-elementos (como 'imagenes', 'mandato', etc.)
                    model_class = type(registro)
                    content_type = ContentType.objects.get_for_model(model_class)
                    object_id = registro.id
            
            if not app_name:
                app_name = get_app_name_from_request(request, registro)
            photos_creadas = []
            for file in files:
                if file.content_type.startswith('image/'):
                    photo = Photos.objects.create(
                        imagen=file,
                        descripcion=descripcion,
                        app=registro._meta.app_label,  # Usar el app_label real del registro
                        content_type=content_type,
                        object_id=object_id,
                        etapa=step_name
                    )
                    # Recargar para obtener EXIF extraído en save()
                    photo.refresh_from_db()
                    photos_creadas.append({
                        'id': photo.id,
                        'url': photo.imagen.url,
                        'descripcion': photo.descripcion,
                        'created_at': photo.created_at.strftime('%d/%m/%Y %H:%M'),
                        'exif_lat': photo.exif_lat,
                        'exif_lon': photo.exif_lon,
                        'exif_datetime': photo.exif_datetime.strftime('%d/%m/%Y %H:%M') if photo.exif_datetime else None,
                    })
            if not photos_creadas:
                return JsonResponse({
                    'success': False,
                    'message': 'No se pudieron procesar los archivos. Asegúrate de que sean imágenes válidas.'
                }, status=400)
            return JsonResponse({
                'success': True,
                'photos': photos_creadas,
                'message': f'Se subieron {len(photos_creadas)} fotos correctamente'
            })
        except Exception as e:
            import traceback
            print(f"Error en UploadPhotosView: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'Error al subir fotos: {str(e)}'
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class UpdatePhotoView(LoginRequiredMixin, ItoLikeMixin, View):
    def post(self, request, registro_id=None, paso_nombre=None, app_name=None, step_name=None):
        if not registro_id:
            resolved_url = request.resolver_match
            if resolved_url and hasattr(resolved_url, 'kwargs'):
                registro_id = resolved_url.kwargs.get('registro_id')
                paso_nombre = resolved_url.kwargs.get('paso_nombre')
        if not step_name:
            step_name = paso_nombre
        try:
            data = json.loads(request.body)
            photo_id = data.get('photo_id')
            descripcion = data.get('descripcion', '')
            registro = get_registro_from_id(registro_id)
            if not registro:
                return JsonResponse({'success': False, 'message': 'Registro no encontrado'}, status=404)
            if not app_name:
                app_name = get_app_name_from_request(request, registro)
            if step_name == 'sitio':
                model_class = type(registro)
                etapa = 'sitio'
                object_id = registro.id
            else:
                try:
                    model_class = apps.get_model(app_name, f"R{step_name.capitalize()}")
                    etapa = model_class.get_etapa()
                    try:
                        etapa_obj = model_class.objects.get(registro_id=registro_id)
                        object_id = etapa_obj.id
                    except model_class.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Etapa no encontrada'}, status=404)
                except LookupError:
                    # Si no hay modelo específico para este step, usar el registro principal
                    model_class = type(registro)
                    etapa = step_name
                    object_id = registro.id
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(model_class)
            try:
                photo = Photos.objects.get(id=photo_id, app=registro._meta.app_label, object_id=object_id, etapa=etapa)
            except Photos.DoesNotExist:
                # Si no se encuentra, buscar en el registro principal (compatibilidad con fotos existentes)
                if step_name != 'sitio':
                    registro_content_type = ContentType.objects.get_for_model(type(registro))
                    try:
                        photo = Photos.objects.get(id=photo_id, app=registro._meta.app_label, object_id=registro.id, etapa=etapa, content_type=registro_content_type)
                    except Photos.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Foto no encontrada'}, status=404)
                else:
                    return JsonResponse({'success': False, 'message': 'Foto no encontrada'}, status=404)
            photo.descripcion = descripcion
            photo.save()
            return JsonResponse({'success': True, 'message': 'Descripción actualizada correctamente'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al actualizar: {str(e)}'}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ReorderPhotosView(View):
    def post(self, request, registro_id=None, paso_nombre=None, app_name=None, step_name=None):
        # Obtener parámetros desde la request
        params = get_params_from_request(request, registro_id=registro_id, paso_nombre=paso_nombre, app_name=app_name, step_name=step_name)
        registro_id = params['registro_id']
        step_name = params['step_name']
        app_name = params['app_name']
        try:
            data = json.loads(request.body)
            orden = data.get('orden', [])
            registro = get_registro_from_id(registro_id)
            if not registro:
                return JsonResponse({'success': False, 'message': 'Registro no encontrado'}, status=404)
            if not app_name:
                app_name = get_app_name_from_request(request, registro)
            if step_name == 'sitio':
                model_class = type(registro)
                etapa = 'sitio'
                object_id = registro.id
            else:
                try:
                    model_class = apps.get_model(app_name, f"R{step_name.capitalize()}")
                    etapa = model_class.get_etapa()
                    try:
                        etapa_obj = model_class.objects.get(registro_id=registro_id)
                        object_id = etapa_obj.id
                    except model_class.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Etapa no encontrada'}, status=404)
                except LookupError:
                    # Si no hay modelo específico para este step, usar el registro principal
                    model_class = type(registro)
                    etapa = step_name
                    object_id = registro.id
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(model_class)
            for index, photo_id in enumerate(orden):
                # Intentar actualizar en el modelo específico de la etapa
                updated = Photos.objects.filter(id=photo_id, app=registro._meta.app_label, object_id=object_id, etapa=etapa).update(orden=index)

                # Si no se actualizó, intentar en el registro principal (compatibilidad con fotos existentes)
                if updated == 0 and step_name != 'sitio':
                    registro_content_type = ContentType.objects.get_for_model(type(registro))
                    Photos.objects.filter(id=photo_id, app=registro._meta.app_label, object_id=registro.id, etapa=etapa, content_type=registro_content_type).update(orden=index)
            # .update() no dispara señales post_save → rebuild explícito
            try:
                from actividades.context_builder import rebuild_contexto
                rebuild_contexto(registro)
            except Exception:
                pass
            return JsonResponse({'success': True, 'message': 'Orden actualizado correctamente'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al reordenar: {str(e)}'}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class DeletePhotoView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def post(self, request, photo_id, registro_id=None, paso_nombre=None, app_name=None, step_name=None):
        resolved_url = request.resolver_match
        if resolved_url and hasattr(resolved_url, 'kwargs'):
            if not registro_id:
                registro_id = resolved_url.kwargs.get('registro_id')
            if not paso_nombre:
                paso_nombre = resolved_url.kwargs.get('paso_nombre')
        if not step_name:
            step_name = paso_nombre
        if not app_name:
            registro = get_registro_from_id(registro_id)
            if registro:
                app_name = get_app_name_from_registro(registro)
            if not app_name:
                app_name = None
        try:
            registro = get_registro_from_id(registro_id)
            if not registro:
                return JsonResponse({'success': False, 'message': 'Registro no encontrado'}, status=404)
            if step_name == 'sitio':
                model_class = type(registro)
                etapa = 'sitio'
                object_id = registro.id
            else:
                try:
                    model_class = apps.get_model(app_name, f"R{step_name.capitalize()}")
                    etapa = model_class.get_etapa()
                    try:
                        etapa_obj = model_class.objects.get(registro_id=registro_id)
                        object_id = etapa_obj.id
                    except model_class.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Etapa no encontrada'}, status=404)
                except LookupError:
                    # Si no hay modelo específico para este step, usar el registro principal
                    model_class = type(registro)
                    etapa = step_name
                    object_id = registro.id
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(model_class)
            try:
                photo = Photos.objects.get(id=photo_id, app=registro._meta.app_label, object_id=object_id, etapa=etapa)
            except Photos.DoesNotExist:
                # Si no se encuentra, buscar en el registro principal (compatibilidad con fotos existentes)
                if step_name != 'sitio':
                    registro_content_type = ContentType.objects.get_for_model(type(registro))
                    try:
                        photo = Photos.objects.get(id=photo_id, app=registro._meta.app_label, object_id=registro.id, etapa=etapa, content_type=registro_content_type)
                    except Photos.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Foto no encontrada'}, status=404)
                else:
                    return JsonResponse({'success': False, 'message': 'Foto no encontrada'}, status=404)
            photo.delete()
            return JsonResponse({'success': True, 'message': 'Foto eliminada correctamente'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al eliminar: {str(e)}'}, status=400)


# ── Gallery (admin view — all photos) ──────────────────────────────────────

def _get_reg_ids_for_sitio_filter(sitio_id=None, tipo_sitio=None):
    """Return RegTxtss IDs filtered by site id or tipo_sitio."""
    from reg_txtss.models import RegTxtss
    qs = RegTxtss.objects.all()
    if sitio_id:
        qs = qs.filter(sitio_id=sitio_id)
    if tipo_sitio:
        qs = qs.filter(sitio__tipo_sitio=tipo_sitio)
    return list(qs.values_list('id', flat=True))


def _build_photos_q_from_reg_ids(reg_ids):
    """Return a Q() covering all Photos linked to the given RegTxtss IDs."""
    from reg_txtss.models import RegTxtss

    if not reg_ids:
        return Q(pk__in=[])

    q = Q()
    ct_reg = ContentType.objects.get_for_model(RegTxtss)
    q |= Q(content_type=ct_reg, object_id__in=reg_ids)

    return q


class PhotoGalleryView(LoginRequiredMixin, BreadcrumbsMixin, ListView):
    model = Photos
    context_object_name = 'photos'
    template_name = 'photos/gallery.html'
    paginate_by = 60

    def get_queryset(self):
        from core.models import Site
        from reg_txtss.models import RegTxtss
        from django.db.models import Subquery, OuterRef
        qs = Photos.objects.select_related('content_type')
        tipo = self.request.GET.get('tipo', '')
        sitio_id = self.request.GET.get('sitio', '')
        etapa = self.request.GET.get('etapa', '')
        size_min = self.request.GET.get('size_min', '')
        size_max = self.request.GET.get('size_max', '')

        qs = qs.annotate(
            sitio_pti_cell_id=Subquery(
                RegTxtss.objects.filter(pk=OuterRef('object_id')).values('sitio__pti_cell_id')[:1]
            ),
            reg_alternativa=Subquery(
                RegTxtss.objects.filter(pk=OuterRef('object_id')).values('alternativa')[:1]
            ),
        )

        # Site and/or tipo filter (combined into one Q query)
        if sitio_id or tipo in ('POSTE', 'TORRE'):
            reg_ids = _get_reg_ids_for_sitio_filter(
                sitio_id=sitio_id if sitio_id else None,
                tipo_sitio=tipo if tipo in ('POSTE', 'TORRE') else None,
            )
            qs = qs.filter(_build_photos_q_from_reg_ids(reg_ids))

        if etapa:
            qs = qs.filter(etapa=etapa)

        try:
            if size_min:
                qs = qs.filter(file_size__gte=int(float(size_min) * 1024))
        except (ValueError, TypeError):
            pass
        try:
            if size_max:
                qs = qs.filter(file_size__lte=int(float(size_max) * 1024))
        except (ValueError, TypeError):
            pass

        return qs.order_by('-created_at')

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['photos/partials/gallery_grid.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        from core.models import Site
        context = super().get_context_data(**kwargs)
        context['tipo_filter'] = self.request.GET.get('tipo', '')
        context['sitio_filter'] = self.request.GET.get('sitio', '')
        context['etapa_filter'] = self.request.GET.get('etapa', '')
        context['size_min'] = self.request.GET.get('size_min', '')
        context['size_max'] = self.request.GET.get('size_max', '')
        context['total_count'] = self.get_queryset().count()
        context['etapas'] = (
            Photos.objects.values_list('etapa', flat=True)
            .distinct().order_by('etapa')
        )
        # Only sites that actually have at least one photo (trace Photos → RegTxtss → site)
        from reg_txtss.models import RegTxtss
        ct_reg = ContentType.objects.get_for_model(RegTxtss)
        reg_ids_with_photos = set(
            Photos.objects.filter(content_type=ct_reg).values_list('object_id', flat=True)
        )
        site_ids_with_photos = (
            RegTxtss.objects.filter(pk__in=reg_ids_with_photos)
            .values_list('sitio_id', flat=True).distinct()
        )
        context['sites'] = Site.objects.filter(pk__in=site_ids_with_photos).order_by('pti_cell_id')

        # Backfill lazy: genera thumbnails de la página actual que aún no los tienen
        for photo in context.get('photos', []):
            if not photo.thumbnail:
                photo.generate_thumbnail()

        return context

    def get_breadcrumbs(self):
        return self._resolve_breadcrumbs([
            {'label': 'Inicio', 'url_name': 'dashboard:dashboard'},
            {'label': 'Imágenes'},
        ])


class BulkDeletePhotosView(LoginRequiredMixin, SuperuserRequiredMixin, View):

    def post(self, request):
        data = json.loads(request.body)
        ids = [int(i) for i in data.get('ids', []) if str(i).isdigit()]
        if not ids:
            return JsonResponse({'success': False, 'message': 'No se seleccionaron fotos'}, status=400)

        photos = Photos.objects.filter(pk__in=ids)
        count = photos.count()

        for photo in photos:
            try:
                if photo.imagen and os.path.exists(photo.imagen.path):
                    os.remove(photo.imagen.path)
            except Exception:
                pass

        photos.delete()
        return JsonResponse({'success': True, 'message': f'{count} foto(s) eliminada(s)'})


class BulkDownloadPhotosView(LoginRequiredMixin, View):

    def post(self, request):
        import zipfile
        import io

        data = json.loads(request.body)
        ids = [int(i) for i in data.get('ids', []) if str(i).isdigit()]
        if not ids:
            return JsonResponse({'success': False, 'message': 'No se seleccionaron fotos'}, status=400)

        photos = list(Photos.objects.filter(pk__in=ids))

        buffer = io.BytesIO()
        seen_names = {}
        with zipfile.ZipFile(buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
            for photo in photos:
                try:
                    path = photo.imagen.path
                    if not os.path.exists(path):
                        continue
                    filename = os.path.basename(path)
                    if filename in seen_names:
                        seen_names[filename] += 1
                        name, ext = os.path.splitext(filename)
                        filename = f"{name}_{seen_names[filename]}{ext}"
                    else:
                        seen_names[filename] = 0
                    zf.write(path, filename)
                except Exception:
                    pass

        buffer.seek(0)
        response = StreamingHttpResponse(
            iter([buffer.read()]),
            content_type='application/zip'
        )
        response['Content-Disposition'] = 'attachment; filename="fotos.zip"'
        return response


class CompressPhotosView(LoginRequiredMixin, SuperuserRequiredMixin, View):

    def post(self, request):
        from PIL import Image

        data = json.loads(request.body)
        ids = [int(i) for i in data.get('ids', []) if str(i).isdigit()]
        quality = int(data.get('quality', 70))
        quality = max(10, min(quality, 95))

        if not ids:
            return JsonResponse({'success': False, 'message': 'No se seleccionaron fotos'}, status=400)

        photos = Photos.objects.filter(pk__in=ids)
        compressed = 0
        saved_bytes = 0

        for photo in photos:
            try:
                path = photo.imagen.path
                if not path.lower().endswith(('.jpg', '.jpeg')):
                    continue
                original_size = os.path.getsize(path)
                with Image.open(path) as img:
                    exif_data = img.info.get('exif', b'')
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    img.save(path, quality=quality, optimize=True, exif=exif_data)
                new_size = os.path.getsize(path)
                saved_bytes += max(0, original_size - new_size)
                Photos.objects.filter(pk=photo.pk).update(file_size=new_size)
                compressed += 1
            except Exception:
                pass

        saved_kb = saved_bytes // 1024
        return JsonResponse({
            'success': True,
            'message': f'{compressed} foto(s) comprimida(s). Ahorro: {saved_kb} KB',
            'saved_bytes': saved_bytes,
        })

