"""
Tabla de ítems y avance de obra (Construcción Sitios).

Cada visita guarda en DatoPaso.datos:
    {"plantilla": "<nombre>", "partidas": [{"id", "nombre", "incidencia", "actual"}]}

Lo acumulado NO se guarda: se calcula recorriendo las visitas del sitio por fecha
(`calcular_serie`). Así, editar una visita antigua se propaga a las siguientes.
    anterior  = acumulada de la visita previa (por id de partida)
    acumulada = min(100, anterior + actual)
    total     = incidencia × acumulada / 100        total_general = Σ total
"""
import json
import uuid
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django import forms
from django.db.models import Q

from widgets.base import WidgetBase
from widgets.fields import JSONListField
from widgets.registry import register_widget

CIEN = Decimal('100')
CERO = Decimal('0')
DOS = Decimal('0.01')
UNO = Decimal('0.1')


def _dec(value, default=CERO):
    if value in (None, ''):
        return default
    try:
        return Decimal(str(value).replace(',', '.').strip())
    except (InvalidOperation, ValueError):
        return default


def _num(d):
    """Decimal → float con 2 decimales (apto JSON)."""
    return float(d.quantize(DOS, rounding=ROUND_HALF_UP))


def _porcentaje(value, campo):
    d = _dec(value)
    if d < 0 or d > 100:
        raise forms.ValidationError(f'{campo} debe estar entre 0 y 100.')
    return d


def normalizar_partidas(data):
    """Valida y normaliza una lista cruda de partidas (la envía el JS del widget)."""
    partidas = []
    vistos = set()
    for row in data:
        if not isinstance(row, dict):
            raise forms.ValidationError('Ítem inválido.')
        nombre = str(row.get('nombre', '')).strip()
        if not nombre:
            raise forms.ValidationError('Todos los ítems deben tener nombre.')
        if len(nombre) > 120:
            raise forms.ValidationError('Nombre de ítem demasiado largo (máx. 120).')
        pid = str(row.get('id') or '').strip() or uuid.uuid4().hex[:12]
        if pid in vistos:
            raise forms.ValidationError('Ítems con id repetido.')
        vistos.add(pid)
        partidas.append({
            'id': pid,
            'nombre': nombre,
            'incidencia': _num(_porcentaje(row.get('incidencia'), 'La incidencia')),
            'actual': _num(_porcentaje(row.get('actual'), 'El % de ejecución actual')),
        })
    return partidas


class PartidasField(JSONListField):
    def clean_items(self, data):
        return normalizar_partidas(data)


def calcular_serie(visitas):
    """
    visitas: lista (en orden cronológico) de listas de partidas guardadas por visita.
    Devuelve una lista paralela de {'filas': [...], 'total': Decimal}.
    Una visita sin partidas guardadas hereda la estructura de la anterior con actual = 0.
    """
    acumulado = {}
    estructura = []
    serie = []
    for partidas in visitas:
        if partidas:
            estructura = [{'id': p['id'], 'nombre': p['nombre'], 'incidencia': _dec(p.get('incidencia'))}
                          for p in partidas]
            actuales = {p['id']: _dec(p.get('actual')) for p in partidas}
        else:
            actuales = {}
        filas = []
        total = CERO
        for p in estructura:
            anterior = acumulado.get(p['id'], CERO)
            actual = actuales.get(p['id'], CERO)
            acumulada = min(CIEN, anterior + actual)
            fila_total = p['incidencia'] * acumulada / CIEN
            acumulado[p['id']] = acumulada
            total += fila_total
            filas.append({
                'id': p['id'], 'nombre': p['nombre'], 'incidencia': p['incidencia'],
                'anterior': anterior, 'actual': actual, 'acumulada': acumulada, 'total': fila_total,
            })
        serie.append({'filas': filas, 'total': total})
    return serie


def redondear(d, decimales=1):
    q = UNO if decimales == 1 else DOS
    return d.quantize(q, rounding=ROUND_HALF_UP)


def serializar(resultado):
    """Resultado de calcular_serie → estructura JSON-friendly (floats a 2 decimales)."""
    return {
        'filas': [{k: (v if k in ('id', 'nombre') else _num(v)) for k, v in f.items()}
                  for f in resultado['filas']],
        'total': _num(resultado['total']),
    }


