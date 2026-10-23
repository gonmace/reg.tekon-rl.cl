from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from actividades.models import DatoPaso, TipoActividad
from core.models.contractors import Contractor
from core.models.sites import Site
from django.contrib.contenttypes.models import ContentType
from users.models import User

from .models import PASO_AVANCE, RegConstruccion

PLAIN_STATIC = {
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
}


def partidas(*pares):
    return [{'id': f'p{i}', 'nombre': f'Partida {i}', 'incidencia': inc, 'actual': act}
            for i, (inc, act) in enumerate(pares)]


@override_settings(STORAGES=PLAIN_STATIC)
class BaseTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.contratista = Contractor.objects.create(name='AJ', code='AJ')
        cls.otra = Contractor.objects.create(name='OTRA', code='OT')
        cls.root = User.objects.create_superuser('root', 'r@x.cl', 'pw', user_type='')
        cls.coord = User.objects.create_user('coord', 'c@x.cl', 'pw', user_type=User.ADMINISTRADOR, contractor=cls.contratista)
        cls.ito = User.objects.create_user('ito', 'i@x.cl', 'pw', user_type=User.ITO, contractor=cls.contratista)
        cls.ito2 = User.objects.create_user('ito2', 'i2@x.cl', 'pw', user_type=User.ITO, contractor=cls.contratista)
        cls.torre = Site.objects.create(pti_cell_id='CL-VS-1458', operator_id='25_179', name='Quillota',
                                        tipo_sitio=Site.TORRE)
        cls.poste = Site.objects.create(pti_cell_id='CL-P-1', operator_id='1', name='Poste', tipo_sitio=Site.POSTE)

    def visita(self, fecha=None, **kw):
        kw.setdefault('user', self.ito)
        kw.setdefault('contratista', self.contratista)
        return RegConstruccion.objects.create(sitio=self.torre, fecha=fecha or date(2026, 1, 10), **kw)

    def guardar_avance(self, reg, filas):
        ct = ContentType.objects.get_for_model(RegConstruccion)
        DatoPaso.objects.update_or_create(content_type=ct, object_id=reg.id, paso_nombre=PASO_AVANCE,
                                          defaults={'datos': {'partidas': filas}})


class ModeloTests(BaseTest):
    def test_tipo_actividad_sembrado(self):
        tipo = TipoActividad.objects.get(app_namespace='reg_construccion_torres')
        self.assertEqual([c.pasodef.nombre for c in tipo.config_pasos.order_by('orden')],
                         ['obra_objetivos', 'obra_avance', 'obra_electrico', 'obra_comentarios'])

    def test_varias_visitas_por_sitio_con_fechas_distintas(self):
        a = self.visita(date(2026, 1, 10))
        b = self.visita(date(2026, 1, 20))
        self.assertEqual((a.numero_visita, b.numero_visita), (1, 2))

    def test_no_permite_misma_fecha_en_el_mismo_sitio(self):
        self.visita(date(2026, 1, 10))
        with self.assertRaises(ValidationError):
            self.visita(date(2026, 1, 10), user=self.ito2)

    def test_visita_eliminada_libera_la_fecha(self):
        a = self.visita(date(2026, 1, 10))
        a.soft_delete()
        self.visita(date(2026, 1, 10))

    def test_solo_sitios_torre(self):
        with self.assertRaises(ValidationError):
            RegConstruccion.objects.create(sitio=self.poste, user=self.ito, fecha=date(2026, 1, 1))

    def test_avance_pct_se_recalcula_en_cadena(self):
        a = self.visita(date(2026, 1, 10))
        b = self.visita(date(2026, 1, 20))
        self.guardar_avance(a, partidas((60, 50), (40, 0)))
        self.guardar_avance(b, partidas((60, 25), (40, 50)))
        a.refresh_from_db(); b.refresh_from_db()
        self.assertEqual(a.avance_pct, 30)               # 60 × 50 %
        self.assertEqual(b.avance_pct, 65)               # 60 × 75 % + 40 × 50 %
        self.guardar_avance(a, partidas((60, 100), (40, 0)))  # editar la visita antigua propaga
        a.refresh_from_db(); b.refresh_from_db()
        self.assertEqual(a.avance_pct, 60)
        self.assertEqual(b.avance_pct, 80)               # 60 × 100 % (tope) + 40 × 50 %


