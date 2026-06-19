from django_weasyprint.views import WeasyTemplateView
from datetime import datetime
from reg_txtss.models import RegTxtss
from django.conf import settings
from pathlib import Path
from django.shortcuts import render
from core.models.google_maps import GoogleMapsImage
from django.contrib.contenttypes.models import ContentType
from widgets.report import get_registro_report_data
from core.utils.coordenadas import calcular_distancia_geopy
from PIL import Image as PilImage, ImageOps

# Tag EXIF "Orientation" (0x0112). Valores 5-8 implican rotación de 90°/270°,
# es decir: el ancho/alto de los píxeles está intercambiado respecto a cómo
# debe verse la foto.
_EXIF_ORIENTATION_TAG = 0x0112
_EXIF_SWAPPED_ORIENTATIONS = (5, 6, 7, 8)


def _foto_orientation(path_str):
    """Devuelve 'portrait' si alto > ancho, 'landscape' en cualquier otro caso.

    Considera la orientación EXIF: una foto vertical suele guardarse con los
    píxeles en horizontal + un tag de rotación, así que hay que intercambiar
    ancho/alto antes de decidir.
    """
    try:
        with PilImage.open(path_str) as img:
            w, h = img.size
            orientation = img.getexif().get(_EXIF_ORIENTATION_TAG, 1)
            if orientation in _EXIF_SWAPPED_ORIENTATIONS:
                w, h = h, w
            return 'portrait' if h > w else 'landscape'
    except Exception:
        return 'landscape'


# Lado máximo (px) al que se reduce cada foto antes de pasarla a WeasyPrint.
# WeasyPrint decodifica las imágenes a su resolución NATIVA en RAM sin importar
# el ancho CSS: una foto de 4032×3024 (~12 MP) ocupa ~48 MB decodificada. Con
# 10-20 fotos por registro eso revienta el límite de memoria del contenedor y el
# worker de gunicorn muere por OOM. 1600 px es de sobra para impresión A4 (~200 dpi).
PDF_IMG_MAX_SIDE = 1600


def _pdf_image_uri(path_str):
    """Devuelve un file:// URI a una versión reducida y cacheada de la imagen.

    Si la imagen ya es pequeña o falla el procesamiento, devuelve el original.
    El cache vive en MEDIA_ROOT/pdf_cache/ para que el preview /media/ también lo sirva.
    """
    if not path_str:
        return None
    try:
        src = Path(path_str)
        st = src.stat()
        with PilImage.open(src) as img:
            w, h = img.size
            orientation = img.getexif().get(_EXIF_ORIENTATION_TAG, 1)
        # WeasyPrint NO aplica la orientación EXIF: renderiza los píxeles tal cual.
        # Si la foto tiene un tag de rotación hay que reescribirla rotando los
        # píxeles, aunque sea pequeña; de lo contrario sale "hechada" en el PDF.
        needs_rotation = orientation not in (0, 1)
        if max(w, h) <= PDF_IMG_MAX_SIDE and not needs_rotation:
            return src.as_uri()

        import hashlib
        cache_dir = Path(settings.MEDIA_ROOT) / 'pdf_cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        # 'v2' invalida los cachés generados antes de aplicar exif_transpose.
        key = hashlib.md5(
            f'{src}|{st.st_mtime_ns}|{st.st_size}|{PDF_IMG_MAX_SIDE}|v2'.encode()
        ).hexdigest()
        cached = cache_dir / f'{key}.jpg'
        if not cached.exists():
            with PilImage.open(src) as img:
                # Rota físicamente los píxeles según el tag EXIF y elimina el tag.
                img = ImageOps.exif_transpose(img)
                img = img.convert('RGB')
                img.thumbnail((PDF_IMG_MAX_SIDE, PDF_IMG_MAX_SIDE), PilImage.LANCZOS)
                img.save(cached, 'JPEG', quality=85, optimize=True)
        return cached.as_uri()
    except Exception:
        try:
            return Path(path_str).as_uri()
        except Exception:
            return None


def _get_fotos_pdf(registro, etapa, ct):
    """Fotos de una etapa con EXIF, orientación y file:// URI para WeasyPrint."""
    from photos.models import Photos
    fotos = []
    for p in Photos.objects.filter(
        content_type=ct, object_id=registro.id, etapa=etapa
    ).order_by('orden', '-created_at'):
        try:
            path_str = p.imagen.path
            url = _pdf_image_uri(path_str)
        except Exception:
            path_str = None
            url = p.imagen.url if p.imagen else ''
        fotos.append({
            'url': url,
            'descripcion': p.descripcion or '',
            'exif_datetime': p.exif_datetime.strftime('%d/%m/%Y %H:%M') if p.exif_datetime else None,
            'exif_lat': round(p.exif_lat, 6) if p.exif_lat is not None else None,
            'exif_lon': round(p.exif_lon, 6) if p.exif_lon is not None else None,
            'orientation': _foto_orientation(path_str) if path_str else 'landscape',
        })
    return fotos


