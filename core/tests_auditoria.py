"""Regresiones de la auditoría pre-deploy: permisos de usuarios, fotos, ítems de avance y visitas concluidas."""
import datetime
import io
import json
import tempfile
import zipfile
from types import SimpleNamespace

from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from core.models.contractors import Contractor
from core.models.permisos import PermisoRol, PermisoUsuario
from core.models.sites import Site
from core.templatetags.access_tags import btn_access
from photos.models import Photos
from reg_construccion.models import RegConstruccion
from reg_construccion.permissions import hay_posterior_concluida
from users.models import User
from widgets.registry import get_widget

PLAIN_STATIC = {
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
}
MEDIA = tempfile.mkdtemp(prefix='tekon-tests-')


def jpeg(nombre='foto.jpg'):
    buffer = io.BytesIO()
    Image.new('RGB', (40, 30), 'red').save(buffer, 'JPEG')
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type='image/jpeg')


class Base(TestCase):
    def setUp(self):
        # el mapa de permisos por rol está en caché y la transacción del test no lo invalida al revertir
        cache.clear()
        self.addCleanup(cache.clear)

    @classmethod
    def setUpTestData(cls):
        cls.empresa = Contractor.objects.create(name='AJ', code='AJ')
        cls.otra = Contractor.objects.create(name='Otra', code='OT')
        cls.root = User.objects.create_superuser('root', 'r@x.cl', 'pw', user_type='')
        cls.admin_emp = User.objects.create_user('admin_emp', 'c@x.cl', 'pw', user_type=User.ADMINISTRADOR, contractor=cls.empresa)
        cls.admin_otra = User.objects.create_user('admin_otra', 'c2@x.cl', 'pw', user_type=User.ADMINISTRADOR, contractor=cls.otra)
        cls.admin_global = User.objects.create_user('admin_global', 'a@x.cl', 'pw', user_type=User.ADMINISTRADOR)
        cls.ito = User.objects.create_user('ito', 'i@x.cl', 'pw', user_type=User.ITO, contractor=cls.empresa)
        cls.ito_otra = User.objects.create_user('ito2', 'i2@x.cl', 'pw', user_type=User.ITO, contractor=cls.otra)

    def api(self, user, method, user_id, body=None):
        self.client.force_login(user)
        url = reverse('users:api_detail', kwargs={'user_id': user_id})
        return getattr(self.client, method)(url, json.dumps(body or {}), content_type='application/json')