def avance_sitio(model, sitio_id, paso_nombre, hasta=None):
    """
    Cálculo para todas las visitas de un sitio (orden cronológico).
    `hasta`: registro hasta el cual calcular (inclusive); None = todas.
    Devuelve [(registro_id, resultado)].
    """
    from django.contrib.contenttypes.models import ContentType
    from actividades.models import DatoPaso

    qs = model.objects.filter(sitio_id=sitio_id, is_deleted=False)
    if hasta is not None:
        qs = qs.filter(Q(fecha__lt=hasta.fecha) | Q(fecha=hasta.fecha, id__lte=hasta.id))
    ids = list(qs.order_by('fecha', 'id').values_list('id', flat=True))
    if hasta is not None and hasta.id not in ids:
        ids.append(hasta.id)
    ct = ContentType.objects.get_for_model(model)
    guardado = {
        d.object_id: (d.datos.get('partidas') or [])
        for d in DatoPaso.objects.filter(content_type=ct, object_id__in=ids, paso_nombre=paso_nombre)
    }
    return list(zip(ids, calcular_serie([guardado.get(i, []) for i in ids])))


def avance_registro(registro, paso_nombre):
    """Cálculo para `registro` considerando todas las visitas previas de su sitio."""
    return avance_sitio(type(registro), registro.sitio_id, paso_nombre, hasta=registro)[-1][1]


def _plantillas(config):
    raw = config.get('plantillas') or []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            raw = []
    return raw if isinstance(raw, list) else []


def puede_editar_estructura(user):
    """Plantilla, agregar y borrar ítems: solo superusuario y ADMINISTRADOR (el resto solo carga el % actual)."""
    return bool(user and (user.is_supermanager or user.is_administrador))


@register_widget
class TablaAvanceWidget(WidgetBase):
    slug = "tabla_avance_widget"
    nombre = "Tabla de avance"
    icon = "fa-solid fa-chart-gantt"

    def validate_config(self, config):
        errors = []
        for plantilla in _plantillas(config):
            nombre = plantilla.get('nombre', '?') if isinstance(plantilla, dict) else '?'
            partidas = plantilla.get('partidas') if isinstance(plantilla, dict) else None
            if not isinstance(partidas, list) or not partidas:
                errors.append(f"La plantilla '{nombre}' no tiene ítems")
                continue
            total = sum(_dec(p.get('incidencia')) for p in partidas if isinstance(p, dict))
            if total != CIEN:
                errors.append(f"La plantilla '{nombre}' suma {total}% de incidencia (debe sumar 100%)")
        return errors

    def validate_data(self, data):
        if not isinstance(data.get('partidas', []), list):
            return ["ítems debe ser una lista"]
        return []

    def completeness(self, data):
        return 3 if data.get('partidas') else 1

    def to_display(self, data, config):
        partidas = data.get('partidas') or []
        return {"label": "Avance", "filas": partidas, "is_empty": not partidas}

    def to_contexto(self, datos, config, registro, paso_nombre, ct=None):
        resultado = serializar(avance_registro(registro, paso_nombre))
        return {
            "raw": datos,
            "display": {"filas": resultado['filas'], "total": resultado['total']},
            "computed": {"total_general": resultado['total']},
            "level": self.completeness(datos),
        }

    def extra_context(self, context):
        registro = context.get('registro')
        paso = context.get('paso')
        request = context.get('request')
        if not (registro and paso):
            return {}
        resultado = serializar(avance_registro(registro, paso.nombre))
        widget = context.get('widget')
        config = getattr(widget, 'config', {}) or {}
        datos = context.get('datos') or {}
        return {
            'tabla_data': {
                'filas': resultado['filas'],
                'total': resultado['total'],
                'plantillas': _plantillas(config),
                'plantilla': datos.get('plantilla', ''),
                'puede_editar_estructura': puede_editar_estructura(getattr(request, 'user', None)),
            },
        }

    def before_save(self, cleaned, stored, request, registro, paso, config):
        if 'partidas' not in cleaned:
            return
        if puede_editar_estructura(request.user):
            return
        # Resto de roles (ITO, Buscador, Coordinación): solo cambian el % actual de partidas ya definidas.
        referencia = avance_registro(registro, paso.nombre)['filas']
        enviados = {p['id']: p for p in cleaned.get('partidas') or []}
        cleaned['partidas'] = [
            {
                'id': f['id'], 'nombre': f['nombre'], 'incidencia': _num(f['incidencia']),
                'actual': enviados.get(f['id'], {}).get('actual', 0.0),
            }
            for f in referencia
        ]
        cleaned['plantilla'] = stored.get('plantilla', '')