def _file_uri_to_media_url(url):
    """Convierte un file:// URI bajo MEDIA_ROOT a una URL /media/ (para preview)."""
    media_root = str(settings.MEDIA_ROOT).rstrip('/')
    if url and url.startswith('file://'):
        path = url[7:]
        if path.startswith(media_root):
            return settings.MEDIA_URL + path[len(media_root):].lstrip('/')
    return url


def _fotos_to_media_urls(fotos):
    """Convierte file:// URIs a URLs /media/ para preview en navegador."""
    result = []
    for f in fotos:
        item = dict(f)
        item['url'] = _file_uri_to_media_url(item.get('url', ''))
        result.append(item)
    return result


def _media_url_to_path(url):
    """Convierte una URL /media/... al path absoluto en disco, o None."""
    if not url or not url.startswith(settings.MEDIA_URL):
        return None
    rel = url[len(settings.MEDIA_URL):].lstrip('/')
    return str(Path(settings.MEDIA_ROOT) / rel)


def _pdf_url_from_media_url(url):
    """Versión reducida + EXIF-corregida (file:// URI) de una foto /media/.

    Devuelve la URL original si no se puede mapear a un archivo en disco.
    """
    path_str = _media_url_to_path(url)
    if not path_str:
        return url
    return _pdf_image_uri(path_str) or url


def _walk_pasos_widgets_urls(pasos_widgets, fn):
    """Aplica fn a cada URL de foto de los widgets camera/imgs_desc (in place).

    Son los dos widgets que muestran p.imagen.url directo (sin pasar por
    fotos_tabla), así que necesitan la misma normalización para el PDF.
    """
    for paso in pasos_widgets or []:
        for widget in paso.get('widgets', []):
            slug = widget.get('slug')
            display = widget.get('display') or {}
            if slug == 'camera_widget':
                for foto in display.get('photos') or []:
                    if foto.get('url'):
                        foto['url'] = fn(foto['url'])
            elif slug == 'imgs_desc_widget':
                for item in display.get('items') or []:
                    photo = item.get('photo')
                    if photo and photo.get('url'):
                        photo['url'] = fn(photo['url'])


def convert_lat_to_dms(lat):
    if lat is None:
        return 'N/A'
    direction = 'N' if lat >= 0 else 'S'
    deg_abs = abs(lat)
    degrees = int(deg_abs)
    minutes_full = (deg_abs - degrees) * 60
    minutes = int(minutes_full)
    seconds = round((minutes_full - minutes) * 60, 2)
    return f"{direction} {degrees}° {minutes}' {seconds}''"

def convert_lon_to_dms(lon):
    if lon is None:
        return 'N/A'
    direction = 'E' if lon >= 0 else 'W'
    deg_abs = abs(lon)
    degrees = int(deg_abs)
    minutes_full = (deg_abs - degrees) * 60
    minutes = int(minutes_full)
    seconds = round((minutes_full - minutes) * 60, 2)
    return f"{direction} {degrees}° {minutes}' {seconds}''"



