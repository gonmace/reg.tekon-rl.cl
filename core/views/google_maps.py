"""
Vistas para la API de Google Maps.
"""

import json
import os
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from core.models.google_maps import GoogleMapsImage
from core.utils.coordenadas import obtener_imagen_google_maps
from reg_txtss.models import RegTxtss
import logging

logger = logging.getLogger(__name__)


class GoogleMapsAPIView(LoginRequiredMixin, View):
    """
    Vista para generar imágenes de Google Maps.
    
    Endpoint: POST /api/v1/google-maps/
    """
    
    def post(self, request, *args, **kwargs):
        """
        Genera una imagen de Google Maps con las coordenadas proporcionadas.
        
        Request JSON:
        {
            "registro_id": 123,
            "etapa": "sitio",
            "coordenada_1": {
                "lat": -33.4567,
                "lon": -70.6483,
                "label": "M",
                "color": "#3B82F6",
                "size": "large"
            },
            "coordenada_2": {
                "lat": -33.4568,
                "lon": -70.6484,
                "label": "I",
                "color": "#EF4444",
                "size": "mid"
            },
            "zoom": 15,
            "maptype": "hybrid",
            "scale": 2,
            "tamano": "640x640"
        }
        
        Response JSON:
        {
            "success": true,
            "message": "Imagen guardada exitosamente",
            "mapa_id": 456,
            "file_path": "google_maps/PTI001_OPERADOR_empalme.png",
            "file_url": "/media/google_maps/PTI001_OPERADOR_empalme.png",
            "distancia_total_metros": 150.25,
            "was_created": true,
            "parameters": {
                "zoom": 15,
                "maptype": "hybrid",
                "scale": 2,
                "tamano": "640x640",
                "coordenadas": [...]
            }
        }
        """
        try:
            # Parsear datos JSON
            data = json.loads(request.body)
            
            # Validar datos requeridos
            registro_id = data.get('registro_id')
            etapa = data.get('etapa')
            
            if not registro_id or not etapa:
                return JsonResponse({
                    'success': False,
                    'error': 'registro_id y etapa son requeridos'
                }, status=400)
            
            # Obtener el registro
            try:
                registro = RegTxtss.objects.get(id=registro_id)
            except RegTxtss.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Registro con ID {registro_id} no encontrado'
                }, status=404)
            
            # Extraer coordenadas del request
            coordenadas = []
            for i in range(1, 10):  # Soporte para hasta 9 coordenadas
                coord_key = f'coordenada_{i}'
                if coord_key in data:
                    coord_data = data[coord_key]
                    coordenadas.append({
                        'lat': float(coord_data['lat']),
                        'lon': float(coord_data['lon']),
                        'label': coord_data.get('label', f'Punto {i}'),
                        'color': coord_data.get('color', '#3B82F6'),
                        'size': coord_data.get('size', 'normal')
                    })
            
            if not coordenadas:
                return JsonResponse({
                    'success': False,
                    'error': 'Al menos una coordenada es requerida'
                }, status=400)
            
            # Parámetros del mapa
            zoom = data.get('zoom', 15)
            maptype = data.get('maptype', 'hybrid')
            scale = data.get('scale', 2)
            tamano = data.get('tamano', '640x640')
            
            # Generar imagen usando Google Maps API
            imagen_bytes = obtener_imagen_google_maps(
                coordenadas=coordenadas,
                zoom=zoom,
                maptype=maptype,
                scale=scale,
                tamano=tamano
            )
            
            if not imagen_bytes:
                return JsonResponse({
                    'success': False,
                    'error': 'Error al generar la imagen con Google Maps API'
                }, status=500)
            
            # Generar nombre de archivo único
            sitio_codigo = getattr(registro.sitio, 'pti_cell_id', 'SIN_CODIGO')
            operador = getattr(registro.sitio, 'operator_id', 'SIN_OPERADOR')
            filename = f"{sitio_codigo}_{operador}_{etapa}.png"
            
            # Crear o actualizar el modelo GoogleMapsImage
            mapa_imagen, was_created = GoogleMapsImage.get_or_create_for_registro(
                registro=registro,
                etapa=etapa,
                zoom=zoom,
                maptype=maptype,
                scale=scale,
                tamano=tamano,
                coordenadas=coordenadas
            )
            
            # Guardar la imagen
            mapa_imagen.imagen.save(
                filename,
                ContentFile(imagen_bytes),
                save=True
            )
            
            # Preparar respuesta
            response_data = {
                'success': True,
                'message': 'Imagen guardada exitosamente',
                'mapa_id': mapa_imagen.id,
                'file_path': mapa_imagen.file_path,
                'file_url': mapa_imagen.file_url,
                'was_created': was_created,
                'parameters': mapa_imagen.parameters
            }
            
            # Agregar información de distancia si está disponible
            if mapa_imagen.distancia_total_metros is not None:
                response_data['distancia_total_metros'] = mapa_imagen.distancia_total_metros
            
            if mapa_imagen.desfase_metros is not None:
                response_data['desfase_metros'] = mapa_imagen.desfase_metros
            
            logger.info(f"Imagen de Google Maps generada exitosamente: {filename}")
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'JSON inválido en el request'
            }, status=400)
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': f'Error en los datos: {str(e)}'
            }, status=400)
            
        except Exception as e:
            logger.error(f"Error al generar imagen de Google Maps: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Error interno del servidor: {str(e)}'
            }, status=500) 