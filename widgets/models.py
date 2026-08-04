from django.db import models


class ImagenEjemplo(models.Model):
    """Imagen de referencia reutilizable, asociada a un widget vía slug en su config."""
    slug = models.SlugField(unique=True)
    nombre = models.CharField(max_length=128)
    imagen = models.ImageField(upload_to='widgets/ejemplos/')
    descripcion = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Imagen de ejemplo'
        verbose_name_plural = 'Imágenes de ejemplo'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class DevPhoto(models.Model):
    """Fotos de prueba para el catálogo de widgets. Solo para desarrollo."""
    imagen = models.ImageField(upload_to='dev/photos/')
    descripcion = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Foto dev'
        verbose_name_plural = 'Fotos dev'
        ordering = ['id']

    def url(self):
        return self.imagen.url