class RegistroPDFView(WeasyTemplateView):
    template_name = 'reportes_txtss/txtss.html'
    pdf_attachment = False  # abre inline; el filename se usa al guardar
    pdf_options = {
        'default-font-family': 'Arial',
        'default-font-size': 12,
        'enable-local-file-access': True,
    }
    pdf_stylesheets = [str(Path(settings.BASE_DIR) / 'static/css/weasyprint.css')]

    def get_pdf_filename(self):
        import re
        registro_id = self.kwargs.get('registro_id')
        try:
            reg = RegTxtss.objects.select_related('sitio').get(id=registro_id)
            def _clean(s):
                # Remove characters invalid in filenames, keep spaces/hyphens/underscores
                return re.sub(r'[\\/:*?"<>|]', '', str(s or '')).strip()
            parts = [
                _clean(reg.sitio.pti_cell_id),
                _clean(reg.sitio.operator_id),
                _clean(reg.sitio.name),
                _clean(reg.alternativa),
            ]
            return '-'.join(p for p in parts if p) + '.pdf'
        except Exception:
            return 'registro.pdf'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registro_id = self.kwargs.get('registro_id')

        registro = RegTxtss.objects.select_related('sitio', 'user').get(id=registro_id)

        registro_content_type = ContentType.objects.get_for_model(registro)

        # Mapas de widgets mapa_1p (mandato) y mapa_2_puntos (desfase)
        mapa_mandato_obj = GoogleMapsImage.objects.filter(
            content_type=registro_content_type, object_id=registro.id, etapa='mandato'
        ).first()
        mapa_desfase_obj = GoogleMapsImage.objects.filter(
            content_type=registro_content_type, object_id=registro.id, etapa='desfase'
        ).first()

        # Fallback legacy (etapas anteriores al sistema de widgets)
        mapa_sitio = GoogleMapsImage.objects.filter(
            content_type=registro_content_type, object_id=registro.id, etapa='sitio'
        ).first()
        mapa_empalme = GoogleMapsImage.objects.filter(
            content_type=registro_content_type, object_id=registro.id, etapa='empalme'
        ).first()
        
        sitio_icon1_color = '#FFFF44'
        sitio_name1 = 'Inspección'
        sitio_icon2_color = None
        sitio_name2 = None

        empalme_icon1_color = '#FF4040'
        empalme_name1 = 'Empalme'
        empalme_icon2_color = '#FFFF44'
        empalme_name2 = 'Inspección'
        empalme_icon3_color = '#0054FF'
        empalme_name3 = 'Mandato'
            
        desfase_color = '#90EE90'  # placeholder; se recalcula más abajo con geopy

        def _fmt6(v):
            return f'{float(v):.6f}' if v is not None else ''

        geo_rows = [
            ['Mandato', _fmt6(registro.sitio.lat_man), convert_lat_to_dms(registro.sitio.lat_man), _fmt6(registro.sitio.lon_man), convert_lon_to_dms(registro.sitio.lon_man)],
        ]
        if registro.sitio.lat_ing is not None and registro.sitio.lon_ing is not None:
            geo_rows.append(['Ingeniería', _fmt6(registro.sitio.lat_ing), convert_lat_to_dms(registro.sitio.lat_ing), _fmt6(registro.sitio.lon_ing), convert_lon_to_dms(registro.sitio.lon_ing)])
        if registro.sitio.lat_con is not None and registro.sitio.lon_con is not None:
            geo_rows.append(['Construcción', _fmt6(registro.sitio.lat_con), convert_lat_to_dms(registro.sitio.lat_con), _fmt6(registro.sitio.lon_con), convert_lon_to_dms(registro.sitio.lon_con)])

        from actividades.models import ContextoRegistro
        ctx_obj = ContextoRegistro.objects.filter(
            content_type=registro_content_type, object_id=registro.id
        ).first()
        reg_contexto = ctx_obj.contexto if ctx_obj else {}

        # Extraer datos desde el contexto de widgets (fuente principal para registros sin legacy steps)
        pasos_ctx = reg_contexto.get('pasos', {})
        flat_ctx  = reg_contexto.get('flat', {})

        # Coordenadas de inspección desde widget ubicacion
        try:
            inspeccion_lat = float(flat_ctx['poste.lat']) if flat_ctx.get('poste.lat') else None
            inspeccion_lon = float(flat_ctx['poste.lon']) if flat_ctx.get('poste.lon') else None
        except (TypeError, ValueError):
            inspeccion_lat = None
            inspeccion_lon = None

        # Desfase calculado con geopy (misma fórmula que ubicacion_widget).
        # Fuente primaria: GPS de inspección vs lat_man/lon_man del sitio en BD.
        # Fallback: distancia_total_metros del mapa de desfase (puntos colocados manualmente).
        desfase_metros_val = None

        # Src de mapas: file:// URI para que WeasyPrint lea el archivo directamente,
        # sin necesidad de petición HTTP al servidor.
        def _file_uri(img_obj):
            if img_obj and img_obj.imagen:
                try:
                    return Path(img_obj.imagen.path).as_uri()
                except Exception:
                    return None
            return None

        mapa_mandato_src = _file_uri(mapa_mandato_obj) or _file_uri(mapa_sitio)
        mapa_desfase_src = _file_uri(mapa_desfase_obj) or _file_uri(mapa_empalme)
        tekon_logo_src = Path(settings.BASE_DIR, 'templates', 'svgs', 'tekon_logo.png').as_uri()

        # Datos del paso poste (widgets)
        poste_paso  = pasos_ctx.get('poste', {})
        poste_form  = poste_paso.get('poste_form_widget', {}).get('display', {})
        poste_ubic  = poste_paso.get('ubicacion_widget', {}).get('display', {})
        poste_comp  = poste_paso.get('ubicacion_widget', {}).get('computed', {})
        poste_fotos = _get_fotos_pdf(registro, 'poste', registro_content_type)
        imagenes_fotos = _get_fotos_pdf(registro, 'imagenes', registro_content_type)

        # Calcular desfase usando geopy (misma fórmula que ubicacion_widget).
        # Prioridad: GPS capturado vs mandato en BD → mapa_desfase_obj → mapa_sitio legacy.
        if inspeccion_lat and inspeccion_lon and registro.sitio.lat_man and registro.sitio.lon_man:
            desfase_metros_val = calcular_distancia_geopy(
                registro.sitio.lat_man, registro.sitio.lon_man,
                inspeccion_lat, inspeccion_lon,
            )
        if not desfase_metros_val:
            desfase_metros_val = (
                (mapa_desfase_obj.distancia_total_metros if mapa_desfase_obj else None)
                or (mapa_sitio.distancia_total_metros if mapa_sitio else None)
                or 0
            )
        if desfase_metros_val <= 150:
            desfase_color = '#90EE90'
        elif desfase_metros_val <= 200:
            desfase_color = '#FFFF44'
        else:
            desfase_color = '#FF4040'

        # Coordenadas del poste en formato DMS
        poste_lat_dms = convert_lat_to_dms(inspeccion_lat) if inspeccion_lat else 'N/A'
        poste_lon_dms = convert_lon_to_dms(inspeccion_lon) if inspeccion_lon else 'N/A'

        # Actualizar fila de inspección con coordenadas correctas
        geo_rows.append(['Inspección', _fmt6(inspeccion_lat), convert_lat_to_dms(inspeccion_lat), _fmt6(inspeccion_lon), convert_lon_to_dms(inspeccion_lon)])

        context.update({
            'registro': registro,
            'datos_generales': {
                f'Código {registro.sitio._meta.get_field("pti_cell_id").verbose_name}:': registro.sitio.pti_cell_id,
                f'Código {registro.sitio._meta.get_field("operator_id").verbose_name}:': registro.sitio.operator_id,
                f'{registro.sitio._meta.get_field("name").verbose_name}:': registro.sitio.name,
                f'{registro.sitio._meta.get_field("tipo_sitio").verbose_name}:': registro.sitio.get_tipo_sitio_display(),
                f'Alternativa:': registro.alternativa,
                f'{registro.sitio._meta.get_field("region").verbose_name}:': registro.sitio.region,
                f'{registro.sitio._meta.get_field("comuna").verbose_name}:': registro.sitio.comuna,
                'Altura:': poste_form.get('altura') or 'N/A',
                'Empresa de Energía:': poste_form.get('empresa_energia') or 'N/A',
            },
            'inspeccion_sitio': {
                'Responsable Técnico:': (registro.user.first_name + ' ' + registro.user.last_name).strip() if registro.user else 'N/A',
                'Fecha de Inspección:': registro.fecha.strftime('%d/%m/%Y'),
            },
            'datos_geograficos': {
                'headers': ['Ubicación', 'Latitud (°)', 'Latitud (DMS)', 'Longitud (°)', 'Longitud (DMS)'],
                'rows': geo_rows,
            },
            'desfase_metros': f'{desfase_metros_val:.0f} m' if desfase_metros_val else 'N/A',
            'desfase_color': desfase_color,

            # Mapas desde contexto de widgets
            'mapa_mandato_src': mapa_mandato_src,
            'mapa_desfase_src': mapa_desfase_src,
            'tekon_logo_src': tekon_logo_src,

            # Datos del poste (widget system)
            'poste_form': poste_form,
            'poste_ubic': poste_ubic,
            'poste_comp': poste_comp,
            'poste_lat_dms': poste_lat_dms,
            'poste_lon_dms': poste_lon_dms,
            'poste_fotos': poste_fotos,
            'imagenes_fotos': imagenes_fotos,

            'pasos_widgets': get_registro_report_data(registro),
            'reg_contexto': reg_contexto,
        })

        # camera_widget e imgs_desc_widget muestran p.imagen.url directo: pasarlas
        # por _pdf_image_uri (reducción a 1600px + orientación EXIF) igual que
        # fotos_tabla, para evitar OOM y fotos "hechadas" en el PDF.
        _walk_pasos_widgets_urls(context['pasos_widgets'], _pdf_url_from_media_url)

        # Opciones de layout de fotos (query params: poste_cols, imagenes_cols)
        try:
            poste_cols = int(self.request.GET.get('poste_cols', 2))
        except (ValueError, TypeError):
            poste_cols = 2
        try:
            imagenes_cols = int(self.request.GET.get('imagenes_cols', 2))
        except (ValueError, TypeError):
            imagenes_cols = 2
        context['poste_cols'] = poste_cols if poste_cols in (1, 2) else 2
        context['imagenes_cols'] = imagenes_cols if imagenes_cols in (1, 2) else 2

        return context

    def _get_sitio_photos(self, registro):
        """
        Obtiene todas las fotos relacionadas con el registro_sitio.
        Para la etapa 'sitio', las fotos se asocian al registro principal (RegTxtss).
        """
        from photos.models import Photos
        from django.contrib.contenttypes.models import ContentType
        
        # Obtener el ContentType del modelo del registro principal
        registro_content_type = ContentType.objects.get_for_model(registro)
        
        # Obtener todas las fotos para este registro, etapa 'sitio' y app 'reg_txtss'
        fotos = Photos.objects.filter(
            content_type=registro_content_type,
            object_id=registro.id,
            etapa='sitio',
            app='reg_txtss'
        ).order_by('orden', '-created_at')
        
        # Convertir a formato para el template
        fotos_list = []
        for foto in fotos:
            fotos_list.append({
                'src': foto.imagen.url,
                'alt': foto.descripcion or f'Foto del sitio {registro.sitio.pti_cell_id}',
                'descripcion': foto.descripcion,
                'orden': foto.orden
            })
        
        return fotos_list

    def _get_empalme_photos(self, registro):
        """
        Obtiene todas las fotos relacionadas con el registro_empalme.
        Para la etapa 'empalme', las fotos se asocian al registro principal (RegTxtss).
        """
        from photos.models import Photos
        from django.contrib.contenttypes.models import ContentType
        
        # Obtener el ContentType del modelo del registro principal
        registro_content_type = ContentType.objects.get_for_model(registro)
        
        # Obtener todas las fotos para este registro, etapa 'empalme' y app 'reg_txtss'
        fotos = Photos.objects.filter(
            content_type=registro_content_type,
            object_id=registro.id,
            etapa='empalme',
            app='reg_txtss'
        ).order_by('orden', '-created_at')
        
        # Convertir a formato para el template
        fotos_list = []
        for foto in fotos:
            fotos_list.append({
                'src': foto.imagen.url,
                'alt': foto.descripcion or f'Foto del empalme {registro.sitio.pti_cell_id}',
                'descripcion': foto.descripcion,
                'orden': foto.orden
            })
        
        return fotos_list

