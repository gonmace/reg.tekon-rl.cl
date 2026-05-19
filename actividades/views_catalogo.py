import json as _json
import os
import re

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from django_tables2 import SingleTableView

from .forms import PasoDefinicionForm
from .models import ConfigPaso, PasoDefinicion, PasoWidget, TipoActividad
from .resources import ConfigPasoResource
from .tables import PasoDefinicionTable

_WIDGETS_DIR = os.path.join(settings.BASE_DIR, 'widgets', 'templates', 'widgets')


def _parse_icon_class(slug):
    """Devuelve la clase FA del widget: primero desde el registry, luego parseando el _boton.html."""
    try:
        from widgets.registry import get_widget
        w = get_widget(slug)
        if w and w.icon:
            return w.icon
    except Exception:
        pass
    icon_path = os.path.join(_WIDGETS_DIR, f'{slug}_boton.html')
    try:
        with open(icon_path, encoding='utf-8') as fh:
            source = fh.read()
        m = re.search(r'<i\s+class="([^"]+)"', source)
        if m and '{{' not in m.group(1):
            return m.group(1)
    except OSError:
        pass
    return 'fa-solid fa-puzzle-piece text-primary'


def _available_widgets():
    """Devuelve lista de dicts {slug, icon_class, tipo, config_fields}."""
    from widgets.views import get_widget_meta
    try:
        files = sorted(
            f for f in os.listdir(_WIDGETS_DIR)
            if f.endswith('.html')
            and not f.endswith('_boton.html')
            and not f.endswith('_page.html')
        )
        result = []
        for f in files:
            slug = f.replace('.html', '')
            meta = get_widget_meta(slug)
            icon_class = _parse_icon_class(slug)
            result.append({
                'slug': slug,
                'nombre': meta.get('nombre', slug),
                'icon_class': icon_class,
                'tipo': meta.get('tipo', 'ajax'),
                'boton_ctx': {
                    'url': f'/widgets/preview/{slug}/',
                    'color': 'ghost',
                    'icon': icon_class,
                },
            })
        return result
    except OSError:
        return []


def _widget_icon_map():
    """Devuelve {slug: icon_class} para lookups en templates."""
    return {w['slug']: w['icon_class'] for w in _available_widgets()}


def _widget_meta_map():
    """Devuelve {slug: {tipo, config_fields}} para lookups en templates."""
    return {w['slug']: {'tipo': w['tipo'], 'config_fields': w['config_fields']} for w in _available_widgets()}


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return self.request.user.is_superuser


# ── Catálogo de Pasos ─────────────────────────────────────────────────────────

