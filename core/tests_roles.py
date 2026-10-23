"""Roles y permisos: resolución de permisos configurables, alcance por empresa y pantalla de Usuarios."""
import json
from datetime import date
from importlib import import_module

from django.apps import apps
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models.contractors import Contractor
from core.models.permisos import PermisoRol, PermisoUsuario
from core.models.sites import Site
from core.permisos_catalogo import ACCIONES, por_defecto
from core.permissions import alcance_registros, can_access_registro, puede_editar_usuario, tiene_permiso
from reg_construccion.models import RegConstruccion
from users.models import User
from users.permissions import validar_rol_empresa

PLAIN_STATIC = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


@override_settings(STORAGES=PLAIN_STATIC)
class RolesBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = Contractor.objects.create(name='A', code='A')
        cls.b = Contractor.objects.create(name='B', code='B')
        cls.root = User.objects.create_superuser('root', 'r@x.cl', 'pw', user_type='')
        cls.admin_global = User.objects.create_user('ag', 'ag@x.cl', 'pw', user_type=User.ADMINISTRADOR)
        cls.admin_a = User.objects.create_user('aa', 'aa@x.cl', 'pw', user_type=User.ADMINISTRADOR, contractor=cls.a)
        cls.ito_a = User.objects.create_user('ia', 'ia@x.cl', 'pw', user_type=User.ITO, contractor=cls.a)
        cls.ito_b = User.objects.create_user('ib', 'ib@x.cl', 'pw', user_type=User.ITO, contractor=cls.b)
        cls.buscador_a = User.objects.create_user('ba', 'ba@x.cl', 'pw', user_type=User.SEARCHER, contractor=cls.a)
        cls.visita = User.objects.create_user('v', 'v@x.cl', 'pw', user_type=User.VISITA, contractor=cls.a)
        cls.sitio = Site.objects.create(pti_cell_id='T-1', operator_id='1', name='Torre', tipo_sitio=Site.TORRE)
        cls.reg_a = RegConstruccion.objects.create(sitio=cls.sitio, user=cls.ito_a, fecha=date(2026, 1, 1), contratista=cls.a)
        cls.reg_b = RegConstruccion.objects.create(sitio=cls.sitio, user=cls.ito_b, fecha=date(2026, 1, 2), contratista=cls.b)

    def setUp(self):
        # el mapa por rol está en caché y la transacción del test no lo invalida al revertir
        cache.clear()
        self.addCleanup(cache.clear)

    def fresco(self, user):
        return User.objects.get(pk=user.pk)

    def post_json(self, user, url, body):
        self.client.force_login(user)
        return self.client.post(url, json.dumps(body), content_type='application/json')


class ResolucionDePermisosTests(RolesBase):
    def test_valores_por_defecto_del_catalogo(self):
        esperado = {
            'cargar_datos': {'ADMINISTRADOR', 'ITO', 'SEARCHER'},
            'concluir': {'ADMINISTRADOR', 'ITO', 'SEARCHER'},
            'reabrir': {'ADMINISTRADOR'},
            'activar_registro': {'ADMINISTRADOR'},
            'definir_items_obra': {'ADMINISTRADOR'},
            'gestionar_usuarios': {'ADMINISTRADOR'},
        }
        for accion, roles in esperado.items():
            for rol in ('ADMINISTRADOR', 'ITO', 'SEARCHER', 'VISITA'):
                self.assertEqual(por_defecto(rol, accion), rol in roles, (rol, accion))

    def test_superusuario_siempre_y_visita_nunca(self):
        PermisoRol.objects.create(rol='VISITA', accion='cargar_datos', permitido=True)
        PermisoUsuario.objects.create(user=self.visita, accion='cargar_datos', permitido=True)
        for accion in ACCIONES:
            self.assertTrue(tiene_permiso(self.root, accion), accion)
            self.assertFalse(tiene_permiso(self.fresco(self.visita), accion), accion)
        self.assertFalse(tiene_permiso(None, 'concluir'))

    def test_orden_usuario_sobre_rol_sobre_defecto(self):
        self.assertTrue(tiene_permiso(self.fresco(self.ito_a), 'concluir'))             # defecto
        PermisoRol.objects.create(rol='ITO', accion='concluir', permitido=False)
        self.assertFalse(tiene_permiso(self.fresco(self.ito_a), 'concluir'))            # rol
        self.assertTrue(tiene_permiso(self.fresco(self.buscador_a), 'concluir'))        # otro rol no cambia
        PermisoUsuario.objects.create(user=self.ito_a, accion='concluir', permitido=True)
        self.assertTrue(tiene_permiso(self.fresco(self.ito_a), 'concluir'))             # excepción del usuario
        self.assertFalse(tiene_permiso(self.fresco(self.ito_b), 'concluir'))

    def test_accion_desconocida(self):
        with self.assertRaises(KeyError):
            tiene_permiso(self.root, 'inventada')


