"""
Datos del dashboard de inicio (solo Construcción Sitios).

Todo respeta el alcance por rol (`core.permissions.alcance_registros`) y se cachea unos
minutos por alcance (todo / contratista / usuario). Ver CLAUDE.md, sección «Dashboard».
"""
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count, Min, OuterRef, Subquery
from django.urls import reverse
from django.utils import timezone

from core.models.sites import Site
from core.permissions import alcance_registros

from .models import ESTADO_OBRA_CHOICES, RegConstruccion

CACHE_TTL = 120  # segundos
DIAS_SIN_VISITA = 14  # una torre en obra sin visita hace más días que esto requiere atención

ESTADOS = dict(ESTADO_OBRA_CHOICES)
# Clases completas (Tailwind las detecta al escanear este archivo).
ESTADO_BARRA = {
    'construccion': 'bg-info',
    'paralizado': 'bg-warning',
    'cancelado': 'bg-neutral/40',
    'concluido': 'bg-success',
}
ESTADO_BADGE = {
    'construccion': 'badge-info',
    'paralizado': 'badge-warning',
    'cancelado': 'badge-neutral',
    'concluido': 'badge-success',
}


# ── Alcance y caché ──────────────────────────────────────────────────────────

def visitas_del_alcance(user):
    """Visitas (no eliminadas) que `user` puede ver."""
    return alcance_registros(RegConstruccion.objects.filter(is_deleted=False), user)


def _cache_key(prefix, user):
    if user is None or user.is_supermanager or user.is_visita or user.is_admin_global:
        scope = 'all'
    elif user.is_admin_empresa:
        scope = f'c{user.contractor_id}'
    else:
        scope = f'u{user.id}'
    return f'dashboard:construccion:{prefix}:{scope}'


def cached(prefix, user, compute, ttl=None):
    """Cachea el resultado por alcance; si el caché falla, calcula directo."""
    try:
        return cache.get_or_set(_cache_key(prefix, user), compute, ttl or CACHE_TTL)
    except Exception:
        return compute()


# ── Sitios con el resumen de su última visita ────────────────────────────────

def sitios_con_ultima_visita(user):
    """Sitios con visitas visibles, anotados con el resumen de su última visita (una sola consulta)."""
    visitas = visitas_del_alcance(user)
    por_sitio = visitas.filter(sitio=OuterRef('pk'))
    ultima = por_sitio.order_by('-fecha', '-id')

    def ultima_de(campo):
        return Subquery(ultima.values(campo)[:1])

    # «Con datos» de la última visita (mismo criterio que with_estado): verde concluida,
    # amarillo con datos sin concluir, rojo sin ningún dato.
    ultima_estado = visitas.with_estado().filter(sitio=OuterRef('pk')).order_by('-fecha', '-id')

    return Site.objects.filter(pk__in=visitas.values('sitio_id')).annotate(
        n_visitas=Subquery(por_sitio.order_by().values('sitio').annotate(c=Count('id')).values('c')),
        primera_fecha=Subquery(por_sitio.order_by().values('sitio').annotate(m=Min('fecha')).values('m')),
        ultimo_id=ultima_de('id'),
        ultima_fecha=ultima_de('fecha'),
        ultimo_avance=ultima_de('avance_pct'),
        ultimo_concluido=ultima_de('concluido'),
        ultimo_completo=ultima_de('completo'),
        ultimo_estado_obra=ultima_de('estado_obra'),
        ultimo_con_datos=Subquery(ultima_estado.values('has_widgets')[:1]),
        ultimo_contratista=ultima_de('contratista__code'),  # en la tabla de sitios solo se muestra el código
        ultimo_contratista_id=ultima_de('contratista_id'),
        ultimo_contratista_nombre=ultima_de('contratista__name'),
    )


def _url_sitio(sitio_id):
    return f"{reverse('reg_construccion:list')}?sitio={sitio_id}"


def _promedio(valores):
    return round(sum(valores) / len(valores), 1) if valores else 0


# ── Panel principal (KPIs, estados, contratistas, torres a seguir) ───────────

