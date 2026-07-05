import os
from io import BytesIO
from django.db import models
from django.conf import settings
from core.models import BaseModel
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Photos(BaseModel):
    # Referencia genérica al modelo de Registro (puede ser de cualquier app)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    registro = GenericForeignKey('content_type', 'object_id')

    # Campo para identificar la aplicación
    app = models.CharField(max_length=100, verbose_name='Aplicación')
    etapa = models.CharField(max_length=255)
    imagen = models.ImageField(upload_to='photos/')
    thumbnail = models.ImageField(upload_to='photos/thumbs/', null=True, blank=True, verbose_name='Miniatura')
    descripcion = models.CharField(max_length=128, blank=True, null=True)
    orden = models.IntegerField(default=0)

    # Metadata EXIF extraída automáticamente al guardar
    exif_lat = models.FloatField(null=True, blank=True, verbose_name='Latitud EXIF')
    exif_lon = models.FloatField(null=True, blank=True, verbose_name='Longitud EXIF')
    exif_datetime = models.DateTimeField(null=True, blank=True, verbose_name='Fecha/hora EXIF')

    file_size = models.PositiveIntegerField(null=True, blank=True, verbose_name='Tamaño (bytes)')

    @property
    def thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        return self.imagen.url if self.imagen else ''

    def generate_thumbnail(self, size=(400, 400), img=None):
        """Genera la miniatura JPEG. Si se pasa `img` (una imagen PIL ya abierta)
        la reutiliza en vez de reabrir el archivo. Devuelve la ruta relativa o None.
        Cuando se invoca de forma aislada (backfill) persiste el campo en la BD."""
        if not self.imagen:
            return None
        try:
            from PIL import Image, ImageOps
            orig_path = self.imagen.path
            thumb_dir = os.path.join(os.path.dirname(orig_path), 'thumbs')
            os.makedirs(thumb_dir, exist_ok=True)
            thumb_filename = os.path.splitext(os.path.basename(orig_path))[0] + '.jpg'
            thumb_abs = os.path.join(thumb_dir, thumb_filename)

            owns = img is None
            source = Image.open(orig_path) if owns else img
            try:
                thumb = ImageOps.exif_transpose(source)  # corrige rotación EXIF
                thumb.thumbnail(size, Image.LANCZOS)
                buf = BytesIO()
                thumb.convert('RGB').save(buf, format='JPEG', quality=82, optimize=True)
            finally:
                if owns:
                    source.close()

            with open(thumb_abs, 'wb') as f:
                f.write(buf.getvalue())

            relative = os.path.relpath(thumb_abs, settings.MEDIA_ROOT)
            self.thumbnail = relative
            if owns:
                Photos.objects.filter(pk=self.pk).update(thumbnail=relative)
            return relative
        except Exception:
            return None

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and self.imagen:
            self._process_new_image()

    def _process_new_image(self):
        """Procesa una foto recién subida abriendo la imagen UNA sola vez:
        tamaño de archivo + EXIF + miniatura, consolidados en un único UPDATE
        (antes eran 2 aperturas Pillow y 3 UPDATE separados)."""
        updates = {}
        try:
            updates['file_size'] = os.path.getsize(self.imagen.path)
            self.file_size = updates['file_size']
        except Exception:
            pass

        try:
            from PIL import Image
            with Image.open(self.imagen.path) as img:
                if self.exif_lat is None and self.exif_datetime is None:
                    for field, value in self._read_exif(img).items():
                        setattr(self, field, value)
                        updates[field] = value
                thumb_rel = self.generate_thumbnail(img=img)
                if thumb_rel:
                    updates['thumbnail'] = thumb_rel
        except Exception:
            pass

        if updates:
            Photos.objects.filter(pk=self.pk).update(**updates)

    def _read_exif(self, img):
        """Lee GPS y fecha/hora del EXIF de una imagen PIL ya abierta. Devuelve
        un dict con los campos a actualizar (vacío si no hay EXIF útil)."""
        result = {}
        try:
            from PIL.ExifTags import TAGS, GPSTAGS
            import datetime

            exif_raw = img._getexif()
            if not exif_raw:
                return result

            exif = {TAGS.get(k, k): v for k, v in exif_raw.items()}

            # ── Fecha/hora ────────────────────────────────────────────────────
            for tag in ('DateTimeOriginal', 'DateTimeDigitized', 'DateTime'):
                dt_str = exif.get(tag)
                if dt_str:
                    try:
                        result['exif_datetime'] = datetime.datetime.strptime(
                            str(dt_str).strip(), '%Y:%m:%d %H:%M:%S'
                        )
                        break
                    except ValueError:
                        pass

            # ── GPS ───────────────────────────────────────────────────────────
            gps_raw = exif.get('GPSInfo')
            if gps_raw:
                gps = {GPSTAGS.get(k, k): v for k, v in gps_raw.items()}

                def _dms_to_decimal(dms, ref):
                    d, m, s = (float(x) for x in dms)
                    decimal = d + m / 60 + s / 3600
                    return -decimal if ref in ('S', 'W') else decimal

                lat_dms = gps.get('GPSLatitude')
                lat_ref = gps.get('GPSLatitudeRef')
                lon_dms = gps.get('GPSLongitude')
                lon_ref = gps.get('GPSLongitudeRef')

                if lat_dms and lat_ref and lon_dms and lon_ref:
                    result['exif_lat'] = _dms_to_decimal(lat_dms, lat_ref)
                    result['exif_lon'] = _dms_to_decimal(lon_dms, lon_ref)
        except Exception:
            pass  # EXIF opcional: nunca bloquear el guardado de la foto
        return result

    def __str__(self):
        return f"{self.registro} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'
        ordering = ['orden', '-created_at']
        indexes = [
            # Lookup dominante: fotos de un registro/etapa (galería, PDF, conteos).
            models.Index(fields=['content_type', 'object_id', 'etapa'],
                         name='photos_ct_obj_etapa_idx'),
        ]

    @staticmethod
    def count_photos(registro_id, etapa, app_name=None, content_type=None):
        """
        Cuenta las fotos para un registro específico, etapa y aplicación.
        
        Args:
            registro_id (int): ID del registro
            etapa (str): Nombre de la etapa
            app_name (str, optional): Nombre de la aplicación
            content_type (ContentType, optional): ContentType del modelo
            
        Returns:
            int: Cantidad de fotos encontradas
        """
        filters = {
            'object_id': registro_id,
            'etapa': etapa,
        }
        
        # Usar content_type si está disponible
        if content_type:
            filters['content_type'] = content_type
        
        # Usar app_name si está disponible (puede usarse junto con content_type)
        if app_name:
            filters['app'] = app_name
            
        return Photos.objects.filter(**filters).count()

    @staticmethod
    def get_photo_count_and_color(registro_id, etapa, app_name=None, content_type=None):
        """
        Obtiene la cantidad de imágenes para un registro específico y una etapa determinada.
        
        Args:
            registro_id (int): ID del registro
            etapa (str): Nombre de la etapa
            app_name (str, optional): Nombre de la aplicación
            content_type (ContentType, optional): ContentType del modelo
            
        Returns:
            int: Cantidad de imágenes encontradas
        """
        return Photos.count_photos(registro_id, etapa, app_name, content_type)