class AlcanceTests(RolesBase):
    def test_alcance_y_acceso_coinciden(self):
        esperado = {
            self.root: {self.reg_a.pk, self.reg_b.pk},
            self.admin_global: {self.reg_a.pk, self.reg_b.pk},
            self.visita: {self.reg_a.pk, self.reg_b.pk},
            self.admin_a: {self.reg_a.pk},
            self.ito_a: {self.reg_a.pk},
            self.buscador_a: set(),
            self.ito_b: {self.reg_b.pk},
        }
        for user, pks in esperado.items():
            visibles = set(alcance_registros(RegConstruccion.objects.all(), user).values_list('pk', flat=True))
            self.assertEqual(visibles, pks, user.username)
            for reg in (self.reg_a, self.reg_b):
                self.assertEqual(can_access_registro(user, reg), reg.pk in pks, (user.username, reg.pk))

    def test_pagina_del_registro_respeta_el_alcance(self):
        url = lambda reg: reverse('reg_construccion:steps', kwargs={'registro_id': reg.pk})
        self.client.force_login(self.admin_a)
        self.assertEqual(self.client.get(url(self.reg_a)).status_code, 200)
        self.assertEqual(self.client.get(url(self.reg_b)).status_code, 403)
        self.client.force_login(self.admin_global)
        self.assertEqual(self.client.get(url(self.reg_b)).status_code, 200)


class AccesoPorReporteTests(RolesBase):
    def test_sin_acceso_al_reporte_no_ve_ni_abre_sus_registros(self):
        User.objects.filter(pk=self.ito_a.pk).update(report_access=['txtss_postes'])
        ito = self.fresco(self.ito_a)
        self.assertEqual(alcance_registros(RegConstruccion.objects.all(), ito).count(), 0)
        self.assertFalse(can_access_registro(ito, self.reg_a))
        self.client.force_login(ito)
        self.assertEqual(self.client.get(reverse('reg_construccion:steps', kwargs={'registro_id': self.reg_a.pk})).status_code, 403)

    def test_txtss_se_filtra_por_tipo_de_sitio(self):
        from reg_txtss.models import RegTxtss
        poste = Site.objects.create(pti_cell_id='P-1', operator_id='2', name='Poste', tipo_sitio=Site.POSTE)
        rp = RegTxtss.objects.create(sitio=poste, user=self.ito_a, fecha=date(2026, 1, 1))
        rt = RegTxtss.objects.create(sitio=self.sitio, user=self.ito_a, fecha=date(2026, 1, 2))
        User.objects.filter(pk=self.ito_a.pk).update(report_access=['txtss_torres'])
        ito = self.fresco(self.ito_a)
        self.assertEqual(set(alcance_registros(RegTxtss.objects.all(), ito).values_list('pk', flat=True)), {rt.pk})
        self.assertFalse(can_access_registro(ito, rp))
        self.assertTrue(can_access_registro(ito, rt))
        self.assertEqual(set(alcance_registros(RegTxtss.objects.all(), self.root).values_list('pk', flat=True)), {rp.pk, rt.pk})


