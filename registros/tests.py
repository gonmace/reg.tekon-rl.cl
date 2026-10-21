"""
Registro concluido: PDF siempre disponible (borrador/final), bloqueo de edición y
quién puede concluir/reabrir. Se prueba igual para TX/TSS y Construcción Sitios.
"""
import datetime
import json

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.urls import reverse

from actividades.models import ConfigPaso, DatoPaso, PasoDefinicion, PasoWidget, TipoActividad
from core.models.contractors import Contractor
from core.models.sites import Site
from reg_construccion.models import RegConstruccion
from reg_txtss.models import RegTxtss
from users.models import User

PLAIN_STATIC = {
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
}


class ConcluidoMixin:
    """Casos comunes. Cada clase concreta define namespace, paso/widget y make_registro()."""
    ns = None            # namespace de URLs == prefijo
    paso = None          # paso con un lista_widget
    model = None

    @classmethod
    def setUpTestData(cls):
        cls.empresa = Contractor.objects.create(name='AJ', code='AJ')
        cls.root = User.objects.create_superuser('root', 'r@x.cl', 'pw', user_type='')
        cls.admin = User.objects.create_user('admin', 'a@x.cl', 'pw', user_type=User.ADMINISTRADOR, contractor=cls.empresa)
        cls.coord = User.objects.create_user('coord', 'c@x.cl', 'pw', user_type=User.COORD, contractor=cls.empresa)
        cls.ito = User.objects.create_user('ito', 'i@x.cl', 'pw', user_type=User.ITO, contractor=cls.empresa)
        cls.visita = User.objects.create_user('visita', 'v@x.cl', 'pw', user_type=User.VISITA, contractor=cls.empresa)
        cls.preparar()
        cls.reg = cls.make_registro(cls.ito)

    @classmethod
    def preparar(cls):
        pass

    def url(self, name, **kw):
        kw.setdefault('registro_id', self.reg.pk)
        return reverse(f'{self.ns}:{name}', kwargs=kw)

    def recargar(self):
        self.reg.refresh_from_db()
        return self.reg

    def alternar(self, user):
        self.client.force_login(user)
        return self.client.post(self.url('api_toggle_concluido'))

    def concluir(self):
        self.model.objects.filter(pk=self.reg.pk).update(concluido=True)

    # ── quién puede concluir / reabrir ───────────────────────────────────────
    def test_ito_concluye_pero_no_reabre(self):
        self.assertEqual(self.alternar(self.ito).status_code, 200)
        self.assertTrue(self.recargar().concluido)
        r = self.alternar(self.ito)
        self.assertEqual(r.status_code, 403)
        self.assertIn('reabrir', r.json()['message'])
        self.assertTrue(self.recargar().concluido)

    def test_administrador_y_superusuario_reabren(self):
        for reabre in (self.admin, self.root):
            self.concluir()
            r = self.alternar(reabre)
            self.assertEqual(r.status_code, 200, reabre.username)
            self.assertFalse(self.recargar().concluido)

    def test_superusuario_tambien_puede_concluir(self):
        self.assertEqual(self.alternar(self.root).status_code, 200)
        self.assertTrue(self.recargar().concluido)

    def test_coord_y_visita_no_cambian_el_estado(self):
        for user in (self.coord, self.visita):
            self.assertEqual(self.alternar(user).status_code, 403, user.username)
        self.assertFalse(self.recargar().concluido)
        self.concluir()
        for user in (self.coord, self.visita):
            self.assertEqual(self.alternar(user).status_code, 403, user.username)
        self.assertTrue(self.recargar().concluido)

    # ── bloqueo ──────────────────────────────────────────────────────────────
    def post_paso(self, user, texto):
        self.client.force_login(user)
        return self.client.post(
            self.url('paso_dinamico', paso_nombre=self.paso) + '?widget=lista_widget',
            {'entradas': json.dumps([texto])})

    def entradas(self):
        ct = ContentType.objects.get_for_model(self.model)
        d = DatoPaso.objects.filter(content_type=ct, object_id=self.reg.pk, paso_nombre=self.paso).first()
        return (d.datos.get('entradas') if d else None) or []

    def test_editable_mientras_no_esta_concluido(self):
        self.assertEqual(self.post_paso(self.ito, 'uno').status_code, 302)
        self.assertEqual(self.entradas(), ['uno'])

    def test_concluido_bloquea_el_formulario_incluso_al_superusuario(self):
        self.post_paso(self.ito, 'uno')
        self.concluir()
        for user in (self.ito, self.root):
            r = self.post_paso(user, 'cambio')
            self.assertEqual(r.status_code, 302, user.username)  # vuelve a los pasos con un aviso
            self.assertEqual(self.entradas(), ['uno'], user.username)
        # reabierto vuelve a ser editable
        self.alternar(self.root)
        self.assertEqual(self.post_paso(self.ito, 'dos').status_code, 302)
        self.assertEqual(self.entradas(), ['dos'])

    def test_concluido_bloquea_subida_de_fotos(self):
        self.concluir()
        for user in (self.ito, self.root):
            self.client.force_login(user)
            r = self.client.post(f'/{self.ns}/{self.reg.pk}/paso/{self.paso}/photos/upload/')
            self.assertEqual(r.status_code, 403, user.username)
            self.assertTrue(r.json()['locked'])

    def test_pagina_del_paso_es_solo_lectura(self):
        self.client.force_login(self.ito)
        url = self.url('paso_dinamico', paso_nombre=self.paso) + '?widget=lista_widget'
        self.assertContains(self.client.get(url), 'Guardar')
        self.concluir()
        r = self.client.get(url)
        self.assertContains(r, 'solo lectura')
        self.assertNotContains(r, 'Guardar')

    # ── interfaz de la página de pasos ───────────────────────────────────────
    def test_switch_de_concluido_segun_rol(self):
        self.client.force_login(self.ito)
        r = self.client.get(self.url('steps'))
        self.assertContains(r, 'id="toggle-concluido"')
        self.assertContains(r, 'Borrador')
        self.concluir()
        # ITO ya no puede reabrir: sin switch, con candado
        self.assertNotContains(self.client.get(self.url('steps')), 'id="toggle-concluido"')
        for user in (self.admin, self.root):
            self.client.force_login(user)
            self.assertContains(self.client.get(self.url('steps')), 'id="toggle-concluido"', msg_prefix=user.username)

    # ── PDF siempre disponible ───────────────────────────────────────────────
    def test_pdf_sin_concluir_sale_como_borrador(self):
        self.client.force_login(self.ito)
        r = self.client.get(self.url('pdf'))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.content.startswith(b'%PDF'))
        self.assertTrue(r.context_data['borrador'])
        self.assertIn('BORRADOR', r.headers['Content-Disposition'])

    def test_pdf_concluido_sale_sin_marca_de_agua(self):
        self.concluir()
        self.client.force_login(self.ito)
        r = self.client.get(self.url('pdf'))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.context_data['borrador'])
        self.assertNotIn('BORRADOR', r.headers['Content-Disposition'])