class PasoDefinicionListView(SuperuserRequiredMixin, SingleTableView):
    model = PasoDefinicion
    table_class = PasoDefinicionTable
    template_name = 'actividades/paso_catalogo.html'
    paginate_by = 30

    def get_queryset(self):
        qs = PasoDefinicion.objects.all()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(titulo__icontains=q) | Q(nombre__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['header_title'] = 'Catálogo de Pasos'
        return ctx


class PasoDefinicionModalView(SuperuserRequiredMixin, View):
    template_name = 'actividades/paso_modal.html'

    def get(self, request, pk=None):
        instance = get_object_or_404(PasoDefinicion, pk=pk) if pk else None
        form = PasoDefinicionForm(instance=instance)
        ctx = {'form': form, 'instance': instance}
        cp_pk = request.GET.get('cp_pk')
        if cp_pk:
            cp = ConfigPaso.objects.filter(pk=cp_pk, pasodef=instance).first()
            if cp:
                ctx['cp_pk'] = cp.pk
                ctx['cp_orden'] = cp.orden
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        instance = get_object_or_404(PasoDefinicion, pk=pk) if pk else None
        form = PasoDefinicionForm(request.POST, instance=instance)
        if form.is_valid():
            paso = form.save()
            orden_str = request.POST.get('orden')
            cp_pk = request.POST.get('cp_pk')
            if cp_pk and orden_str is not None:
                cp = ConfigPaso.objects.filter(pk=cp_pk, pasodef=instance).first()
                if cp:
                    try:
                        cp.orden = int(orden_str)
                        cp.save(update_fields=['orden'])
                    except ValueError:
                        pass
            verb = 'actualizado' if pk else 'creado'
            return JsonResponse({'success': True, 'message': f'Paso "{paso.titulo}" {verb}.'})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


class PasoDefinicionDeleteView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        paso = get_object_or_404(PasoDefinicion, pk=pk)
        usos = paso.asignaciones.count()
        if usos > 0:
            return JsonResponse(
                {'success': False, 'message': f'No se puede eliminar: asignado a {usos} tipo(s).'},
                status=400,
            )
        titulo = paso.titulo
        paso.delete()
        return JsonResponse({'success': True, 'message': f'Paso "{titulo}" eliminado.'})


class PasoDefinicionCloneView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        import random
        import string
        original = get_object_or_404(PasoDefinicion, pk=pk)
        suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
        clone = PasoDefinicion.objects.create(
            nombre=f'{original.nombre}-{suffix}',
            titulo=f'{original.titulo} (copia)',
            descripcion=original.descripcion,
        )
        return JsonResponse({'success': True, 'message': f'Paso clonado como "{clone.titulo}".'})


# ── Tipos de Actividad — asignación de pasos ─────────────────────────────────

class TipoActividadListView(SuperuserRequiredMixin, View):
    template_name = 'actividades/tipo_list.html'

    def get(self, request):
        tipos = TipoActividad.objects.all()
        return render(request, self.template_name, {
            'tipos': tipos,
            'header_title': 'Tipos de Actividad',
        })


class TipoPasosView(SuperuserRequiredMixin, View):
    template_name = 'actividades/tipo_pasos.html'

    def get(self, request, pk):
        from django.urls import reverse as _reverse
        tipo = get_object_or_404(TipoActividad, pk=pk)
        config_pasos = tipo.config_pasos.order_by('orden').select_related('pasodef').prefetch_related('pasodef__paso_widgets')
        available = PasoDefinicion.objects.exclude(asignaciones__tipo=tipo).order_by('titulo')
        back_url = request.GET.get('back_url') or _reverse('actividades:tipo_list')
        back_label = request.GET.get('back_label') or 'Tipos de Actividad'
        next_orden = config_pasos.count()
        from widgets.views import get_widget_meta
        available_widgets = _available_widgets()
        widget_meta_map = {w['slug']: get_widget_meta(w['slug']) for w in available_widgets}
        widget_icon_map = _widget_icon_map()

        # Per-paso widget data for JS: {pasodef_pk: [{slug, config}, ...]} ordered by orden
        paso_widgets_data = {}
        for cp in config_pasos:
            paso_widgets_data[str(cp.pasodef.pk)] = [
                {'slug': pw.widget_slug, 'config': pw.config}
                for pw in cp.pasodef.paso_widgets.order_by('orden')
            ]

        return render(request, self.template_name, {
            'tipo': tipo,
            'config_pasos': config_pasos,
            'next_orden': next_orden,
            'header_title': f'Pasos — {tipo.nombre}',
            'back_url': back_url,
            'back_label': back_label,
            'available': available,
            'available_widgets': available_widgets,
            'widget_icon_map': widget_icon_map,
            'widget_meta_map': widget_meta_map,
            'paso_widgets_json': _json.dumps(paso_widgets_data),
            'widget_icon_map_json': _json.dumps(widget_icon_map),
        })


class TipoPasoAddView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        tipo = get_object_or_404(TipoActividad, pk=pk)
        paso_id = request.POST.get('paso_id')
        pasodef = get_object_or_404(PasoDefinicion, pk=paso_id)
        if ConfigPaso.objects.filter(tipo=tipo, pasodef=pasodef).exists():
            return JsonResponse({'success': False, 'message': 'El paso ya está asignado.'}, status=400)
        next_orden = ConfigPaso.objects.filter(tipo=tipo).count()
        ConfigPaso.objects.create(tipo=tipo, pasodef=pasodef, orden=next_orden)
        return JsonResponse({'success': True, 'message': f'Paso "{pasodef.titulo}" asignado.'})


class TipoPasoRemoveView(SuperuserRequiredMixin, View):
    def post(self, request, pk, cp_pk):
        from actividades.models import DatoPaso
        tipo = get_object_or_404(TipoActividad, pk=pk)
        cp = get_object_or_404(ConfigPaso, pk=cp_pk, tipo=tipo)
        pasodef = cp.pasodef
        titulo = pasodef.titulo
        cp.delete()
        if not pasodef.asignaciones.exists() and not DatoPaso.objects.filter(paso_nombre=pasodef.nombre).exists():
            pasodef.delete()
        return JsonResponse({'success': True, 'message': f'Paso "{titulo}" quitado.'})


class PasoWidgetsSetView(SuperuserRequiredMixin, View):
    """Reemplaza la lista completa de widgets de un paso."""
    def post(self, request, pk):
        paso = get_object_or_404(PasoDefinicion, pk=pk)
        slugs = request.POST.getlist('widget_slugs')
        allowed = {w['slug'] for w in _available_widgets()}
        invalid = [s for s in slugs if s not in allowed]
        if invalid:
            return JsonResponse({'success': False, 'message': f'Widgets no reconocidos: {", ".join(invalid)}'}, status=400)

        import json as _json
        configs = {}
        for key, val in request.POST.items():
            if key.startswith('cfg_'):
                parts = key[4:].split('__', 1)
                if len(parts) == 2:
                    slug_k, field_k = parts
                    try:
                        parsed = _json.loads(val)
                        # Normalizar listas JSON a CSV string para consistencia con entrada manual
                        if isinstance(parsed, list):
                            configs.setdefault(slug_k, {})[field_k] = ', '.join(str(x) for x in parsed)
                        else:
                            configs.setdefault(slug_k, {})[field_k] = parsed
                    except (ValueError, TypeError):
                        try:
                            configs.setdefault(slug_k, {})[field_k] = int(val)
                        except ValueError:
                            configs.setdefault(slug_k, {})[field_k] = val

        paso.paso_widgets.all().delete()
        for orden, slug in enumerate(slugs):
            PasoWidget.objects.create(pasodef=paso, widget_slug=slug, orden=orden, config=configs.get(slug, {}))
        count = len(slugs)
        msg = f'{count} widget{"s" if count != 1 else ""} asignado{"s" if count != 1 else ""}.' if count else 'Widgets quitados.'
        return JsonResponse({'success': True, 'message': msg})


class TipoPasoCreateView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        import re
        tipo = get_object_or_404(TipoActividad, pk=pk)
        titulo = request.POST.get('titulo', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        try:
            orden = int(request.POST.get('orden', 0))
        except (ValueError, TypeError):
            orden = ConfigPaso.objects.filter(tipo=tipo).count()

        if not titulo:
            return JsonResponse({'success': False, 'message': 'El título es obligatorio.'}, status=400)
        if not nombre:
            return JsonResponse({'success': False, 'message': 'El slug es obligatorio.'}, status=400)
        if not re.match(r'^[a-z0-9][a-z0-9-]*$', nombre):
            return JsonResponse({
                'success': False,
                'message': 'El slug solo puede contener letras minúsculas, números y guiones.',
            }, status=400)
        if ConfigPaso.objects.filter(tipo=tipo, pasodef__nombre=nombre).exists():
            return JsonResponse({'success': False, 'message': f'Ya existe un paso "{nombre}" en este tipo.'}, status=400)

        paso = PasoDefinicion.objects.create(nombre=nombre, titulo=titulo)
        ConfigPaso.objects.create(tipo=tipo, pasodef=paso, orden=orden)
        return JsonResponse({'success': True, 'message': f'Paso "{titulo}" creado.'})


# ── Export / Import de pasos de un tipo ────────────────────────────────────

class TipoPasosExportView(SuperuserRequiredMixin, View):
    """Exporta los pasos asignados a un TipoActividad como Excel (.xlsx)."""

    def get(self, request, pk):
        tipo = get_object_or_404(TipoActividad, pk=pk)
        qs = ConfigPaso.objects.filter(
            tipo=tipo,
        ).order_by('orden').select_related('pasodef').prefetch_related('pasodef__paso_widgets')
        resource = ConfigPasoResource()
        dataset = resource.export(qs)
        xlsx_bytes = dataset.export('xlsx')
        response = HttpResponse(
            xlsx_bytes,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="pasos_{tipo.nombre}.xlsx"'
        return response


class TipoPasosImportView(SuperuserRequiredMixin, View):
    """Importa pasos desde Excel/CSV para un TipoActividad específico."""

    def post(self, request, pk):
        from import_export.formats.base_formats import CSV, XLSX
        from widgets.registry import get_widget

        tipo = get_object_or_404(TipoActividad, pk=pk)
        upload = request.FILES.get('file')
        if not upload:
            return JsonResponse({'success': False, 'message': 'No se recibió ningún archivo.'}, status=400)

        ext = upload.name.lower().rsplit('.', 1)[-1]
        if ext == 'xlsx':
            file_format = XLSX()
        elif ext == 'csv':
            file_format = CSV()
        else:
            return JsonResponse({
                'success': False,
                'message': 'Formato no soportado. Usá .xlsx o .csv.',
            }, status=400)

        try:
            data = file_format.create_dataset(upload.read())
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'No se pudo leer el archivo: {e}',
            }, status=400)

        created = 0
        updated = 0
        errors = []

        for i, row in enumerate(data.dict, start=1):
            nombre = (row.get('nombre') or '').strip()
            titulo = (row.get('titulo') or '').strip()
            descripcion = (row.get('descripcion') or '').strip()
            try:
                orden = int(row.get('orden', 0))
            except (ValueError, TypeError):
                orden = 0

            if not nombre or not titulo:
                errors.append(f'Fila {i}: nombre y título son obligatorios.')
                continue

            if not re.match(r'^[a-z0-9][a-z0-9-]*$', nombre):
                errors.append(f'Fila {i}: slug inválido "{nombre}".')
                continue

            pasodef, paso_created = PasoDefinicion.objects.update_or_create(
                nombre=nombre,
                defaults={'titulo': titulo, 'descripcion': descripcion},
            )

            cp, cp_created = ConfigPaso.objects.update_or_create(
                tipo=tipo, pasodef=pasodef,
                defaults={'orden': orden},
            )

            if cp_created:
                created += 1
            else:
                updated += 1

            widgets_raw = row.get('widgets_json', '')
            if widgets_raw:
                try:
                    widgets_data = _json.loads(widgets_raw)
                    if isinstance(widgets_data, list):
                        pasodef.paso_widgets.all().delete()
                        for w_data in widgets_data:
                            slug = w_data.get('slug', '')
                            if not slug:
                                continue
                            if get_widget(slug):
                                PasoWidget.objects.create(
                                    pasodef=pasodef,
                                    widget_slug=slug,
                                    orden=w_data.get('orden', 0),
                                    config=w_data.get('config', {}),
                                )
                except (_json.JSONDecodeError, TypeError):
                    pass

        return JsonResponse({
            'success': True,
            'message': f'Importación completa: {created} creados, {updated} actualizados.',
            'created': created,
            'updated': updated,
            'errors': errors[:10],
        })