class UsuariosYEmpresaTests(RolesBase):
    def test_validacion_del_modelo(self):
        with self.assertRaises(ValidationError):
            User(username='s', user_type='', contractor=self.a).full_clean(exclude=['password'])
        with self.assertRaises(ValidationError):
            User(username='i', user_type=User.ITO).full_clean(exclude=['password'])
        for u in (User(username='ok1', user_type=User.ADMINISTRADOR), User(username='ok2', user_type=User.ITO, contractor=self.a)):
            u.full_clean(exclude=['password'])

    def test_propiedades_de_alcance_del_administrador(self):
        self.assertTrue(self.admin_global.is_admin_global)
        self.assertFalse(self.admin_global.is_admin_empresa)
        self.assertTrue(self.admin_a.is_admin_empresa)
        self.assertFalse(self.ito_a.is_admin_global or self.ito_a.is_admin_empresa)

    def test_roles_y_empresa_asignables(self):
        self.assertIsNone(validar_rol_empresa(self.root, User.ADMINISTRADOR, None))
        self.assertIsNone(validar_rol_empresa(self.admin_global, User.ITO, self.b))
        self.assertIsNone(validar_rol_empresa(self.admin_global, User.ADMINISTRADOR, self.b))
        self.assertIsNotNone(validar_rol_empresa(self.admin_global, User.ADMINISTRADOR, None))   # no crea globales
        self.assertIsNone(validar_rol_empresa(self.admin_a, User.VISITA, self.a))
        self.assertIsNotNone(validar_rol_empresa(self.admin_a, User.ITO, self.b))                # otra empresa
        self.assertIsNotNone(validar_rol_empresa(self.admin_a, User.ADMINISTRADOR, self.a))      # no crea administradores
        self.assertIsNotNone(validar_rol_empresa(self.root, User.ITO, None))                     # falta empresa

    def test_quien_puede_editar_a_quien(self):
        self.assertTrue(puede_editar_usuario(self.root, self.admin_a))
        self.assertTrue(puede_editar_usuario(self.root, User.objects.create_superuser('r2', 'r2@x.cl', 'pw', user_type='')))
        self.assertTrue(puede_editar_usuario(self.admin_global, self.ito_b))
        self.assertTrue(puede_editar_usuario(self.admin_global, self.admin_a))
        self.assertFalse(puede_editar_usuario(self.admin_global, self.root))
        self.assertTrue(puede_editar_usuario(self.admin_a, self.visita))
        self.assertFalse(puede_editar_usuario(self.admin_a, self.ito_b))
        self.assertFalse(puede_editar_usuario(self.admin_a, self.admin_global))
        self.assertFalse(puede_editar_usuario(self.ito_a, self.visita))

    def test_admin_de_empresa_crea_en_su_empresa_y_no_administradores(self):
        crear = lambda **kw: self.post_json(self.admin_a, reverse('users:api'), {
            'username': 'n@x.cl', 'password': 'Clave-segura-2026', 'user_type': 'ITO', **kw})
        self.assertEqual(crear(contractor=self.b.pk).status_code, 403)
        self.assertEqual(crear(user_type='ADMINISTRADOR', contractor=self.a.pk).status_code, 403)
        r = crear()                                              # sin empresa: usa la suya
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(User.objects.get(username='n@x.cl').contractor, self.a)

    def test_la_lista_se_limita_a_la_empresa_del_administrador(self):
        self.client.force_login(self.admin_a)
        nombres = {u.username for u in self.client.get(reverse('users:list')).context['table'].data}
        self.assertEqual(nombres, {'aa', 'ia', 'ba', 'v'})
        self.client.force_login(self.admin_global)
        nombres = {u.username for u in self.client.get(reverse('users:list')).context['table'].data}
        self.assertTrue({'ib', 'ia', 'aa'} <= nombres)

    def test_migracion_de_coord_y_superusuario(self):
        migracion = import_module('users.migrations.0008_eliminar_coord')
        User.objects.filter(pk=self.admin_global.pk).update(contractor=self.b)       # administrador con empresa
        coord = User.objects.create_user('co', 'co@x.cl', 'pw', user_type='COORD', contractor=self.a)
        User.objects.filter(pk=self.root.pk).update(contractor=self.a)               # superusuario con empresa
        migracion.coord_a_administrador(apps, None)
        self.assertIsNone(self.fresco(self.admin_global).contractor)                 # administradores previos → globales
        coord.refresh_from_db()
        self.assertEqual((coord.user_type, coord.contractor), (User.ADMINISTRADOR, self.a))
        self.assertIsNone(self.fresco(self.root).contractor)