@override_settings(STORAGES=PLAIN_STATIC)
class TxtssConcluidoTests(ConcluidoMixin, TestCase):
    ns = 'reg_txtss'
    paso = 'prueba'
    model = RegTxtss
    ct_label = 'reg_txtss.regtxtss'

    @classmethod
    def preparar(cls):
        cls.sitio = Site.objects.create(pti_cell_id='P-1', operator_id='1', name='Poste', tipo_sitio=Site.POSTE)
        tipo = TipoActividad.objects.create(nombre='TX/TSS Postes', app_namespace='reg_txtss_postes', tipo_sitio='POSTE')
        paso = PasoDefinicion.objects.create(nombre='prueba', titulo='Prueba')
        PasoWidget.objects.create(pasodef=paso, widget_slug='lista_widget', orden=1, config={})
        ConfigPaso.objects.create(tipo=tipo, pasodef=paso, orden=1)

    @classmethod
    def make_registro(cls, user):
        return RegTxtss.objects.create(sitio=cls.sitio, user=user, fecha=datetime.date(2026, 1, 1), alternativa='A')

    def test_no_se_edita_fecha_ni_alternativa_si_esta_concluido(self):
        self.concluir()
        self.client.force_login(self.root)
        r = self.client.post(self.url('api_update_alternativa'), data=json.dumps({'alternativa': 'B'}),
                             content_type='application/json')
        self.assertEqual(r.status_code, 403)
        self.client.force_login(self.ito)
        r = self.client.post(self.url('api_update_fecha'), data=json.dumps({'fecha': '2026-02-02'}),
                             content_type='application/json')
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.recargar().fecha, datetime.date(2026, 1, 1))


@override_settings(STORAGES=PLAIN_STATIC)
class ConstruccionConcluidoTests(ConcluidoMixin, TestCase):
    ns = 'reg_construccion'
    paso = 'obra_objetivos'
    model = RegConstruccion
    ct_label = 'reg_construccion.regconstruccion'

    @classmethod
    def preparar(cls):
        cls.sitio = Site.objects.create(pti_cell_id='T-1', operator_id='1', name='Torre', tipo_sitio=Site.TORRE)

    @classmethod
    def make_registro(cls, user):
        return RegConstruccion.objects.create(
            sitio=cls.sitio, user=user, fecha=datetime.date(2026, 1, 1), contratista=cls.empresa)

    def test_no_se_edita_la_cabecera_si_esta_concluido(self):
        self.concluir()
        self.client.force_login(self.root)
        r = self.client.post(self.url('api_update'), {
            'fecha': '2026-01-01', 'proyecto': 'Cambio', 'revision': 1, 'estado_obra': 'construccion'})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.recargar().proyecto, '')
