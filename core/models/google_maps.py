"""
Modelo para almacenar imágenes de Google Maps generadas.
"""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from core.models.core_models import BaseModel
import os
import json


class GoogleMapsImage(BaseModel):
    """
    Modelo para almacenar imágenes de Google Maps generadas.
    """
    # Relación genérica con cualquier modelo de registro
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    registro = GenericForeignKey('content_type', 'object_id')
    
    # Información del mapa
    etapa = models.CharField(max_length=100, verbose_name='Etapa del registro')
    zoom = models.IntegerField(verbose_name='Nivel de zoom')
    maptype = models.CharField(max_length=50, verbose_name='Tipo de mapa', default='hybrid')
    scale = models.IntegerField(verbose_name='Escala', default=2)
    tamano = models.CharField(max_length=20, verbose_name='Tamaño', default='1200x600')
    
    # Archivo de imagen
    imagen = models.ImageField(
        upload_to='google_maps/',
        verbose_name='Imagen del mapa',
        help_text='Imagen estática generada por Google Maps API'
    )
    
    # Información de coordenadas (almacenada como JSON)
    coordenadas_json = models.TextField(
        verbose_name='Coordenadas JSON',
        help_text='Coordenadas utilizadas para generar el mapa'
    )
    
    # Información de distancia
    distancia_total_metros = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name='Distancia total (metros)'
    )
    desfase_metros = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name='Desfase (metros)'
    )
    
    # Metadatos
    was_created = models.BooleanField(
        default=True, 
        verbose_name='Fue creado',
        help_text='Indica si la imagen fue creada o ya existía'
    )
    
    class Meta:
        verbose_name = 'Imagen de Google Maps'
        verbose_name_plural = 'Imágenes de Google Maps'
        ordering = ['-created_at']
        unique_together = ['content_type', 'object_id', 'etapa']
    
    def __str__(self):
        return f"Mapa {self.etapa} - {self.registro} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"
    
    @property
    def coordenadas(self):
        """Devuelve las coordenadas como lista de diccionarios."""
        try:
            return json.loads(self.coordenadas_json)
        except (json.JSONDecodeError, TypeError):
            return []
    
    @coordenadas.setter
    def coordenadas(self, value):
        """Establece las coordenadas como JSON."""
        if isinstance(value, list):
            self.coordenadas_json = json.dumps(value, ensure_ascii=False)
        else:
            self.coordenadas_json = value
    
    @property
    def file_path(self):
        """Devuelve la ruta del archivo relativa."""
        if self.imagen:
            return self.imagen.name
        return None
    
    @property
    def file_url(self):
        """Devuelve la URL del archivo."""
        if self.imagen:
            return self.imagen.url
        return None
    
    @property
    def parameters(self):
        """Devuelve los parámetros utilizados para generar el mapa."""
        return {
            'zoom': self.zoom,
            'maptype': self.maptype,
            'scale': self.scale,
            'tamano': self.tamano,
            'coordenadas': self.coordenadas
        }
    
    def calcular_distancias(self):
        """Calcula las distancias entre puntos consecutivos."""
        coords = self.coordenadas
        if len(coords) < 2:
            return
        
        from core.utils.coordenadas import calcular_distancia_entre_puntos
        
        # Calcular distancia total entre puntos consecutivos
        distancia_total = 0
        for i in range(len(coords) - 1):
            coord1 = coords[i]
            coord2 = coords[i + 1]
            distancia = calcular_distancia_entre_puntos(
                coord1['lat'], coord1['lon'],
                coord2['lat'], coord2['lon']
            )
            distancia_total += distancia
        
        self.distancia_total_metros = distancia_total
        
        # Si solo hay 2 puntos, también calcular el desfase
        if len(coords) == 2:
            self.desfase_metros = distancia_total
        
        self.save()
    
    def save(self, *args, **kwargs):
        """Sobrescribir save para calcular distancias automáticamente."""
        # Red de seguridad: si la imagen cambia (ej. desde admin), borrar archivo anterior.
        # En el flujo normal de la vista, el archivo ya fue borrado antes de llegar aquí.
        if self.pk and self.imagen:
            try:
                old_name = GoogleMapsImage.objects.filter(pk=self.pk).values_list('imagen', flat=True).first()
                if old_name and old_name != self.imagen.name:
                    self.imagen.storage.delete(old_name)
            except Exception:
                pass

        super().save(*args, **kwargs)

        # Calcular distancias si no están calculadas
        if self.distancia_total_metros is None:
            self.calcular_distancias()

    def delete(self, *args, **kwargs):
        """Borrar archivo de imagen al eliminar el registro."""
        if self.imagen:
            self.imagen.delete(save=False)
        super().delete(*args, **kwargs)

    @classmethod
    def get_or_create_for_registro(cls, registro, etapa, **kwargs):
        """
        Obtiene o crea una imagen de Google Maps para un registro y etapa específicos.
        
        Args:
            registro: Instancia del modelo de registro
            etapa: Nombre de la etapa
            **kwargs: Parámetros adicionales para crear la imagen
        
        Returns:
            tuple: (GoogleMapsImage, created)
        """
        content_type = ContentType.objects.get_for_model(registro)
        
        # Intentar obtener imagen existente
        try:
            imagen = cls.objects.get(
                content_type=content_type,
                object_id=registro.id,
                etapa=etapa
            )
            imagen.was_created = False
            imagen.save()
            return imagen, False
        except cls.DoesNotExist:
            # Crear nueva imagen
            imagen = cls.objects.create(
                content_type=content_type,
                object_id=registro.id,
                etapa=etapa,
                was_created=True,
                **kwargs
            )
            return imagen, True 