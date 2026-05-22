import os
import re
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.template.loader import get_template
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin
from core.permissions import superuser_required

WIDGETS_DIR = os.path.join(settings.BASE_DIR, 'widgets', 'templates', 'widgets')

# Valores de prueba pre-llenados para cada parámetro documentado
_TEST_VALUES = {
    'camera_widget':    {'upload_url': '/widgets/dev/photos/upload/', 'foto_min': '3'},
    'comentario_widget':{'rows': '4'},
    'distancia_widget': {'save_url': '', 'lat1': '-33.4569400', 'lon1': '-70.6482700', 'lat2': '-33.4610000', 'lon2': '-70.6550000'},
    'mapa_1p':          {'lat': '-33.4569400', 'lon': '-70.6482700', 'height': '300', 'color': '#3b82f6', 'label': 'M', 'save_url': '/widgets/dev/map/save/'},
    'mapa_2_puntos':    {'lat1': '-33.4569400', 'lon1': '-70.6482700', 'lat2': '-33.4610000', 'lon2': '-70.6550000', 'label1': 'P', 'color1': '#e74c3c', 'label2': 'M', 'color2': '#0054ff', 'save_url': '/widgets/dev/map/save/'},
    'ubicacion_widget': {},
}



def _parse_widget(filename):
    path = os.path.join(WIDGETS_DIR, filename)
    with open(path, encoding='utf-8') as f:
        source = f.read()

    slug = filename.replace('.html', '')
    is_page = bool(re.match(r'\s*\{%-?\s*extends\b', source))
    test_defaults = _TEST_VALUES.get(slug, {})

    comment_match = re.match(r'\s*\{%-?\s*comment\s*-?%\}(.*?)\{%-?\s*endcomment\s*-?%\}', source, re.DOTALL)
    params = []
    estados = []
    description = ''
    usage = ''
    if comment_match:
        block = comment_match.group(1)
        lines = block.splitlines()
        # Split block into named sections. First line is the filename, skip it.
        sections = {}
        current_section = '__desc__'
        sections[current_section] = []
        for line in lines[1:]:
            header = re.match(r'^\s{0,3}([A-ZÁÉÍÓÚ][^:\n]*):$', line.strip())
            if header:
                current_section = header.group(1).lower()
                sections.setdefault(current_section, [])
            else:
                sections[current_section].append(line)

        def _clean(lst):
            stripped = [l.strip() for l in lst]
            while stripped and not stripped[0]:
                stripped.pop(0)
            while stripped and not stripped[-1]:
                stripped.pop()
            return stripped

        desc_lines = _clean(sections.get('__desc__', []))
        description = ' '.join(l for l in desc_lines if l)

        nombre_lines = _clean(sections.get('nombre', []))
        nombre = nombre_lines[0].strip() if nombre_lines else slug

        uso_lines = _clean(sections.get('uso', []))
        usage = '\n'.join(uso_lines)

        tipo_lines = _clean(sections.get('tipo', []))
        tipo = tipo_lines[0].strip().lower() if tipo_lines else 'ajax'

        def _placeholder(desc):
            m = re.search(r'\(ej[.:]?\s*([^)]+)\)', desc, re.IGNORECASE)
            if m:
                return m.group(1).strip()
            m = re.search(r'default\s+"([^"]+)"', desc, re.IGNORECASE)
            if m:
                return m.group(1).strip()
            m = re.search(r'default\s+([^\s,.(]+)', desc, re.IGNORECASE)
            if m:
                return m.group(1).strip()
            return ''

        config_fields = []
        for line in sections.get('config', []):
            m = re.match(r'^\s{0,6}(\w+)\s+[—-]+\s+(.+)$', line)
            if m:
                desc = m.group(2).strip()
                config_fields.append({
                    'name': m.group(1).strip(),
                    'desc': desc,
                    'placeholder': _placeholder(desc),
                })

        for line in sections.get('parámetros', []) + sections.get('parametros', []):
            m = re.match(r'^\s{0,6}(\w+)\s+[—-]+\s+(.+)$', line)
            if m:
                name = m.group(1).strip()
                desc = m.group(2).strip()
                optional = '(opcional)' in desc.lower()
                params.append({
                    'name': name,
                    'desc': desc,
                    'optional': optional,
                    'placeholder': _placeholder(desc),
                    'test_value': test_defaults.get(name, ''),
                })

        # Config fields son también parámetros (opcionales en tiempo de preview)
        for cf in config_fields:
            if not any(p['name'] == cf['name'] for p in params):
                params.append({
                    'name': cf['name'],
                    'desc': cf['desc'],
                    'optional': True,
                    'placeholder': cf['placeholder'],
                    'test_value': test_defaults.get(cf['name'], ''),
                })

        _FLAG_CSS = {0: 'badge-ghost', 1: 'badge-error', 2: 'badge-warning', 3: 'badge-success'}
        for line in sections.get('estados', []):
            m = re.match(r'^\s*([0-3])\s+[—-]+\s+(.+)$', line)
            if m:
                level = int(m.group(1))
                estados.append({
                    'level': level,
                    'desc': m.group(2).strip(),
                    'css': _FLAG_CSS.get(level, 'badge-ghost'),
                })
    else:
        tipo = 'ajax'
        nombre = slug
        config_fields = []
        vars_found = sorted(set(re.findall(r'\{\{\s*(\w+)[\s.|]', source)))
        for v in vars_found:
            if v not in ('block', 'widget', 'forloop', 'True', 'False'):
                params.append({
                    'name': v,
                    'desc': '',
                    'optional': False,
                    'test_value': test_defaults.get(v, ''),
                })

    if usage:
        include_tag = '{{% {} %}}'.format(usage.strip())
    else:
        include_tag = "{{% include 'widgets/{}' %}}".format(filename)

    return {
        'name': filename,
        'slug': slug,
        'nombre': nombre,
        'is_page': is_page,
        'params': params,
        'estados': estados,
        'description': description,
        'usage': usage,
        'has_docs': bool(comment_match),
        'include_tag': include_tag,
        'tipo': tipo,
        'config_fields': config_fields,
    }