def preview_registro_individual(request, registro_id):
    view = RegistroPDFView()
    view.kwargs = {'registro_id': registro_id}
    context = view.get_context_data()

    # El PDF usa file:// URIs; el preview del navegador necesita URLs relativas /media/
    from core.models.google_maps import GoogleMapsImage
    from django.contrib.contenttypes.models import ContentType
    from reg_txtss.models import RegTxtss as _RegTxtss
    _ct = ContentType.objects.get_for_model(_RegTxtss)
    for etapa, key in [('mandato', 'mapa_mandato_src'), ('desfase', 'mapa_desfase_src'),
                       ('sitio', 'mapa_mandato_src'), ('empalme', 'mapa_desfase_src')]:
        if context.get(key):
            break
        img = GoogleMapsImage.objects.filter(content_type=_ct, object_id=registro_id, etapa=etapa).first()
        if img and img.imagen:
            context[key] = img.imagen.url

    # Reemplazar file:// por URL relativa para los dos mapas
    for etapa, key in [('mandato', 'mapa_mandato_src'), ('desfase', 'mapa_desfase_src')]:
        img = GoogleMapsImage.objects.filter(content_type=_ct, object_id=registro_id, etapa=etapa).first()
        if img and img.imagen:
            context[key] = img.imagen.url

    # Reemplazar file:// por /media/ en las fotos
    context['poste_fotos'] = _fotos_to_media_urls(context.get('poste_fotos', []))
    context['imagenes_fotos'] = _fotos_to_media_urls(context.get('imagenes_fotos', []))
    _walk_pasos_widgets_urls(context.get('pasos_widgets'), _file_uri_to_media_url)

    return render(request, 'reportes_txtss/txtss.html', context)