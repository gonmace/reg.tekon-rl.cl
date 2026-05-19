from django.db import models


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