class PantallaPermisosTests(RolesBase):
    url = property(lambda self: reverse('users:permisos_rol'))

    def test_solo_el_superusuario_guarda_la_matriz(self):
        cuerpo = {'cambios': [{'rol': 'ITO', 'accion': 'concluir', 'permitido': False}]}
        for user in (self.admin_global, self.admin_a, self.ito_a, self.visita):
            self.assertEqual(self.post_json(user, self.url, cuerpo).status_code, 403, user.username)
        self.assertFalse(PermisoRol.objects.exists())
        self.assertEqual(self.post_json(self.root, self.url, cuerpo).status_code, 200)
        self.assertFalse(tiene_permiso(self.fresco(self.ito_a), 'concluir'))

    def test_solo_se_guardan_las_diferencias_con_el_defecto(self):
        self.post_json(self.root, self.url, {'cambios': [{'rol': 'ITO', 'accion': 'concluir', 'permitido': False}]})
        self.assertEqual(PermisoRol.objects.count(), 1)
        self.post_json(self.root, self.url, {'cambios': [{'rol': 'ITO', 'accion': 'concluir', 'permitido': True}]})
        self.assertFalse(PermisoRol.objects.exists())                       # igual al defecto: se borra la fila

    def test_cambios_invalidos_y_restaurar(self):
        for malo in ({'rol': 'VISITA', 'accion': 'concluir', 'permitido': True},
                     {'rol': 'ITO', 'accion': 'inventada', 'permitido': True},
                     {'rol': 'ITO', 'accion': 'concluir', 'permitido': 'si'}):
            self.assertEqual(self.post_json(self.root, self.url, {'cambios': [malo]}).status_code, 400, malo)
        self.post_json(self.root, self.url, {'cambios': [{'rol': 'ADMINISTRADOR', 'accion': 'reabrir', 'permitido': False}]})
        self.assertFalse(tiene_permiso(self.fresco(self.admin_a), 'reabrir'))
        self.assertEqual(self.post_json(self.root, self.url, {'restaurar': True}).status_code, 200)
        self.assertTrue(tiene_permiso(self.fresco(self.admin_a), 'reabrir'))

    def test_la_pagina_muestra_casillas_solo_al_superusuario(self):
        self.client.force_login(self.root)
        self.assertContains(self.client.get(reverse('users:list')), 'permiso-check')
        self.client.force_login(self.admin_global)
        r = self.client.get(reverse('users:list'))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'permiso-check')
        self.assertNotContains(r, 'Coordinador')

    def test_excepciones_por_usuario_solo_las_define_el_superusuario(self):
        url = reverse('users:api_detail', kwargs={'user_id': self.ito_a.pk})
        put = lambda user, extra: (self.client.force_login(user), self.client.put(
            url, json.dumps({'permisos_extra': extra}), content_type='application/json'))[1]
        self.assertEqual(put(self.admin_global, {'concluir': 'deny'}).status_code, 200)
        self.assertFalse(PermisoUsuario.objects.exists())                  # el administrador no puede fijarlas
        self.assertEqual(put(self.root, {'concluir': 'deny', 'inventada': 'allow', 'reabrir': 'allow'}).status_code, 200)
        self.assertEqual(set(PermisoUsuario.objects.values_list('accion', 'permitido')), {('concluir', False), ('reabrir', True)})
        put(self.root, {'concluir': 'inherit'})
        self.assertEqual(list(PermisoUsuario.objects.values_list('accion', flat=True)), ['reabrir'])

    def test_el_modal_muestra_excepciones_solo_al_superusuario(self):
        url = reverse('users:edit_modal', kwargs={'user_id': self.ito_a.pk})
        self.client.force_login(self.root)
        self.assertIn('permisosExtraSection', self.client.get(url).json()['form_html'])
        self.client.force_login(self.admin_global)
        self.assertNotIn('permisosExtraSection', self.client.get(url).json()['form_html'])


class SitiosYEmpresasTests(RolesBase):
    def test_admin_global_edita_pero_no_crea_ni_elimina_empresas(self):
        self.client.force_login(self.admin_global)
        self.assertEqual(self.client.get(reverse('contractors:contractors_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('contractors:contractor_create_modal')).status_code, 403)
        r = self.client.post(reverse('contractors:contractors_api'), '{}', content_type='application/json')
        self.assertEqual(r.status_code, 403)
        r = self.client.delete(reverse('contractors:contractor_detail', kwargs={'contractor_id': self.a.pk}))
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.client.get(reverse('contractors:contractor_edit_modal', kwargs={'contractor_id': self.a.pk})).status_code, 200)

    def test_admin_de_empresa_no_entra_a_sitios_ni_empresas(self):
        self.client.force_login(self.admin_a)
        for nombre in ('sitios:sitios_list', 'contractors:contractors_list'):
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 302, nombre)

    def test_admin_global_no_elimina_sitios(self):
        url = reverse('sitios:sitios-detail', kwargs={'pk': self.sitio.pk})
        self.client.force_login(self.admin_global)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.client.force_login(self.root)
        self.assertEqual(self.client.delete(url).status_code, 200)