class VistasTests(BaseTest):
    def test_activar_crea_primera_visita(self):
        self.client.force_login(self.coord)
        r = self.client.post(reverse('reg_construccion:activar'),
                             {'sitio': self.torre.pk, 'user': self.ito.pk},
                             headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(RegConstruccion.objects.filter(sitio=self.torre).count(), 1)
        # activar de nuevo el mismo día → error amistoso, sin duplicar
        r = self.client.post(reverse('reg_construccion:activar'),
                             {'sitio': self.torre.pk, 'user': self.ito.pk},
                             headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(RegConstruccion.objects.filter(sitio=self.torre).count(), 1)

    def test_nueva_visita_copia_cabecera_y_rechaza_fecha_repetida(self):
        base = self.visita(date.today() - timedelta(days=7), proyecto='Rutas', revision=2)
        self.client.force_login(self.ito)
        url = reverse('reg_construccion:api_nueva_visita', kwargs={'registro_id': base.id})
        r = self.client.post(url, data='{}', content_type='application/json')
        self.assertEqual(r.status_code, 200, r.content)
        nueva = RegConstruccion.objects.exclude(pk=base.pk).get()
        self.assertEqual((nueva.proyecto, nueva.revision, nueva.fecha), ('Rutas', 2, date.today()))
        r = self.client.post(url, data='{}', content_type='application/json')
        self.assertEqual(r.status_code, 400)

    def test_listado_muestra_una_fila_por_sitio_y_sus_visitas_en_el_panel(self):
        self.visita(date(2026, 1, 10)); self.visita(date(2026, 1, 20))
        self.client.force_login(self.root)
        r = self.client.get(reverse('reg_construccion:list'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context['table'].rows), 1)            # un sitio, aunque tenga 2 visitas
        self.assertEqual(len(r.context['panel_table'].rows), 2)      # único sitio → se preselecciona

    def test_ito_solo_ve_y_edita_lo_suyo(self):
        mia = self.visita(date(2026, 1, 10))
        ajena = self.visita(date(2026, 1, 20), user=self.ito2)
        self.client.force_login(self.ito)
        r = self.client.get(reverse('reg_construccion:list'))
        self.assertEqual([s.pk for s in r.context['table'].data], [self.torre.pk])
        self.assertEqual([v.pk for v in r.context['panel_page'].object_list], [mia.pk])  # solo SU visita
        self.assertEqual(self.client.get(reverse('reg_construccion:steps', kwargs={'registro_id': ajena.pk})).status_code, 403)
        r = self.client.post(reverse('reg_construccion:api_update', kwargs={'registro_id': ajena.pk}),
                             {'fecha': '2026-02-01', 'proyecto': 'X', 'revision': 0, 'estado_obra': 'construccion'})
        self.assertEqual(r.status_code, 403)

    def test_administrador_y_superusuario_cambian_el_ito(self):
        admin = User.objects.create_user('adm3', 'adm3@x.cl', 'pw', user_type=User.ADMINISTRADOR)
        reg = self.visita(date(2026, 1, 10))
        url = reverse('reg_construccion:api_update', kwargs={'registro_id': reg.pk})
        for user, destino in ((admin, self.ito2), (self.root, self.ito)):
            self.client.force_login(user)
            r = self.client.get(reverse('reg_construccion:api_edit_form', kwargs={'registro_id': reg.pk}))
            self.assertContains(r, 'name="user"')
            r = self.client.post(url, {'user': destino.pk, 'fecha': '2026-03-01', 'revision': 9, 'estado_obra': 'construccion'})
            self.assertEqual(r.status_code, 200, r.content)
            reg.refresh_from_db()
            self.assertEqual(reg.user, destino)
        # un ITO no puede reasignar aunque envíe `user`
        self.client.force_login(self.ito)
        self.client.post(url, {'user': self.ito2.pk, 'fecha': '2026-01-10', 'revision': 0, 'estado_obra': 'construccion'})
        reg.refresh_from_db()
        self.assertEqual(reg.user, self.ito)

    def test_pasos_renderizan(self):
        reg = self.visita(date(2026, 1, 10))
        self.client.force_login(self.root)
        r = self.client.get(reverse('reg_construccion:steps', kwargs={'registro_id': reg.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Ítems Y Avance')
        for paso in ('obra_objetivos', 'obra_avance', 'obra_comentarios'):
            r = self.client.get(reverse('reg_construccion:paso_dinamico',
                                        kwargs={'registro_id': reg.pk, 'paso_nombre': paso}) + '?widget=' + (
                'tabla_avance_widget' if paso == 'obra_avance' else 'lista_widget'))
            self.assertEqual(r.status_code, 200, paso)

    def test_guardar_avance_ito_solo_cambia_porcentaje_actual(self):
        reg = self.visita(date(2026, 1, 10))
        self.guardar_avance(reg, partidas((60, 0), (40, 0)))
        self.client.force_login(self.ito)
        url = reverse('reg_construccion:paso_dinamico', kwargs={'registro_id': reg.pk, 'paso_nombre': PASO_AVANCE})
        import json
        enviado = [{'id': 'p0', 'nombre': 'HACKEADA', 'incidencia': 99, 'actual': 40},
                   {'id': 'p1', 'nombre': 'Partida 1', 'incidencia': 1, 'actual': 10},
                   {'id': 'nueva', 'nombre': 'Intrusa', 'incidencia': 0, 'actual': 5}]
        r = self.client.post(url + '?widget=tabla_avance_widget', {'partidas': json.dumps(enviado), 'plantilla': 'x'})
        self.assertEqual(r.status_code, 302, r.content)
        ct = ContentType.objects.get_for_model(RegConstruccion)
        guardado = DatoPaso.objects.get(content_type=ct, object_id=reg.pk, paso_nombre=PASO_AVANCE).datos['partidas']
        self.assertEqual([(p['nombre'], p['incidencia'], p['actual']) for p in guardado],
                         [('Partida 0', 60, 40), ('Partida 1', 40, 10)])

    def _post_estructura(self, user, reg, actual=25):
        import json
        self.client.force_login(user)
        url = reverse('reg_construccion:paso_dinamico', kwargs={'registro_id': reg.pk, 'paso_nombre': PASO_AVANCE})
        return self.client.post(url + '?widget=tabla_avance_widget', {
            'plantilla': 'Torre estándar',
            'partidas': json.dumps([{'id': 'a', 'nombre': 'Zapata', 'incidencia': 100, 'actual': actual}])})

    def test_administrador_y_superusuario_definen_la_estructura(self):
        admin = User.objects.create_user('adm', 'adm@x.cl', 'pw', user_type=User.ADMINISTRADOR)
        for user in (self.root, admin):
            reg = self.visita(date(2026, 1, 10) if user is self.root else date(2026, 2, 10))
            r = self._post_estructura(user, reg)
            self.assertEqual(r.status_code, 302, r.content)
            ct = ContentType.objects.get_for_model(RegConstruccion)
            guardado = DatoPaso.objects.get(content_type=ct, object_id=reg.pk, paso_nombre=PASO_AVANCE).datos
            self.assertEqual([p['nombre'] for p in guardado['partidas']], ['Zapata'])
            self.assertEqual(guardado['plantilla'], 'Torre estándar')

    def test_ito_no_puede_cambiar_la_estructura(self):
        """El ITO solo carga el % actual: los ítems enviados se descartan."""
        reg = self.visita(date(2026, 1, 10))
        self.guardar_avance(reg, partidas((60, 0), (40, 0)))
        for user in (self.ito,):
            r = self._post_estructura(user, reg, actual=25)
            self.assertEqual(r.status_code, 302, r.content)
            ct = ContentType.objects.get_for_model(RegConstruccion)
            guardado = DatoPaso.objects.get(content_type=ct, object_id=reg.pk, paso_nombre=PASO_AVANCE).datos['partidas']
            self.assertEqual([p['nombre'] for p in guardado], ['Partida 0', 'Partida 1'])  # sin «Zapata»

    def test_sin_cargar_datos_solo_se_define_la_estructura(self):
        """Quien tiene `definir_items_obra` pero no `cargar_datos` guarda únicamente la tabla de avance."""
        from core.models.permisos import PermisoUsuario
        admin = User.objects.create_user('adm2', 'adm2@x.cl', 'pw', user_type=User.ADMINISTRADOR)
        PermisoUsuario.objects.create(user=admin, accion='cargar_datos', permitido=False)
        reg = self.visita(date(2026, 1, 10))
        self.client.force_login(admin)
        url = reverse('reg_construccion:paso_dinamico', kwargs={'registro_id': reg.pk, 'paso_nombre': 'obra_objetivos'})
        self.assertEqual(self.client.post(url + '?widget=lista_widget', {'entradas': '["x"]'}).status_code, 403)
        self.assertEqual(self._post_estructura(admin, reg).status_code, 302)

    def test_administrador_carga_todos_los_pasos(self):
        admin = User.objects.create_user('adm4', 'adm4@x.cl', 'pw', user_type=User.ADMINISTRADOR)
        reg = self.visita(date(2026, 1, 10))
        self.client.force_login(admin)
        url = reverse('reg_construccion:paso_dinamico', kwargs={'registro_id': reg.pk, 'paso_nombre': 'obra_objetivos'})
        self.assertNotEqual(self.client.post(url + '?widget=lista_widget', {'entradas': '["x"]'}).status_code, 403)

    def test_pdf_se_genera(self):
        reg = self.visita(date(2026, 1, 10))
        self.guardar_avance(reg, partidas((100, 40)))
        self.client.force_login(self.root)
        r = self.client.get(reverse('reg_construccion:pdf', kwargs={'registro_id': reg.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.content.startswith(b'%PDF'))


class ActividadesInspeccionadasTests(BaseTest):
    """«Objetivos de la visita» se muestra como «Actividades» (clave interna intacta)."""

    def test_el_paso_se_muestra_con_el_nombre_nuevo(self):
        reg = self.visita(date(2026, 1, 10))
        self.client.force_login(self.root)
        r = self.client.get(reverse('reg_construccion:steps', kwargs={'registro_id': reg.pk}))
        self.assertContains(r, 'Actividades')
        self.assertNotContains(r, 'Objetivos De La Visita')

    def test_el_pdf_trae_las_entradas_guardadas_en_la_seccion_nueva(self):
        from django.template.loader import render_to_string
        reg = self.visita(date(2026, 1, 10))
        ct = ContentType.objects.get_for_model(RegConstruccion)
        DatoPaso.objects.create(content_type=ct, object_id=reg.id, paso_nombre='obra_objetivos',
                                datos={'entradas': ['Revisión de izaje', 'Revisión de AST']})
        self.client.force_login(self.root)
        r = self.client.get(reverse('reg_construccion:pdf', kwargs={'registro_id': reg.pk}))
        self.assertEqual(r.context_data['actividades'], ['Revisión de izaje', 'Revisión de AST'])
        html = render_to_string('reportes_construccion/construccion.html', r.context_data)
        self.assertIn('<h2>Actividades</h2>', html)
        self.assertNotIn('Objetivos de la Visita', html)
        self.assertIn('Revisión de AST', html)

    def test_pdf_oculta_comentarios_vacios_y_los_muestra_como_parrafos(self):
        from django.template.loader import render_to_string
        reg = self.visita(date(2026, 1, 10))
        self.client.force_login(self.root)
        url = reverse('reg_construccion:pdf', kwargs={'registro_id': reg.pk})
        html = render_to_string('reportes_construccion/construccion.html', self.client.get(url).context_data)
        self.assertNotIn('Comentarios y Acciones', html)
        self.assertNotIn('<h2>Eléctrico</h2>', html)
        ct = ContentType.objects.get_for_model(RegConstruccion)
        DatoPaso.objects.create(content_type=ct, object_id=reg.id, paso_nombre='obra_comentarios',
                                datos={'entradas': ['Primer párrafo', 'Segundo\npárrafo']})
        html = render_to_string('reportes_construccion/construccion.html', self.client.get(url).context_data)
        self.assertIn('<h2>Comentarios y Acciones</h2>', html)
        self.assertIn('<p>Primer párrafo</p>', html)
        self.assertNotIn('<ol class="lista-numerada"><li>Primer', html)

    def test_libro_de_obras_segunda_camara_en_actividades(self):
        """Actividades tiene 2 botones de cámara (fotos 0/4 y libro de obras) con etapas distintas."""
        from photos.models import Photos
        from reg_construccion.pdf_views import SECCIONES_FOTOS
        reg = self.visita(date(2026, 1, 10))
        self.client.force_login(self.root)
        r = self.client.get(reverse('reg_construccion:steps', kwargs={'registro_id': reg.pk}))
        step = dict(r.context['steps'])['obra_objetivos']
        self.assertEqual(step['elements']['photos']['min_count'], 4)
        extra = step['elements']['photos_extra']
        self.assertEqual([e['slug'] for e in extra], ['camera_libro_widget'])
        self.assertEqual(extra[0]['count'], 0)
        self.assertEqual(extra[0]['color'], 'paso-opcional')  # opcional y vacío
        self.assertEqual(step['elements']['photos']['color'], 'paso-rojo')  # obligatoria (0/4) y vacía
        self.assertEqual(dict(r.context['steps'])['obra_electrico']['elements']['photos']['color'], 'paso-opcional')
        elec = dict(r.context['steps'])['obra_electrico']['elements']
        self.assertEqual(elec['form_widgets'][0]['color'], 'paso-opcional')  # comentario opcional y vacío
        ct = ContentType.objects.get_for_model(RegConstruccion)
        DatoPaso.objects.create(content_type=ct, object_id=reg.id, paso_nombre='obra_electrico',
                                datos={'comentario': 'Empalme listo'})
        r = self.client.get(reverse('reg_construccion:steps', kwargs={'registro_id': reg.pk}))
        self.assertEqual(dict(r.context['steps'])['obra_electrico']['elements']['form_widgets'][0]['color'],
                         'paso-verde')
        self.assertContains(r, 'Libro de obras')
        # la página de la cámara del libro sube a su propia etapa
        r = self.client.get(reverse('reg_construccion:paso_dinamico',
                                    kwargs={'registro_id': reg.pk, 'paso_nombre': 'obra_objetivos'})
                            + '?widget=camera_libro_widget')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['upload_url'], f'/reg_construccion/{reg.pk}/paso/obra_libro/photos/upload/')
        self.assertEqual(r.context['widget_titulo'], 'Libro de obras')
        r = self.client.get(reverse('reg_construccion:paso_dinamico',
                                    kwargs={'registro_id': reg.pk, 'paso_nombre': 'obra_objetivos'})
                            + '?widget=camera_widget')
        self.assertContains(r, '<h1 class="text-lg font-semibold mb-3">Imágenes</h1>', html=False)
        self.assertIn('libro', [k for k, _, _ in SECCIONES_FOTOS])

    def test_imagen_del_libro_se_sube_a_su_etapa_y_sale_en_el_pdf(self):
        import io
        import shutil
        import tempfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        from PIL import Image
        from photos.models import Photos
        reg = self.visita(date(2026, 1, 10))
        buf = io.BytesIO()
        Image.new('RGB', (40, 30), 'white').save(buf, 'JPEG')
        media = tempfile.mkdtemp()
        try:
            with override_settings(MEDIA_ROOT=media):
                self.client.force_login(self.root)
                r = self.client.post(f'/reg_construccion/{reg.pk}/paso/obra_libro/photos/upload/',
                                     {'photos': SimpleUploadedFile('libro.jpg', buf.getvalue(), 'image/jpeg')})
                self.assertEqual(r.status_code, 200, r.content)
                self.assertEqual(Photos.objects.filter(object_id=reg.pk, etapa='obra_libro').count(), 1)
                self.assertEqual(Photos.objects.filter(object_id=reg.pk, etapa='obra_objetivos').count(), 0)
                r = self.client.get(reverse('reg_construccion:pdf', kwargs={'registro_id': reg.pk}))
                self.assertEqual(len(r.context_data['fotos_libro']), 1)
                self.assertEqual(r.context_data['fotos_libro'][0]['descripcion'], 'Fotografía 1')
                self.assertEqual(r.context_data['fotos_actividades'], [])
        finally:
            shutil.rmtree(media, ignore_errors=True)

    def test_dias_transcurridos_desde_la_primera_visita(self):
        primera = self.visita(date(2026, 1, 10))
        segunda = self.visita(date(2026, 1, 25))
        self.client.force_login(self.root)
        for reg, dias in ((primera, 0), (segunda, 15)):
            r = self.client.get(reverse('reg_construccion:pdf', kwargs={'registro_id': reg.pk}))
            self.assertEqual(r.context_data['fecha_inicio'], date(2026, 1, 10))
            self.assertEqual(r.context_data['dias_transcurridos'], dias)

    def test_color_de_la_visita_ignora_los_pasos_opcionales(self):
        """Solo los pasos no opcionales cuentan para pasar de «sin datos» (rojo) a «parcial» (amarillo)."""
        reg = self.visita(date(2026, 1, 10))
        ct = ContentType.objects.get_for_model(RegConstruccion)

        def con_datos():
            return RegConstruccion.objects.with_estado().get(pk=reg.pk).has_widgets

        self.assertFalse(con_datos())
        DatoPaso.objects.create(content_type=ct, object_id=reg.id, paso_nombre='obra_electrico',
                                datos={'comentario': 'Empalme listo'})
        self.assertFalse(con_datos())  # Eléctrico es opcional: no cambia el color
        DatoPaso.objects.create(content_type=ct, object_id=reg.id, paso_nombre='obra_objetivos',
                                datos={'entradas': ['Revisión de izaje']})
        self.assertTrue(con_datos())

    def test_visita_completa_cuando_los_pasos_obligatorios_estan_completos(self):
        """`completo` (fila verde) exige Actividades + 4 imágenes, Ítems y avance y Comentarios; lo opcional no."""
        from photos.models import Photos
        reg = self.visita(date(2026, 1, 10))
        ct = ContentType.objects.get_for_model(RegConstruccion)

        def completo():
            return RegConstruccion.objects.get(pk=reg.pk).completo

        def dato(paso, datos):
            DatoPaso.objects.update_or_create(content_type=ct, object_id=reg.id, paso_nombre=paso,
                                              defaults={'datos': datos})

        self.assertFalse(completo())
        dato('obra_objetivos', {'entradas': ['Revisión de izaje']})
        dato('obra_avance', {'partidas': partidas((100, 10))})
        dato('obra_comentarios', {'entradas': ['Sin novedades']})
        self.assertFalse(completo())  # faltan las 4 imágenes de Actividades
        for _ in range(4):
            Photos.objects.create(content_type=ct, object_id=reg.id, etapa='obra_objetivos', app='reg_construccion',
                                  imagen='photos/x.jpg')
        self.assertTrue(completo())  # Eléctrico y Libro de obras (opcionales) vacíos no impiden el verde
        dato('obra_comentarios', {'entradas': []})
        self.assertFalse(completo())

    def test_fila_verde_si_completo_aunque_no_este_concluida(self):
        from .tables import RegConstruccionTable, SitiosObraTable
        reg = self.visita(date(2026, 1, 10))
        RegConstruccion.objects.filter(pk=reg.pk).update(completo=True)
        record = RegConstruccion.objects.with_estado().get(pk=reg.pk)
        clase = RegConstruccionTable._meta.row_attrs['class'](record)
        self.assertIn('row-concluido', clase)
        sitio = type('S', (), {'ultimo_concluido': False, 'ultimo_completo': True})()
        self.assertIn('row-concluido', SitiosObraTable._meta.row_attrs['class'](sitio))

    def test_solo_la_ultima_visita_puede_crear_una_nueva(self):
        primera = self.visita(date(2026, 1, 10))
        ultima = self.visita(date(2026, 1, 25))
        self.client.force_login(self.root)
        r = self.client.get(reverse('reg_construccion:visitas_sitio', kwargs={'sitio_id': self.torre.pk}),
                            HTTP_HX_REQUEST='true')
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertEqual(html.count('obra-nueva-btn'), 1)          # un solo botón habilitado
        self.assertIn(f'data-id="{ultima.pk}"', html)
        self.assertNotIn('disabled', html)
        self.assertTrue(primera.pk != ultima.pk)

    def test_nueva_visita_de_la_cabecera_solo_en_la_ultima(self):
        primera = self.visita(date(2026, 1, 10))
        ultima = self.visita(date(2026, 1, 25))
        self.client.force_login(self.root)
        for reg, hay_boton in ((primera, False), (ultima, True)):
            r = self.client.get(reverse('reg_construccion:steps', kwargs={'registro_id': reg.pk}))
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.context['es_ultima_visita'], hay_boton)
            self.assertEqual('aria-label="Nuevo reporte"' in r.content.decode(), hay_boton)

    def test_visita_concluida_no_se_puede_eliminar(self):
        concluida = self.visita(date(2026, 1, 10), concluido=True)
        abierta = self.visita(date(2026, 1, 25))
        self.client.force_login(self.root)
        # UI: el panel solo ofrece borrar la visita abierta
        r = self.client.get(reverse('reg_construccion:visitas_sitio', kwargs={'sitio_id': self.torre.pk}),
                            HTTP_HX_REQUEST='true')
        self.assertEqual(r.content.decode().count('obra-delete-btn'), 1)
        # backend: la concluida se rechaza, la abierta se elimina
        self.assertEqual(self.client.post(f'/reg_construccion/api/registros/{concluida.pk}/delete/').status_code, 403)
        concluida.refresh_from_db()
        self.assertFalse(concluida.is_deleted)
        self.assertEqual(self.client.post(f'/reg_construccion/api/registros/{abierta.pk}/delete/').status_code, 200)

    def test_columna_dias_en_la_tabla_de_visitas(self):
        self.visita(date(2026, 1, 10))
        self.visita(date(2026, 1, 25))
        self.client.force_login(self.root)
        r = self.client.get(reverse('reg_construccion:visitas_sitio', kwargs={'sitio_id': self.torre.pk}),
                            HTTP_HX_REQUEST='true')
        tabla = r.context['panel_table']
        self.assertEqual([row.get_cell_value('dias') for row in tabla.rows], [15, 0])  # de la más reciente a la más antigua
        self.assertIn('Días', r.content.decode())

    def test_form_de_edicion_sin_contratista_ni_descripcion(self):
        from .forms import RegConstruccionEditForm
        self.assertEqual(list(RegConstruccionEditForm().fields), ['fecha', 'revision', 'estado_obra'])

    def test_migracion_0004_renombra_sin_pisar_etiquetas_editadas(self):
        import importlib
        from django.apps import apps
        from actividades.models import PasoDefinicion, PasoWidget
        mig = importlib.import_module('reg_construccion.migrations.0004_actividades_inspeccionadas')
        paso = PasoDefinicion.objects.get(nombre='obra_objetivos')
        pw = PasoWidget.objects.get(pasodef=paso, widget_slug='lista_widget')

        # estado antiguo → se renombra título y etiqueta
        paso.titulo = 'Objetivos de la visita'; paso.save()
        pw.config = {**pw.config, 'label': 'Objetivos de la visita'}; pw.save()
        mig.renombrar(apps, None)
        paso.refresh_from_db(); pw.refresh_from_db()
        self.assertEqual((paso.titulo, pw.config['label']), ('Actividades inspeccionadas',) * 2)

        # idempotente y reversible
        mig.renombrar(apps, None)
        mig.revertir(apps, None)
        paso.refresh_from_db(); pw.refresh_from_db()
        self.assertEqual((paso.titulo, pw.config['label']), ('Objetivos de la visita',) * 2)

        # etiqueta editada a mano → se conserva
        pw.config = {**pw.config, 'label': 'Mi etiqueta'}; pw.save()
        mig.renombrar(apps, None)
        paso.refresh_from_db(); pw.refresh_from_db()
        self.assertEqual(paso.titulo, 'Actividades inspeccionadas')
        self.assertEqual(pw.config['label'], 'Mi etiqueta')


class ListadoMaestroDetalleTests(BaseTest):
    """Tabla de sitios arriba (una fila por sitio) y panel de visitas del sitio elegido abajo."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.torre2 = Site.objects.create(pti_cell_id='CL-VS-2000', operator_id='30_1', name='Valparaíso Alto',
                                         tipo_sitio=Site.TORRE)
        cls.admin = User.objects.create_user('admin', 'a@x.cl', 'pw', user_type=User.ADMINISTRADOR)  # global: sin empresa
        cls.visitante = User.objects.create_user('visitante', 'v@x.cl', 'pw', user_type=User.VISITA, contractor=cls.contratista)
        cls.ito3 = User.objects.create_user('ito3', 'i3@x.cl', 'pw', user_type=User.ITO, contractor=cls.otra)

    def visita_en(self, sitio, fecha, **kw):
        kw.setdefault('user', self.ito)
        kw.setdefault('contratista', self.contratista)
        return RegConstruccion.objects.create(sitio=sitio, fecha=fecha, **kw)

    def lista(self, user, **params):
        self.client.force_login(user)
        return self.client.get(reverse('reg_construccion:list'), params)

    def panel(self, user, sitio, **params):
        self.client.force_login(user)
        return self.client.get(reverse('reg_construccion:visitas_sitio', kwargs={'sitio_id': sitio.pk}),
                               params, headers={'HX-Request': 'true'})

    def escenario(self):
        v1 = self.visita_en(self.torre, date(2026, 1, 10))
        v2 = self.visita_en(self.torre, date(2026, 1, 20))
        v3 = self.visita_en(self.torre2, date(2026, 1, 15), user=self.ito3, contratista=self.otra)
        self.guardar_avance(v1, partidas((100, 20)))
        self.guardar_avance(v2, partidas((100, 30)))
        return v1, v2, v3

    # ── tabla de sitios ──────────────────────────────────────────────────────
    def test_una_fila_por_sitio_con_el_resumen_de_su_ultima_visita(self):
        v1, v2, v3 = self.escenario()
        r = self.lista(self.root)
        filas = {s.pk: s for s in r.context['table'].data}
        self.assertEqual(set(filas), {self.torre.pk, self.torre2.pk})
        q = filas[self.torre.pk]
        self.assertEqual((q.n_visitas, q.ultima_fecha, q.ultimo_id), (2, date(2026, 1, 20), v2.pk))
        self.assertEqual(q.ultimo_avance, 50)                       # 20 + 30 acumulado en la última visita
        self.assertEqual(q.ultimo_contratista, 'AJ')                # código del contratista, no el nombre
        self.assertEqual(filas[self.torre2.pk].ultimo_contratista, 'OT')
        self.assertEqual(filas[self.torre2.pk].n_visitas, 1)
        # color de fila según la última visita: con datos → amarillo; sin ningún dato → rojo
        self.assertTrue(q.ultimo_con_datos)
        self.assertFalse(filas[self.torre2.pk].ultimo_con_datos)
        self.assertContains(r, 'row-parcial', count=1)
        self.assertContains(r, 'row-vacio', count=1)
        self.assertNotContains(r, 'row-concluido')
        # orden: la obra con la visita más reciente primero
        self.assertEqual([s.pk for s in r.context['table'].data], [self.torre.pk, self.torre2.pk])
        self.assertContains(r, 'obra-sitio-id', count=2)

    def test_un_sitio_con_todas_sus_visitas_eliminadas_no_aparece(self):
        v1, v2, v3 = self.escenario()
        v3.soft_delete()
        r = self.lista(self.root)
        self.assertEqual([s.pk for s in r.context['table'].data], [self.torre.pk])

    def test_busqueda_por_pti_operador_nombre_y_contratista(self):
        self.escenario()
        for q, esperado in (('1458', {self.torre.pk}), ('30_1', {self.torre2.pk}),
                            ('valpara', {self.torre2.pk}), ('OTRA', {self.torre2.pk}), ('AJ', {self.torre.pk}),
                            ('nada', set())):
            r = self.lista(self.root, q=q)
            self.assertEqual({s.pk for s in r.context['table'].data}, esperado, q)
        # también por el código del contratista
        self.otra.code = 'ZZ9'
        self.otra.save()
        r = self.lista(self.root, q='ZZ9')
        self.assertEqual({s.pk for s in r.context['table'].data}, {self.torre2.pk})

    def test_alcance_por_rol(self):
        self.escenario()
        esperado = {
            self.ito: {self.torre.pk},            # solo donde tiene visitas
            self.ito3: {self.torre2.pk},
            self.coord: {self.torre.pk},          # administrador de empresa: su contratista
            self.admin: {self.torre.pk, self.torre2.pk},
            self.visitante: {self.torre.pk, self.torre2.pk},
            self.root: {self.torre.pk, self.torre2.pk},
        }
        for user, sitios in esperado.items():
            r = self.lista(user)
            self.assertEqual({s.pk for s in r.context['table'].data}, sitios, user.username)

    def test_las_visitas_de_otro_ito_no_cuentan_para_su_resumen(self):
        self.visita_en(self.torre, date(2026, 1, 10))
        self.visita_en(self.torre, date(2026, 1, 25), user=self.ito2)   # visita de otro ITO
        fila = self.lista(self.ito).context['table'].data[0]
        self.assertEqual((fila.n_visitas, fila.ultima_fecha), (1, date(2026, 1, 10)))

    # ── selección y panel ────────────────────────────────────────────────────
    def test_sitio_en_la_url_preselecciona_y_uno_ajeno_se_ignora(self):
        self.escenario()
        r = self.lista(self.root, sitio=self.torre2.pk)
        self.assertEqual(r.context['sitio_sel'], self.torre2.pk)
        self.assertEqual([v.sitio_id for v in r.context['panel_page'].object_list], [self.torre2.pk])
        # sin ?sitio= y con varios sitios: nada seleccionado
        self.assertIsNone(self.lista(self.root).context['sitio_sel'])
        self.assertNotIn('panel_sitio', self.lista(self.root).context)
        # un sitio que el usuario no ve se ignora (con 2 sitios visibles no hay autoselección)
        self.assertIsNone(self.lista(self.admin, sitio=999999).context['sitio_sel'])

    def test_con_un_solo_sitio_se_preselecciona(self):
        self.escenario()
        r = self.lista(self.ito)
        self.assertEqual(r.context['sitio_sel'], self.torre.pk)
        self.assertEqual(len(r.context['panel_table'].rows), 2)
        # pedir un sitio ajeno no filtra datos: se queda con el único visible
        self.assertEqual(self.lista(self.ito, sitio=self.torre2.pk).context['sitio_sel'], self.torre.pk)

    def test_panel_htmx_solo_trae_las_visitas_del_sitio_de_la_mas_reciente_a_la_mas_antigua(self):
        v1, v2, v3 = self.escenario()
        r = self.panel(self.root, self.torre)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'reg_construccion/partials/visitas_sitio.html')
        self.assertEqual([v.pk for v in r.context['panel_page'].object_list], [v2.pk, v1.pk])
        self.assertEqual([v.n_visita for v in r.context['panel_page'].object_list], [2, 1])
        self.assertEqual(r.context['panel_total'], 2)
        self.assertContains(r, 'obra-row-id', count=2)

    def test_panel_sin_htmx_redirige_al_listado_con_el_sitio(self):
        self.escenario()
        self.client.force_login(self.root)
        r = self.client.get(reverse('reg_construccion:visitas_sitio', kwargs={'sitio_id': self.torre.pk}))
        self.assertRedirects(r, f"{reverse('reg_construccion:list')}?sitio={self.torre.pk}",
                             fetch_redirect_response=False)

    def test_panel_de_un_sitio_fuera_del_alcance_da_404(self):
        self.escenario()
        self.assertEqual(self.panel(self.ito, self.torre2).status_code, 404)
        self.assertEqual(self.panel(self.coord, self.torre2).status_code, 404)

    def test_panel_pagina_de_a_10_con_enlaces_explicitos(self):
        for i in range(12):
            self.visita_en(self.torre, date(2026, 2, 1) + timedelta(days=i))
        r1 = self.panel(self.root, self.torre)
        self.assertEqual(len(r1.context['panel_page'].object_list), 10)
        self.assertContains(r1, f"{reverse('reg_construccion:visitas_sitio', kwargs={'sitio_id': self.torre.pk})}?page=2")
        r2 = self.panel(self.root, self.torre, page=2)
        self.assertEqual(len(r2.context['panel_page'].object_list), 2)
        # el N° de visita cuenta sobre TODAS las del sitio, no solo la página
        self.assertEqual([v.n_visita for v in r2.context['panel_page'].object_list], [2, 1])

    def test_panel_filtra_por_fechas_sin_cambiar_el_numero_de_visita(self):
        self.visita_en(self.torre, date(2026, 1, 10))
        self.visita_en(self.torre, date(2026, 2, 10))
        self.visita_en(self.torre, date(2026, 3, 10))
        r = self.panel(self.root, self.torre, desde='2026-02-01', hasta='2026-02-28')
        visitas = list(r.context['panel_page'].object_list)
        self.assertEqual([(v.fecha, v.n_visita) for v in visitas], [(date(2026, 2, 10), 2)])
        self.assertEqual((r.context['panel_total'], r.context['panel_page'].paginator.count), (3, 1))
        # fechas inválidas se ignoran
        self.assertEqual(len(self.panel(self.root, self.torre, desde='x').context['panel_page'].object_list), 3)

    def test_atras_de_la_visita_vuelve_al_sitio(self):
        v = self.visita_en(self.torre, date(2026, 1, 10))
        self.client.force_login(self.root)
        r = self.client.get(reverse('reg_construccion:steps', kwargs={'registro_id': v.pk}))
        self.assertEqual(r.context['back_url'], f"{reverse('reg_construccion:list')}?sitio={self.torre.pk}")

    # ── rendimiento ──────────────────────────────────────────────────────────
    def test_las_consultas_no_crecen_con_el_numero_de_sitios_ni_de_visitas(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        self.escenario()

        def consultas():
            with CaptureQueriesContext(connection) as c:
                self.lista(self.root)
            return len(c)

        antes = consultas()
        for i in range(4):
            s = Site.objects.create(pti_cell_id=f'X-{i}', operator_id=str(i), name=f'Extra {i}', tipo_sitio=Site.TORRE)
            for d in range(3):
                self.visita_en(s, date(2026, 3, 1) + timedelta(days=d))
        self.assertEqual(consultas(), antes)

    def test_color_de_fila_verde_si_la_ultima_visita_esta_concluida(self):
        # dos sitios para que el panel de visitas no se preseleccione (y no sume sus propias filas)
        for sitio in (self.torre, self.torre2):
            v = self.visita_en(sitio, date(2026, 1, 10))
            RegConstruccion.objects.filter(pk=v.pk).update(concluido=True)
        r = self.lista(self.root)
        self.assertContains(r, 'row-concluido', count=2)
        self.assertNotContains(r, 'row-parcial')
        self.assertNotContains(r, 'row-vacio')


class AccesoSitiosEmpresasImagenesTests(BaseTest):
    """Sitios y Empresas solo para superusuario y ADMINISTRADOR; las imágenes, solo las propias."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin = User.objects.create_user('adm', 'adm@x.cl', 'pw', user_type=User.ADMINISTRADOR)
        cls.searcher = User.objects.create_user('bus', 'b@x.cl', 'pw', user_type=User.SEARCHER, contractor=cls.contratista)
        cls.visitante = User.objects.create_user('vis', 'v@x.cl', 'pw', user_type=User.VISITA, contractor=cls.contratista)

    def _menu(self, user):
        from django.test import RequestFactory
        from core.menu.menu_builder import MenuBuilder
        request = RequestFactory().get('/')
        request.user = user
        request.session = {}
        return {item.name for item in MenuBuilder.get_menu(user, '/', request)}

    def test_menu_sitios_y_empresas_solo_super_y_admin(self):
        for user in (self.root, self.admin):
            self.assertTrue({'Sitios', 'Empresas'} <= self._menu(user), user.username)
        for user in (self.coord, self.ito, self.searcher, self.visitante):
            self.assertFalse({'Sitios', 'Empresas'} & self._menu(user), user.username)

    def test_paginas_de_sitios_y_empresas_bloquean_a_los_demas(self):
        urls = [reverse('sitios:sitios_list'), reverse('contractors:contractors_list')]
        for user in (self.root, self.admin):
            self.client.force_login(user)
            for url in urls:
                self.assertEqual(self.client.get(url).status_code, 200, (user.username, url))
        for user in (self.coord, self.ito, self.searcher, self.visitante):
            self.client.force_login(user)
            for url in urls:
                self.assertEqual(self.client.get(url).status_code, 302, (user.username, url))
            # la API de contratistas también (JSON 403)
            self.assertEqual(self.client.get(reverse('contractors:contractors_api')).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(urls[0]).status_code, 302)  # anónimo → login

    def test_imagenes_solo_las_de_mis_reportes(self):
        from photos.models import Photos
        from photos.views import _photos_visibles
        mio = self.visita(date(2026, 1, 10), user=self.ito)
        ajeno = self.visita(date(2026, 1, 25), user=self.ito2)
        ct = ContentType.objects.get_for_model(RegConstruccion)
        foto_mia = Photos.objects.create(content_type=ct, object_id=mio.pk, etapa='obra_objetivos',
                                         app='reg_construccion', imagen='photos/a.jpg')
        foto_ajena = Photos.objects.create(content_type=ct, object_id=ajeno.pk, etapa='obra_objetivos',
                                           app='reg_construccion', imagen='photos/b.jpg')
        self.assertEqual(set(_photos_visibles(self.ito).values_list('pk', flat=True)), {foto_mia.pk})
        self.assertEqual(set(_photos_visibles(self.ito2).values_list('pk', flat=True)), {foto_ajena.pk})
        # administrador de empresa: los reportes de su empresa (ambos ITO son de AJ)
        self.assertEqual(set(_photos_visibles(self.coord).values_list('pk', flat=True)), {foto_mia.pk, foto_ajena.pk})
        self.assertEqual(set(_photos_visibles(self.visitante).values_list('pk', flat=True)), {foto_mia.pk, foto_ajena.pk})
        for user in (self.root, self.admin):
            self.assertEqual(set(_photos_visibles(user).values_list('pk', flat=True)), {foto_mia.pk, foto_ajena.pk})


class DashboardConstruccionTests(BaseTest):
    """Dashboard de inicio (solo Construcción): KPIs, alcance por rol, mapa y usuarios sin acceso."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        hoy = date.today()
        self.torre2 = Site.objects.create(pti_cell_id='CL-VS-2', operator_id='2', name='Dos',
                                          tipo_sitio=Site.TORRE, lat_ing=-33.0, lon_ing=-71.0)
        # torre 1 (sin coordenadas): 2 visitas, la última al 60 % y paralizada, hace 20 días
        self.visita(hoy - timedelta(days=40))
        ultima = self.visita(hoy - timedelta(days=20), estado_obra='paralizado')
        # torre 2: una visita reciente de otro ITO, en construcción al 30 %
        otra = RegConstruccion.objects.create(sitio=self.torre2, fecha=hoy - timedelta(days=2), user=self.ito2,
                                              contratista=self.otra)
        # las señales recalculan avance_pct desde las partidas: se fija con update()
        RegConstruccion.objects.filter(pk=ultima.pk).update(avance_pct=60)
        RegConstruccion.objects.filter(pk=otra.pk).update(avance_pct=30)

    def test_panel_usa_la_ultima_visita_de_cada_sitio(self):
        from . import dashboard
        p = dashboard.panel(self.root)
        k = p['kpis']
        self.assertEqual((k['torres'], k['en_obra'], k['total_visitas']), (2, 1, 3))
        self.assertEqual(k['avance_global'], 45.0)  # (60 + 30) / 2
        self.assertEqual(k['avance_en_obra'], 30.0)  # solo la torre 2 está en construcción
        self.assertEqual(k['visitas_30'], 2)
        self.assertEqual({e['codigo']: e['n'] for e in p['estados']},
                         {'construccion': 1, 'paralizado': 1, 'cancelado': 0, 'concluido': 0})
        self.assertEqual([c['codigo'] for c in p['contratistas']], ['AJ', 'OT'])
        self.assertEqual([r['n'] for r in p['rangos']], [0, 1, 1, 0])  # 30 % y 60 %

    def test_sin_visita_reciente_solo_obras_en_curso(self):
        from . import dashboard
        RegConstruccion.objects.filter(sitio=self.torre2).update(fecha=date.today() - timedelta(days=30))
        p = dashboard.panel(self.root)
        self.assertEqual([f['id'] for f in p['sin_visita_reciente']], [self.torre2.id])
        self.assertEqual(p['sin_visita_reciente'][0]['dias_sin_visita'], 30)
        self.assertEqual(p['kpis']['sin_visita'], 1)  # la torre 1 está paralizada: no cuenta

    def test_alcance_por_rol(self):
        from . import dashboard
        self.assertEqual(dashboard.panel(self.root)['kpis']['total_visitas'], 3)
        self.assertEqual(dashboard.panel(self.ito)['kpis']['total_visitas'], 2)
        self.assertEqual(dashboard.panel(self.ito2)['kpis']['total_visitas'], 1)
        self.assertEqual(dashboard.panel(self.coord)['kpis']['total_visitas'], 3)  # su empresa (AJ): ito + ito2
        self.assertEqual(len(dashboard.actividad_reciente(self.ito)), 2)

    def test_mapa_omite_sitios_sin_coordenadas_y_respeta_el_alcance(self):
        from django.core.cache import cache
        cache.clear()
        url = reverse('reg_construccion:api_mapa_dashboard')
        self.client.force_login(self.root)
        feats = self.client.get(url).json()['features']
        self.assertEqual([f['properties']['pti'] for f in feats], ['CL-VS-2'])
        self.assertEqual(feats[0]['geometry']['coordinates'], [-71.0, -33.0])
        self.client.force_login(self.ito)  # el ITO no tiene visitas en la torre 2
        self.assertEqual(self.client.get(url).json()['features'], [])

    def test_mapa_prohibido_sin_acceso_al_reporte(self):
        otro = User.objects.create_user('otro', 'o@x.cl', 'pw', user_type=User.ITO, contractor=self.contratista,
                                        report_access=['txtss_postes'])
        self.client.force_login(otro)
        self.assertEqual(self.client.get(reverse('reg_construccion:api_mapa_dashboard')).status_code, 403)

    def test_inicio_renderiza_y_sin_acceso_muestra_bienvenida(self):
        self.client.force_login(self.root)
        r = self.client.get(reverse('dashboard:dashboard'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Avance por contratista')
        otro = User.objects.create_user('otro', 'o@x.cl', 'pw', user_type=User.ITO, contractor=self.contratista,
                                        report_access=['txtss_postes'])
        self.client.force_login(otro)
        r = self.client.get(reverse('dashboard:dashboard'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Bienvenido')
        self.assertNotContains(r, 'Avance por contratista')