class UsuariosPermisosTests(Base):
    def test_admin_empresa_no_puede_tomar_una_cuenta_superusuario(self):
        r = self.api(self.admin_emp, 'put', self.root.pk, {'user_type': 'ITO', 'password': 'Un-Clave-Larga-93'})
        self.assertEqual(r.status_code, 403)
        self.root.refresh_from_db()
        self.assertFalse(self.root.check_password('Un-Clave-Larga-93'))
        self.assertEqual(self.root.user_type, '')

    def test_admin_empresa_no_modifica_ni_elimina_usuarios_de_otra_empresa(self):
        self.assertEqual(self.api(self.admin_emp, 'put', self.ito_otra.pk, {'first_name': 'X'}).status_code, 403)
        self.assertEqual(self.api(self.admin_emp, 'delete', self.ito_otra.pk).status_code, 403)
        self.assertEqual(self.api(self.admin_emp, 'put', self.admin_otra.pk, {'user_type': 'ITO'}).status_code, 403)
        self.ito_otra.refresh_from_db()
        self.assertFalse(self.ito_otra.is_deleted)

    def test_admin_empresa_gestiona_ito_de_su_empresa(self):
        self.assertEqual(self.api(self.admin_emp, 'put', self.ito.pk, {'first_name': 'Ana'}).status_code, 200)
        self.assertEqual(self.api(self.admin_emp, 'delete', self.ito.pk).status_code, 200)
        self.ito.refresh_from_db()
        self.assertTrue(self.ito.is_deleted)

    def test_modal_de_edicion_respeta_el_mismo_alcance(self):
        self.client.force_login(self.admin_emp)
        self.assertEqual(self.client.get(reverse('users:edit_modal', kwargs={'user_id': self.root.pk})).status_code, 403)
        self.assertEqual(self.client.get(reverse('users:edit_modal', kwargs={'user_id': self.ito.pk})).status_code, 200)

    def test_superusuario_sigue_pudiendo_y_no_se_elimina_a_si_mismo(self):
        self.assertEqual(self.api(self.root, 'put', self.ito_otra.pk, {'first_name': 'Z'}).status_code, 200)
        self.assertEqual(self.api(self.root, 'delete', self.root.pk).status_code, 403)

    def test_admin_empresa_solo_ve_usuarios_de_su_empresa(self):
        self.client.force_login(self.admin_emp)
        r = self.client.get(reverse('users:list'))
        usernames = {u.username for u in r.context['table'].data}
        self.assertIn('ito', usernames)
        self.assertNotIn('ito2', usernames)
        self.assertNotIn('root', usernames)

    def test_admin_empresa_crea_siempre_en_su_empresa_y_valida_la_contrasena(self):
        self.client.force_login(self.admin_emp)
        url = reverse('users:api')
        r = self.client.post(url, json.dumps({'username': 'n@x.cl', 'password': '123', 'user_type': 'ITO'}),
                             content_type='application/json')
        self.assertEqual(r.status_code, 400)
        r = self.client.post(url, json.dumps({'username': 'n@x.cl', 'password': 'Una-Clave-Larga-93', 'user_type': 'ITO'}),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(User.objects.get(username='n@x.cl').contractor, self.empresa)


@override_settings(STORAGES=PLAIN_STATIC, MEDIA_ROOT=MEDIA)
class ConstruccionBase(Base):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sitio = Site.objects.create(pti_cell_id='T-1', operator_id='1', name='Torre', tipo_sitio=Site.TORRE)
        cls.v1 = cls.visita(datetime.date(2026, 1, 1))

    @classmethod
    def visita(cls, fecha, concluido=False):
        return RegConstruccion.objects.create(
            sitio=cls.sitio, user=cls.ito, fecha=fecha, contratista=cls.empresa, concluido=concluido)

    def foto(self, registro):
        return Photos.objects.create(
            content_type=ContentType.objects.get_for_model(RegConstruccion), object_id=registro.pk,
            app='reg_construccion', etapa='obra_objetivos', imagen=jpeg())


class FotosTests(ConstruccionBase):
    def subir(self, user, registro):
        self.client.force_login(user)
        return self.client.post(f'/reg_construccion/{registro.pk}/paso/obra_objetivos/photos/upload/', {'photos': jpeg()})

    def test_admin_de_la_empresa_sube_fotos_en_construccion(self):
        r = self.subir(self.admin_emp, self.v1)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(Photos.objects.filter(object_id=self.v1.pk).count(), 1)

    def test_admin_de_otra_empresa_e_ito_ajeno_no_suben(self):
        for user in (self.admin_otra, self.ito_otra):
            self.assertEqual(self.subir(user, self.v1).status_code, 403, user.username)

    def test_admin_global_sube(self):
        self.assertEqual(self.subir(self.admin_global, self.v1).status_code, 200)

    def test_sin_el_permiso_cargar_datos_no_suben(self):
        PermisoRol.objects.create(rol='ITO', accion='cargar_datos', permitido=False)
        self.assertEqual(self.subir(self.ito, self.v1).status_code, 403)
        PermisoUsuario.objects.create(user=self.ito, accion='cargar_datos', permitido=True)  # la excepción manda
        self.assertEqual(self.subir(User.objects.get(pk=self.ito.pk), self.v1).status_code, 200)

    def test_ito_dueno_y_superusuario_suben(self):
        for user in (self.ito, self.root):
            self.assertEqual(self.subir(user, self.v1).status_code, 200, user.username)

    def test_descarga_masiva_solo_de_fotos_visibles(self):
        foto = self.foto(self.v1)
        url = reverse('photos:bulk_download')
        for user, esperado in ((self.ito_otra, 0), (self.ito, 1), (self.root, 1)):
            self.client.force_login(user)
            r = self.client.post(url, json.dumps({'ids': [foto.pk]}), content_type='application/json')
            self.assertEqual(r.status_code, 200)
            nombres = zipfile.ZipFile(io.BytesIO(b''.join(r.streaming_content))).namelist()
            self.assertEqual(len(nombres), esperado, user.username)

    def test_borrado_y_compresion_masivos_respetan_el_registro_concluido(self):
        concluida = self.visita(datetime.date(2026, 3, 1), concluido=True)
        foto = self.foto(concluida)
        self.client.force_login(self.root)
        for name in ('photos:bulk_delete', 'photos:compress'):
            r = self.client.post(reverse(name), json.dumps({'ids': [foto.pk]}), content_type='application/json')
            self.assertEqual(r.status_code, 403, name)
        self.assertTrue(Photos.objects.filter(pk=foto.pk).exists())


class TablaAvanceRolesTests(TestCase):
    def before_save(self, user, cleaned, stored):
        request = SimpleNamespace(user=user)
        get_widget('tabla_avance_widget').before_save(cleaned, stored, request, None, None, {})
        return cleaned

    def test_sin_cargar_datos_define_items_pero_no_carga_el_porcentaje(self):
        admin = User.objects.create_user('adm', 'a@x.cl', 'pw', user_type=User.ADMINISTRADOR)
        PermisoUsuario.objects.create(user=admin, accion='cargar_datos', permitido=False)
        stored = {'partidas': [{'id': 'a', 'nombre': 'Uno', 'incidencia': 100, 'actual': 10}]}
        cleaned = {'partidas': [
            {'id': 'a', 'nombre': 'Uno', 'incidencia': 60, 'actual': 55},
            {'id': 'b', 'nombre': 'Nuevo', 'incidencia': 40, 'actual': 90},
        ]}
        partidas = self.before_save(admin, cleaned, stored)['partidas']
        self.assertEqual([(p['id'], p['incidencia'], p['actual']) for p in partidas], [('a', 60, 10), ('b', 40, 0.0)])

    def test_administrador_define_items_y_carga_el_porcentaje(self):
        admin = User(user_type=User.ADMINISTRADOR)
        cleaned = {'partidas': [{'id': 'a', 'nombre': 'Uno', 'incidencia': 100, 'actual': 55}]}
        partidas = self.before_save(admin, cleaned, {'partidas': []})['partidas']
        self.assertEqual(partidas[0]['actual'], 55)

    def test_superusuario_conserva_lo_enviado(self):
        cleaned = {'partidas': [{'id': 'a', 'nombre': 'Uno', 'incidencia': 100, 'actual': 55}]}
        partidas = self.before_save(User(user_type=''), cleaned, {'partidas': []})['partidas']
        self.assertEqual(partidas[0]['actual'], 55)


class VisitaAnteriorAConcluidaTests(ConstruccionBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.v2 = cls.visita(datetime.date(2026, 2, 1), concluido=True)

    def test_helper(self):
        self.assertTrue(hay_posterior_concluida(self.v1))
        self.assertFalse(hay_posterior_concluida(self.v2))
        self.assertTrue(hay_posterior_concluida(self.v2, datetime.date(2025, 1, 1)))

    def test_no_se_edita_el_avance_de_la_visita_anterior(self):
        self.client.force_login(self.ito)
        url = reverse('reg_construccion:paso_dinamico', kwargs={'registro_id': self.v1.pk, 'paso_nombre': 'obra_avance'})
        r = self.client.post(url + '?widget=tabla_avance_widget', {'partidas': '[]'})
        self.assertEqual(r.status_code, 403)
        # sin visita posterior concluida sí se puede
        self.v2.concluido = False
        self.v2.save()
        r = self.client.post(url + '?widget=tabla_avance_widget', {'partidas': '[]'})
        self.assertNotEqual(r.status_code, 403)

    def test_no_se_cambia_la_fecha_ni_se_elimina_la_visita_anterior(self):
        self.client.force_login(self.root)
        r = self.client.post(reverse('reg_construccion:api_update', kwargs={'registro_id': self.v1.pk}), {
            'fecha': '2026-01-05', 'proyecto': '', 'revision': 1, 'estado_obra': 'construccion'})
        self.assertEqual(r.status_code, 403)
        r = self.client.post(reverse('reg_construccion:api_delete', kwargs={'registro_id': self.v1.pk}))
        self.assertEqual(r.status_code, 403)
        self.v1.refresh_from_db()
        self.assertEqual(self.v1.fecha, datetime.date(2026, 1, 1))
        self.assertFalse(self.v1.is_deleted)

    def test_no_se_crea_una_visita_con_fecha_anterior_a_una_concluida(self):
        self.client.force_login(self.ito)
        url = reverse('reg_construccion:api_nueva_visita', kwargs={'registro_id': self.v2.pk})
        r = self.client.post(url, json.dumps({'fecha': '2026-01-15'}), content_type='application/json')
        self.assertEqual(r.status_code, 403)
        r = self.client.post(url, json.dumps({'fecha': '2026-03-15'}), content_type='application/json')
        self.assertEqual(r.status_code, 200, r.content)


class BtnAccessTests(TestCase):
    def acceso(self, user, **extra):
        return btn_access({'request': SimpleNamespace(user=user), **extra})

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_sin_bandera_depende_del_permiso_cargar_datos(self):
        self.assertEqual(self.acceso(User(user_type=User.ADMINISTRADOR)), 'allowed')
        self.assertEqual(self.acceso(User(user_type=User.ITO)), 'allowed')
        PermisoRol.objects.create(rol='ITO', accion='cargar_datos', permitido=False)
        self.assertEqual(self.acceso(User(user_type=User.ITO)), 'disabled')

    def test_la_vista_decide_con_puede_escribir(self):
        self.assertEqual(self.acceso(User(user_type=User.ADMINISTRADOR), puede_escribir=True), 'allowed')
        self.assertEqual(self.acceso(User(user_type=User.ADMINISTRADOR), puede_escribir=False), 'disabled')
        self.assertEqual(self.acceso(User(user_type=User.ITO), puede_escribir=False), 'disabled')

    def test_concluido_y_visita_mandan_sobre_la_bandera(self):
        self.assertEqual(self.acceso(User(user_type=User.ADMINISTRADOR), puede_escribir=True, bloqueado=True), 'disabled')
        self.assertEqual(self.acceso(User(user_type=User.VISITA), puede_escribir=True), 'hidden')