def _calcular_panel(user):
    hoy = timezone.localdate()
    hace30, hace60 = hoy - timedelta(days=30), hoy - timedelta(days=60)
    umbral = hoy - timedelta(days=DIAS_SIN_VISITA)

    filas = list(sitios_con_ultima_visita(user).values(
        'id', 'pti_cell_id', 'name', 'n_visitas', 'primera_fecha', 'ultima_fecha', 'ultimo_avance',
        'ultimo_estado_obra', 'ultimo_contratista_id', 'ultimo_contratista', 'ultimo_contratista_nombre'))
    for f in filas:
        f['avance'] = float(f['ultimo_avance'] or 0)
        f['url'] = _url_sitio(f['id'])

    visitas = visitas_del_alcance(user)
    visitas_30 = visitas.filter(fecha__gt=hace30).count()
    visitas_prev = visitas.filter(fecha__gt=hace60, fecha__lte=hace30).count()
    visitas_30_por_contratista = dict(
        visitas.filter(fecha__gt=hace30).order_by().values_list('contratista_id').annotate(c=Count('id')))

    # Estados de la última visita de cada torre
    total = len(filas)
    estados = []
    for codigo, label in ESTADO_OBRA_CHOICES:
        n = sum(1 for f in filas if f['ultimo_estado_obra'] == codigo)
        estados.append({'codigo': codigo, 'label': label, 'n': n,
                        'pct': round(n * 100 / total, 1) if total else 0,
                        'barra': ESTADO_BARRA[codigo], 'badge': ESTADO_BADGE[codigo]})

    # Torres por rango de avance de su última visita
    rangos = []
    for label, desde, hasta in (('0–25 %', 0, 25), ('25–50 %', 25, 50), ('50–75 %', 50, 75), ('75–100 %', 75, 101)):
        n = sum(1 for f in filas if desde <= f['avance'] < hasta)
        rangos.append({'label': label, 'n': n, 'pct': round(n * 100 / total) if total else 0})

    en_obra = [f for f in filas if f['ultimo_estado_obra'] == 'construccion']
    sin_visita = sorted((f for f in en_obra if f['ultima_fecha'] and f['ultima_fecha'] < umbral),
                        key=lambda f: f['ultima_fecha'])
    for f in sin_visita:
        f['dias_sin_visita'] = (hoy - f['ultima_fecha']).days
    menor_avance = sorted(en_obra, key=lambda f: f['avance'])
    for f in menor_avance:
        f['dias_en_obra'] = (hoy - f['primera_fecha']).days if f['primera_fecha'] else None

    sin_concluir = visitas.filter(concluido=False).count()

    # Por contratista de la última visita
    grupos = {}
    for f in filas:
        g = grupos.setdefault(f['ultimo_contratista_id'], {
            'id': f['ultimo_contratista_id'],
            'nombre': f['ultimo_contratista_nombre'] or 'Sin contratista',
            'codigo': f['ultimo_contratista'] or '',
            'torres': 0, 'en_obra': 0, 'concluidas': 0, 'avances': [],
        })
        g['torres'] += 1
        g['en_obra'] += f['ultimo_estado_obra'] == 'construccion'
        g['concluidas'] += f['ultimo_estado_obra'] == 'concluido'
        g['avances'].append(f['avance'])
    contratistas = []
    for g in grupos.values():
        g['avance'] = _promedio(g.pop('avances'))
        g['visitas_30'] = visitas_30_por_contratista.get(g['id'], 0)
        contratistas.append(g)
    contratistas.sort(key=lambda g: (-g['torres'], g['nombre']))

    return {
        'kpis': {
            'torres': total,
            'en_obra': len(en_obra),
            'concluidas': sum(1 for f in filas if f['ultimo_estado_obra'] == 'concluido'),
            'avance_en_obra': _promedio([f['avance'] for f in en_obra]),
            'avance_global': _promedio([f['avance'] for f in filas]),
            'visitas_30': visitas_30,
            'visitas_prev': visitas_prev,
            'delta_visitas': round((visitas_30 - visitas_prev) * 100 / visitas_prev) if visitas_prev else None,
            'total_visitas': visitas.count(),
            'sin_visita': len(sin_visita),
            'sin_concluir': sin_concluir,
            'atencion': len(sin_visita) + sin_concluir,
        },
        'estados': estados,
        'rangos': rangos,
        'contratistas': contratistas,
        'menor_avance': menor_avance[:6],
        'sin_visita_reciente': sin_visita[:6],
    }


def panel(user):
    return cached('panel', user, lambda: _calcular_panel(user))


# ── Actividad reciente y pendientes ──────────────────────────────────────────

def _items(qs, limit):
    items = []
    for r in qs.select_related('sitio', 'user', 'contratista')[:limit]:
        nombre = (r.user.get_full_name.strip() or r.user.username) if r.user else '—'
        items.append({
            'sitio': r.sitio.name if r.sitio else '—',
            'pti': r.sitio.pti_cell_id if r.sitio else '',
            'usuario': nombre,
            'contratista': r.contratista.code if r.contratista else '',
            'fecha': r.fecha, 'actualizado': r.updated_at,
            'avance': float(r.avance_pct or 0),
            'estado': 'concluido' if r.concluido else ('en_proceso' if r.has_widgets else 'vacio'),
            'url': reverse('reg_construccion:steps', kwargs={'registro_id': r.id}),
        })
    return items


def actividad_reciente(user, limit=8):
    """Últimas visitas modificadas dentro del alcance del usuario."""
    return _items(visitas_del_alcance(user).with_estado().order_by('-updated_at'), limit)


def pendientes(user, limit=6):
    """Visitas sin concluir, las más antiguas primero."""
    return _items(visitas_del_alcance(user).filter(concluido=False).with_estado().order_by('fecha'), limit)


# ── Mapa ─────────────────────────────────────────────────────────────────────

def mapa_geojson(user):
    """FeatureCollection de torres con obra (coordenadas: construcción → ingeniería → mandato)."""
    filas = sitios_con_ultima_visita(user).values(
        'id', 'pti_cell_id', 'name', 'ultima_fecha', 'ultimo_avance', 'ultimo_estado_obra',
        'ultimo_contratista_nombre', 'lat_con', 'lon_con', 'lat_ing', 'lon_ing', 'lat_man', 'lon_man')
    features = []
    for f in filas:
        coords = next(((f[la], f[lo]) for la, lo in (('lat_con', 'lon_con'), ('lat_ing', 'lon_ing'),
                                                     ('lat_man', 'lon_man'))
                       if f[la] is not None and f[lo] is not None), None)
        if coords is None:
            continue
        estado = f['ultimo_estado_obra'] or 'construccion'
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [float(coords[1]), float(coords[0])]},
            'properties': {
                'nombre': f['name'], 'pti': f['pti_cell_id'],
                'avance': float(f['ultimo_avance'] or 0),
                'estado': estado, 'estado_label': ESTADOS.get(estado, estado),
                'ultima_fecha': f['ultima_fecha'].strftime('%d/%m/%Y') if f['ultima_fecha'] else '',
                'contratista': f['ultimo_contratista_nombre'] or '',
                'url': _url_sitio(f['id']),
            },
        })
    return {'type': 'FeatureCollection', 'features': features}
