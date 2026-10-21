"""
Reordena los pasos de Construcción Torres:

- «Actividades inspeccionadas» pasa a «Actividades» y gana cámara (las fotos del antiguo
  paso general «Registro fotográfico» se mueven aquí).
- Nuevo paso «Eléctrico»: un comentario + cámara.
- «Comentarios generales» pasa a «Comentarios y acciones»: áreas de texto sin numerar.

Las claves internas (obra_objetivos, obra_comentarios) no cambian: ahí están los datos guardados.
"""
from django.db import migrations

NAMESPACE = 'reg_construccion_torres'
PASO_ACT, PASO_ELEC, PASO_COM, PASO_FOTOS = 'obra_objetivos', 'obra_electrico', 'obra_comentarios', 'obra_fotos'

CAMARA = {'foto_min': 1}
COM_NUEVO = {'label': 'Comentarios y acciones', 'placeholder': 'Comentario o acción de la visita',
             'max_items': 50, 'multilinea': True, 'numerada': False}
COM_ANTIGUO = {'label': 'Comentarios generales', 'placeholder': 'Observación de la visita', 'max_items': 50}


def _modelos(apps):
    return (apps.get_model('actividades', 'TipoActividad'), apps.get_model('actividades', 'PasoDefinicion'),
            apps.get_model('actividades', 'PasoWidget'), apps.get_model('actividades', 'ConfigPaso'))


def _mover_fotos(apps, de, a):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Photos = apps.get_model('photos', 'Photos')
    ct = ContentType.objects.filter(app_label='reg_construccion', model='regconstruccion').first()
    if ct:
        Photos.objects.filter(content_type=ct, etapa=de).update(etapa=a)


def _renombrar(apps, act, com, com_config):
    _, PasoDefinicion, PasoWidget, _ = _modelos(apps)
    PasoDefinicion.objects.filter(nombre=PASO_ACT).update(titulo=act)
    PasoDefinicion.objects.filter(nombre=PASO_COM).update(titulo=com)
    pw = PasoWidget.objects.filter(pasodef__nombre=PASO_COM, widget_slug='lista_widget').first()
    if pw:
        pw.config = com_config
        pw.save(update_fields=['config'])


def adelante(apps, schema_editor):
    TipoActividad, PasoDefinicion, PasoWidget, ConfigPaso = _modelos(apps)
    tipo = TipoActividad.objects.filter(app_namespace=NAMESPACE).first()
    if not tipo:
        return
    _renombrar(apps, 'Actividades', 'Comentarios y acciones', COM_NUEVO)

    act = PasoDefinicion.objects.get(nombre=PASO_ACT)
    PasoWidget.objects.get_or_create(pasodef=act, widget_slug='camera_widget',
                                     defaults={'orden': 2, 'config': CAMARA})

    elec, _ = PasoDefinicion.objects.get_or_create(nombre=PASO_ELEC, defaults={'titulo': 'Eléctrico'})
    PasoWidget.objects.get_or_create(pasodef=elec, widget_slug='comentario_widget',
                                     defaults={'orden': 1, 'config': {'label': 'Eléctrico', 'name': 'comentario'}})
    PasoWidget.objects.get_or_create(pasodef=elec, widget_slug='camera_widget',
                                     defaults={'orden': 2, 'config': CAMARA})
    ConfigPaso.objects.update_or_create(tipo=tipo, pasodef=elec, defaults={'orden': 3})
    ConfigPaso.objects.filter(tipo=tipo, pasodef__nombre=PASO_COM).update(orden=4)

    _mover_fotos(apps, PASO_FOTOS, PASO_ACT)
    ConfigPaso.objects.filter(tipo=tipo, pasodef__nombre=PASO_FOTOS).delete()
    PasoDefinicion.objects.filter(nombre=PASO_FOTOS, asignaciones__isnull=True).delete()


def atras(apps, schema_editor):
    TipoActividad, PasoDefinicion, PasoWidget, ConfigPaso = _modelos(apps)
    tipo = TipoActividad.objects.filter(app_namespace=NAMESPACE).first()
    if not tipo:
        return
    _renombrar(apps, 'Actividades inspeccionadas', 'Comentarios generales', COM_ANTIGUO)
    PasoWidget.objects.filter(pasodef__nombre=PASO_ACT, widget_slug='camera_widget').delete()

    fotos, _ = PasoDefinicion.objects.get_or_create(nombre=PASO_FOTOS, defaults={'titulo': 'Registro fotográfico'})
    PasoWidget.objects.get_or_create(pasodef=fotos, widget_slug='camera_widget',
                                     defaults={'orden': 1, 'config': CAMARA})
    ConfigPaso.objects.update_or_create(tipo=tipo, pasodef=fotos, defaults={'orden': 4})
    ConfigPaso.objects.filter(tipo=tipo, pasodef__nombre=PASO_COM).update(orden=3)
    # Las fotos de Actividades vuelven al paso general; las de Eléctrico quedan huérfanas con su paso.
    _mover_fotos(apps, PASO_ACT, PASO_FOTOS)
    ConfigPaso.objects.filter(tipo=tipo, pasodef__nombre=PASO_ELEC).delete()
    PasoDefinicion.objects.filter(nombre=PASO_ELEC, asignaciones__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('reg_construccion', '0007_remove_historicalregconstruccion_altura_and_more'),
        ('actividades', '0022_contexto_registro'),
        ('photos', '__first__'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]
    operations = [migrations.RunPython(adelante, atras)]