def get_widget_meta(slug):
    """Returns parsed widget meta (tipo, config_fields) from its comment block."""
    try:
        return _parse_widget(f'{slug}.html')
    except Exception:
        return {'tipo': 'ajax', 'config_fields': []}


def _parse_boton_icon(slug):
    """Extrae la clase del primer <i> del template {slug}_boton.html."""
    path = os.path.join(WIDGETS_DIR, f'{slug}_boton.html')
    try:
        with open(path, encoding='utf-8') as fh:
            m = re.search(r'<i\s+class="([^"]+)"', fh.read())
            if m:
                return m.group(1)
    except OSError:
        pass
    return 'fa-solid fa-puzzle-piece text-primary'


def _boton_ctx(slug):
    from widgets.registry import get_widget
    w = get_widget(slug)
    icon = (w.icon if w and w.icon else None) or _parse_boton_icon(slug)
    return {
        'url': f'/widgets/preview/{slug}/',
        'color': 'ghost',
        'icon': icon,
    }


@superuser_required
def catalog(request):
    templates = sorted(
        f for f in os.listdir(WIDGETS_DIR)
        if f.endswith('.html') and not f.endswith('_boton.html')
    )
    widgets = [w for w in (_parse_widget(t) for t in templates) if not w['is_page']]
    for w in widgets:
        w['icon_template'] = 'widgets/{}_boton.html'.format(w['slug'])
        w['boton_ctx'] = _boton_ctx(w['slug'])
    return render(request, 'widget_catalog.html', {'widgets': widgets})


def icon_view(request, slug):
    return render(request, f'widgets/{slug}_boton.html', {'widget': _boton_ctx(slug)})


# ── Mocks para widgets con objetos Python complejos ─────────────────────────

class _UbicacionForm(forms.Form):
    lat = forms.CharField(
        label='Latitud',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': ''}),
        help_text='Grados decimales.',
    )
    lon = forms.CharField(
        label='Longitud',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': ''}),
        help_text='Grados decimales.',
    )



def _build_preview_context(slug, get_params):
    """Devuelve el contexto combinando GET params y mocks por widget."""
    ctx = {k: v for k, v in get_params.items() if v != ''}

    if slug == 'ubicacion_widget':
        form = _UbicacionForm()
        ctx['lat_field'] = form['lat']
        ctx['lon_field'] = form['lon']

    return ctx


# ── Dev photo endpoints (solo para pruebas del catálogo) ─────────────────────

class DevPhotoListView(LoginRequiredMixin, View):
    def get(self, request):
        from .models import DevPhoto
        photos = [
            {'id': p.id, 'url': p.imagen.url, 'descripcion': p.descripcion or ''}
            for p in DevPhoto.objects.all()
        ]
        return JsonResponse({'photos': photos})


class DevPhotoUploadView(LoginRequiredMixin, View):
    def post(self, request):
        from .models import DevPhoto
        files = request.FILES.getlist('photos')
        if not files:
            return JsonResponse({'success': False, 'message': 'Sin archivos'}, status=400)
        saved = []
        for f in files:
            photo = DevPhoto.objects.create(imagen=f)
            saved.append({'id': photo.id, 'url': photo.imagen.url, 'descripcion': ''})
        return JsonResponse({'success': True, 'photos': saved})


class DevPhotoUpdateView(LoginRequiredMixin, View):
    def post(self, request):
        import json as _json
        from .models import DevPhoto
        try:
            body = _json.loads(request.body)
        except _json.JSONDecodeError:
            return JsonResponse({'success': False}, status=400)
        photo_id = body.get('photo_id')
        descripcion = body.get('descripcion', '')
        DevPhoto.objects.filter(pk=photo_id).update(descripcion=descripcion)
        return JsonResponse({'success': True})


class DevPhotoDeleteView(LoginRequiredMixin, View):
    def post(self, request, photo_id):
        from .models import DevPhoto
        photo = DevPhoto.objects.filter(pk=photo_id).first()
        if photo:
            photo.imagen.delete(save=False)
            photo.delete()
        return JsonResponse({'success': True})


@xframe_options_sameorigin
def preview(request, slug):
    template_name = 'widgets/{}.html'.format(slug)
    try:
        t = get_template(template_name)
        is_page = bool(re.match(r'\s*\{%-?\s*extends\b', t.template.source))
    except Exception:
        is_page = False

    context = _build_preview_context(slug, request.GET)

    if is_page:
        return render(request, template_name, context)
    return render(request, 'widget_preview_frame.html', {'widget_template': template_name, **context})
