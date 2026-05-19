from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models


class TipoActividad(models.Model):
    TIPO_SITIO_CHOICES = [
        ('POSTE', 'Poste'),
        ('TORRE', 'Torre'),
    ]

    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    app_namespace = models.SlugField(max_length=50, unique=True, verbose_name='Namespace URL')
    tipo_sitio = models.CharField(
        max_length=10, choices=TIPO_SITIO_CHOICES,
        verbose_name='Tipo de sitio',
        help_text='Debe coincidir con el tipo_sitio del sitio (POSTE o TORRE).'
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Tipo de Actividad'
        verbose_name_plural = 'Tipos de Actividad'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class PasoDefinicion(models.Model):
    nombre = models.SlugField(max_length=50, verbose_name='Nombre (slug)')
    titulo = models.CharField(max_length=100, verbose_name='Título')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')

    class Meta:
        verbose_name = 'Paso'
        verbose_name_plural = 'Pasos'
        ordering = ['titulo']

    def __str__(self):
        return self.titulo


class PasoWidget(models.Model):
    pasodef = models.ForeignKey(
        PasoDefinicion, on_delete=models.CASCADE, related_name='paso_widgets',
        verbose_name='Paso',
    )
    widget_slug = models.CharField(max_length=100, verbose_name='Widget')
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden')
    config = models.JSONField(default=dict, verbose_name='Configuración')

    class Meta:
        verbose_name = 'Widget de paso'
        verbose_name_plural = 'Widgets de paso'
        unique_together = [('pasodef', 'widget_slug')]
        ordering = ['orden']

    def __str__(self):
        return f'{self.pasodef.titulo} → {self.widget_slug}'

    def clean(self):
        from widgets.registry import get_widget
        widget = get_widget(self.widget_slug)
        if widget:
            errors = widget.validate_config(self.config)
            if errors:
                raise ValidationError({'config': errors})


class ConfigPaso(models.Model):
    tipo = models.ForeignKey(TipoActividad, on_delete=models.CASCADE, related_name='config_pasos')
    pasodef = models.ForeignKey(PasoDefinicion, on_delete=models.PROTECT, related_name='asignaciones')
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden')

    class Meta:
        verbose_name = 'Paso asignado'
        verbose_name_plural = 'Pasos asignados'
        unique_together = [('tipo', 'pasodef')]
        ordering = ['orden']

    def __str__(self):
        return f'{self.tipo} → {self.pasodef.titulo} (orden {self.orden})'



class DatoPaso(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    registro = GenericForeignKey('content_type', 'object_id')
    paso_nombre = models.CharField(max_length=50, verbose_name='Nombre del paso')
    datos = models.JSONField(default=dict, verbose_name='Datos (JSON)')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dato de Paso'
        verbose_name_plural = 'Datos de Pasos'
        unique_together = [('content_type', 'object_id', 'paso_nombre')]

    def __str__(self):
        return f'DatoPaso {self.object_id}/{self.paso_nombre}'

    def get_widget_data(self, widget_slug: str) -> dict:
        return self.datos.get(widget_slug, {})

    def set_widget_data(self, widget_slug: str, data: dict):
        self.datos[widget_slug] = data
        self.save(update_fields=['datos', 'updated_at'])


class ContextoRegistro(models.Model):
    """
    JSON de contexto acumulado a nivel de registro.
    Se reconstruye cada vez que se guarda un widget o imagen.
    Sirve como fuente de parámetros para otros widgets y para estadísticas/PDF.
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    registro = GenericForeignKey('content_type', 'object_id')
    contexto = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('content_type', 'object_id')]
        verbose_name = 'Contexto de Registro'
        verbose_name_plural = 'Contextos de Registro'

    def __str__(self):
        return f'Contexto {self.content_type.model}/{self.object_id}'
