"""
Mantiene dos campos denormalizados de `RegConstruccion`:
- `avance_pct` (avance total acumulado por visita), y
- `completo` (todos los pasos no opcionales completos: pinta la fila de verde).

El % acumulado de una visita depende de las anteriores del mismo sitio, así que al
guardar/borrar el paso de avance, o al crear/mover/borrar una visita, se recalcula
toda la serie del sitio. Se usa queryset.update() para no disparar señales ni historial.
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from actividades.models import DatoPaso
from photos.models import Photos

from .models import PASO_AVANCE, RegConstruccion

URL_NAMESPACE = 'reg_construccion'
TIPO_NAMESPACE = 'reg_construccion_torres'


def recalcular_avance_sitio(sitio_id):
    if not sitio_id:
        return
    from widgets.widget_types.tabla_avance import avance_sitio, redondear, CERO
    from decimal import Decimal
    for registro_id, resultado in avance_sitio(RegConstruccion, sitio_id, PASO_AVANCE):
        total = min(Decimal('100'), max(CERO, redondear(resultado['total'], 2)))
        RegConstruccion.objects.filter(pk=registro_id).update(avance_pct=total)


def _sitio_de_dato(dato):
    if dato.paso_nombre != PASO_AVANCE or dato.content_type.model != 'regconstruccion':
        return None
    return RegConstruccion.objects.filter(pk=dato.object_id).values_list('sitio_id', flat=True).first()


@receiver(post_save, sender=DatoPaso)
@receiver(post_delete, sender=DatoPaso)
def avance_por_dato(sender, instance, **kwargs):
    recalcular_avance_sitio(_sitio_de_dato(instance))


@receiver(post_save, sender=RegConstruccion)
@receiver(post_delete, sender=RegConstruccion)
def avance_por_visita(sender, instance, **kwargs):
    recalcular_avance_sitio(instance.sitio_id)


def calcular_completo(registro):
    """True si ningún widget obligatorio está incompleto. Opcionales vacíos (gris) no cuentan.

    Reutiliza los colores del timeline de pasos: verde = completo, opcional = gris (no exigido);
    rojo o amarillo = falta algo obligatorio.
    """
    from registros.views.dynamic_steps import get_dynamic_steps
    colores = []
    for _, step in get_dynamic_steps(registro, model=RegConstruccion, url_namespace=URL_NAMESPACE,
                                     tipo_namespace=TIPO_NAMESPACE):
        el = step['elements']
        colores += [w['color'] for w in el['form_widgets']]
        if el['photos'].get('enabled'):
            colores.append(el['photos']['color'])
        colores += [e['color'] for e in el['photos_extra']]
    return bool(colores) and all(c in ('paso-verde', 'paso-opcional') for c in colores)


def recalcular_completo(registro_id):
    registro = RegConstruccion.objects.filter(pk=registro_id).first()
    if registro:
        RegConstruccion.objects.filter(pk=registro_id).update(completo=calcular_completo(registro))


def _es_de_construccion(instance):
    return instance.content_type.model == 'regconstruccion'


@receiver(post_save, sender=DatoPaso)
@receiver(post_delete, sender=DatoPaso)
def completo_por_dato(sender, instance, **kwargs):
    if _es_de_construccion(instance):
        recalcular_completo(instance.object_id)


@receiver(post_save, sender=Photos)
@receiver(post_delete, sender=Photos)
def completo_por_foto(sender, instance, **kwargs):
    if _es_de_construccion(instance):
        recalcular_completo(instance.object_id)


@receiver(post_save, sender=RegConstruccion)
def completo_por_visita(sender, instance, created, **kwargs):
    if created:
        recalcular_completo(instance.pk)
