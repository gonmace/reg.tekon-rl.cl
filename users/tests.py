from datetime import date

from django.test import TestCase, override_settings
from django.urls import reverse

from core.models.contractors import Contractor
from users.models import User
from users.permissions import can_hijack


class HijackTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.contractor = Contractor.objects.create(name='Contratista', code='C1')
        cls.root = User.objects.create_superuser('root', 'root@x.cl', 'pw', user_type='')
        cls.root2 = User.objects.create_superuser('root2', 'root2@x.cl', 'pw', user_type='')
        cls.supermanager = User.objects.create_user('sm', 'sm@x.cl', 'pw', user_type='')
        cls.ito = User.objects.create_user(
            'ito', 'ito@x.cl', 'pw', user_type=User.ITO, contractor=cls.contractor)

    def test_superuser_puede_impersonar_a_no_superuser(self):
        self.assertTrue(can_hijack(hijacker=self.root, hijacked=self.ito))

    def test_no_puede_impersonar_a_otro_superuser(self):
        self.assertFalse(can_hijack(hijacker=self.root, hijacked=self.root2))

    def test_supermanager_sin_is_superuser_no_puede(self):
        self.assertFalse(can_hijack(hijacker=self.supermanager, hijacked=self.ito))

    def test_no_puede_impersonar_inactivo_o_borrado(self):
        self.ito.is_active = False
        self.assertFalse(can_hijack(hijacker=self.root, hijacked=self.ito))
        self.ito.is_active, self.ito.is_deleted = True, True
        self.assertFalse(can_hijack(hijacker=self.root, hijacked=self.ito))

    def test_flujo_acquire_y_release(self):
        self.client.force_login(self.root)
        r = self.client.post(reverse('hijack:acquire'), {'user_pk': self.ito.pk, 'next': '/'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.ito.pk)
        r = self.client.post(reverse('hijack:release'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.root.pk)

    def test_supermanager_recibe_403_al_impersonar(self):
        self.client.force_login(self.supermanager)
        r = self.client.post(reverse('hijack:acquire'), {'user_pk': self.ito.pk})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.supermanager.pk)


class UiSmokeTests(TestCase):
    """Las páginas principales renderizan (menú, header con dropdown, cards, banner)."""

    @classmethod
    def setUpTestData(cls):
        cls.contractor = Contractor.objects.create(name='Contratista', code='C1')
        cls.root = User.objects.create_superuser('root', 'root@x.cl', 'pw', user_type='')
        cls.ito = User.objects.create_user(
            'ito', 'ito@x.cl', 'pw', user_type=User.ITO, contractor=cls.contractor)

    def test_paginas_principales(self):
        self.client.force_login(self.root)
        for name in ('dashboard:dashboard', 'users:list'):
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 200, name)
        self.assertContains(self.client.get(reverse('users:list')), 'hijack/acquire')

    def test_banner_al_impersonar(self):
        self.client.force_login(self.root)
        self.client.post(reverse('hijack:acquire'), {'user_pk': self.ito.pk, 'next': '/'})
        r = self.client.get(reverse('dashboard:dashboard'))
        self.assertContains(r, 'Volver a mi cuenta')
        self.assertContains(r, 'Cerrar sesi')


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from core.models.sites import Site
        from reg_construccion.models import RegConstruccion
        from reg_txtss.models import RegTxtss
        cls.contractor = Contractor.objects.create(name='AJ', code='AJ')
        cls.root = User.objects.create_superuser('root', 'root@x.cl', 'pw', user_type='')
        cls.ito = User.objects.create_user('ito', 'ito@x.cl', 'pw', user_type=User.ITO, contractor=cls.contractor)
        cls.ito2 = User.objects.create_user('ito2', 'i2@x.cl', 'pw', user_type=User.ITO, contractor=cls.contractor)
        torre = Site.objects.create(pti_cell_id='T-1', operator_id='1', name='Torre Uno', tipo_sitio=Site.TORRE)
        RegTxtss.objects.create(sitio=torre, user=cls.ito, alternativa='A')
        RegConstruccion.objects.create(sitio=torre, user=cls.ito, avance_pct=40)
        RegConstruccion.objects.create(sitio=torre, user=cls.ito2, fecha=date(2026, 1, 1), avance_pct=10)

    def test_dashboard_renderiza_con_actividad_y_respeta_el_rol(self):
        from django.core.cache import cache
        from django.test import override_settings
        cache.clear()
        with override_settings(STORAGES={
            'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
            'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'}}):
            self.client.force_login(self.root)
            r = self.client.get(reverse('dashboard:dashboard'))
            self.assertEqual(r.status_code, 200)
            self.assertEqual(len(r.context['actividad_reciente']), 2)
            self.assertEqual(r.context['kpis']['total_visitas'], 2)
            self.client.force_login(self.ito)
            r = self.client.get(reverse('dashboard:dashboard'))
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.context['kpis']['total_visitas'], 1)
            self.assertEqual(len(r.context['actividad_reciente']), 1)


class NombreParaMostrarTests(TestCase):
    def test_display_name_e_iniciales(self):
        from users.models import User
        con = User.objects.create_user('ana@x.cl', 'ana@x.cl', 'pw', user_type=User.ITO, first_name='Ana', last_name='Pérez')
        sin = User.objects.create_user('juan@x.cl', 'juan@x.cl', 'pw', user_type=User.ITO)
        self.assertEqual((con.display_name, con.iniciales), ('Ana Pérez', 'AP'))
        self.assertEqual((sin.display_name, sin.iniciales), ('juan@x.cl', 'JU'))  # sin nombre: cae al usuario

    def test_el_encabezado_muestra_el_nombre_y_no_el_correo(self):
        user = User.objects.create_user('ana@x.cl', 'ana@x.cl', 'pw', user_type=User.ITO, first_name='Ana', last_name='Pérez')
        self.client.force_login(user)
        html = self.client.get(reverse('dashboard:dashboard')).content.decode()
        self.assertIn('<span class="hidden lg:inline text-sm font-medium">Ana Pérez</span>', html)
        self.assertNotIn('>ana@x.cl<', html)


class AccesoUsuariosTests(TestCase):
    """Usuarios: superusuario y ADMINISTRADOR (global o de empresa) entran; ITO no."""

    @classmethod
    def setUpTestData(cls):
        empresa = Contractor.objects.create(name='AJ', code='AJ')
        cls.root = User.objects.create_superuser('root', 'r@x.cl', 'pw', user_type='')
        cls.admin = User.objects.create_user('adm', 'a@x.cl', 'pw', user_type=User.ADMINISTRADOR)
        cls.coord = User.objects.create_user('coord', 'c@x.cl', 'pw', user_type=User.ADMINISTRADOR, contractor=empresa)
        cls.ito = User.objects.create_user('ito', 'i@x.cl', 'pw', user_type=User.ITO, contractor=empresa)

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.addCleanup(cache.clear)

    def _menu(self, user):
        from django.test import RequestFactory
        from core.menu.menu_builder import MenuBuilder
        request = RequestFactory().get('/')
        request.user, request.session = user, {}
        return {item.name for item in MenuBuilder.get_menu(user, '/', request)}

    def test_menu_usuarios(self):
        self.assertIn('Usuarios', self._menu(self.root))
        self.assertIn('Usuarios', self._menu(self.coord))
        self.assertIn('Usuarios', self._menu(self.admin))
        self.assertNotIn('Usuarios', self._menu(self.ito))

    def test_se_puede_quitar_el_acceso_a_usuarios_a_un_rol_o_a_un_usuario(self):
        from core.models.permisos import PermisoRol, PermisoUsuario
        PermisoRol.objects.create(rol='ADMINISTRADOR', accion='gestionar_usuarios', permitido=False)
        self.assertNotIn('Usuarios', self._menu(self.admin))
        PermisoUsuario.objects.create(user=self.admin, accion='gestionar_usuarios', permitido=True)
        self.assertIn('Usuarios', self._menu(User.objects.get(pk=self.admin.pk)))

    def test_pagina_y_api_de_usuarios(self):
        url, api = reverse('users:list'), reverse('users:api')
        for user in (self.root, self.coord, self.admin):
            self.client.force_login(user)
            self.assertEqual(self.client.get(url).status_code, 200, user.username)
        for user in (self.ito,):
            self.client.force_login(user)
            self.assertEqual(self.client.get(url).status_code, 302, user.username)   # → dashboard
            self.assertEqual(self.client.post(api, '{}', content_type='application/json').status_code, 403, user.username)
            self.assertEqual(self.client.get(reverse('users:create_modal')).status_code, 403, user.username)


class InvitacionTests(TestCase):
    """Invitar por correo: el usuario crea su contraseña con el enlace y puede iniciar sesión."""

    @classmethod
    def setUpTestData(cls):
        cls.empresa = Contractor.objects.create(name='AJ', code='AJ')
        cls.otra = Contractor.objects.create(name='OT', code='OT')
        cls.root = User.objects.create_superuser('root', 'r@x.cl', 'pw', user_type='')
        cls.coord = User.objects.create_user('coord@x.cl', 'coord@x.cl', 'pw', user_type=User.ADMINISTRADOR, contractor=cls.empresa,
                                             first_name='Cora', last_name='Díaz')
        cls.ito = User.objects.create_user('ito@x.cl', 'ito@x.cl', 'pw', user_type=User.ITO, contractor=cls.empresa)
        cls.ito_otra = User.objects.create_user('ito2@x.cl', 'ito2@x.cl', 'pw', user_type=User.ITO, contractor=cls.otra)
        cls.admin = User.objects.create_user('adm@x.cl', 'adm@x.cl', 'pw', user_type=User.ADMINISTRADOR)

    def _crear(self, user, **extra):
        import json
        self.client.force_login(user)
        # Invitar: solo correo (+ rol y empresa); nombre, apellido y teléfono los completa el invitado
        payload = {'username': 'nuevo@x.cl', 'user_type': User.ITO, 'contractor': self.empresa.pk, 'invitar': True, **extra}
        return self.client.post(reverse('users:api'), json.dumps(payload), content_type='application/json')

    def test_crear_con_invitacion_envia_correo_y_sin_contrasena(self):
        from django.core import mail
        r = self._crear(self.coord)
        self.assertEqual(r.status_code, 200, r.content)
        usuario = User.objects.get(username='nuevo@x.cl')
        self.assertFalse(usuario.has_usable_password())
        self.assertEqual((usuario.first_name, usuario.last_name, usuario.phone), ('', '', None))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['nuevo@x.cl'])
        self.assertIn('/password-reset/', mail.outbox[0].body)
        self.assertIn('Cora Díaz', mail.outbox[0].body)  # quién invita

    def test_sin_invitacion_la_contrasena_sigue_siendo_obligatoria(self):
        r = self._crear(self.coord, invitar=False)
        self.assertEqual(r.status_code, 400)

    def test_el_enlace_permite_crear_la_contrasena_e_iniciar_sesion(self):
        import re
        from django.core import mail
        self._crear(self.coord)
        enlace = re.search(r'https?://\S+/password-reset/\S+/\S+/', mail.outbox[0].body).group(0)
        ruta = '/' + enlace.split('/', 3)[3]
        self.client.logout()
        r = self.client.get(ruta, follow=True)
        self.assertEqual(r.status_code, 200)
        for campo in ('first_name', 'last_name', 'phone'):
            self.assertContains(r, f'name="{campo}"')           # el invitado completa su perfil
        url_form = r.redirect_chain[-1][0] if r.redirect_chain else ruta
        clave = {'new_password1': 'Clave-segura-2026', 'new_password2': 'Clave-segura-2026'}
        # sin los datos del perfil no se activa la cuenta
        r = self.client.post(url_form, clave)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.get(username='nuevo@x.cl').has_usable_password())
        r = self.client.post(url_form, {**clave, 'first_name': 'Nora', 'last_name': 'Soto', 'phone': '123'})
        self.assertEqual(r.status_code, 200)                    # teléfono inválido
        r = self.client.post(url_form, {**clave, 'first_name': 'Nora', 'last_name': 'Soto', 'phone': '+56 9 1234 5678'})
        self.assertEqual(r.status_code, 302, r.content[:300])
        usuario = User.objects.get(username='nuevo@x.cl')
        self.assertEqual((usuario.first_name, usuario.last_name, usuario.phone), ('Nora', 'Soto', '+56 9 1234 5678'))
        self.assertTrue(self.client.login(username='nuevo@x.cl', password='Clave-segura-2026'))

    def test_reenviar_invitacion_y_permisos(self):
        from django.core import mail
        url = lambda u: reverse('users:invite', kwargs={'user_id': u.pk})
        self.client.force_login(self.coord)
        self.assertEqual(self.client.post(url(self.ito)).status_code, 200)             # de su empresa
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.client.post(url(self.ito_otra)).status_code, 403)         # de otra empresa
        self.assertEqual(self.client.post(url(self.root)).status_code, 403)             # superusuario
        for user in (self.ito,):
            self.client.force_login(user)
            self.assertEqual(self.client.post(url(self.ito)).status_code, 403, user.username)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(url(self.ito_otra)).status_code, 200)         # global: cualquier empresa
        self.client.force_login(self.root)
        self.assertEqual(self.client.post(url(self.ito_otra)).status_code, 200)
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(self.client.post(reverse('users:invite', kwargs={'user_id': 99999})).status_code, 404)

    def test_falla_el_envio_pero_el_usuario_queda_creado(self):
        from unittest import mock
        with mock.patch('users.invitations.send_mail', side_effect=OSError('smtp caído')):
            r = self._crear(self.coord)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()['success'])
        self.assertIn('no se pudo enviar', r.json()['message'])
        self.assertTrue(User.objects.filter(username='nuevo@x.cl').exists())

    def test_olvide_mi_contrasena_ya_no_da_error(self):
        """Antes redirigía a 'password_reset_done' sin el namespace y devolvía 500."""
        from django.core import mail
        self.client.logout()
        r = self.client.post(reverse('users:password_reset'), {'email': 'ito@x.cl'})
        self.assertRedirects(r, reverse('users:password_reset_done'), fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 1)

    def test_quien_ya_tiene_contrasena_solo_la_cambia(self):
        """El enlace de «olvidé mi contraseña» no pide nombre, apellido ni teléfono."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        uid = urlsafe_base64_encode(force_bytes(self.ito.pk))
        ruta = reverse('users:password_reset_confirm', kwargs={'uidb64': uid, 'token': default_token_generator.make_token(self.ito)})
        r = self.client.get(ruta, follow=True)
        self.assertEqual(r.status_code, 200)
        for campo in ('first_name', 'last_name', 'phone'):
            self.assertNotContains(r, f'name="{campo}"')
        r = self.client.post(r.redirect_chain[-1][0], {'new_password1': 'Otra-clave-2026', 'new_password2': 'Otra-clave-2026'})
        self.assertEqual(r.status_code, 302)


class UltimaConexionTests(TestCase):
    @override_settings(STORAGES={'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
                                 'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'}})
    def test_la_tabla_muestra_la_ultima_conexion(self):
        from django.utils import timezone
        empresa = Contractor.objects.create(name='AJ', code='AJ')
        root = User.objects.create_superuser('root', 'r@x.cl', 'pw', user_type='')
        con = User.objects.create_user('con@x.cl', 'con@x.cl', 'pw', user_type=User.ITO, contractor=empresa)
        User.objects.filter(pk=con.pk).update(last_login=timezone.now())
        nunca = User.objects.create_user('nunca@x.cl', 'nunca@x.cl', 'pw', user_type=User.ITO, contractor=empresa)
        invitado = User.objects.create_user('inv@x.cl', 'inv@x.cl', 'pw', user_type=User.ITO, contractor=empresa)
        invitado.set_unusable_password(); invitado.save()
        self.client.force_login(root)
        html = self.client.get(reverse('users:list')).content.decode()
        self.assertIn('Última conexión', html)
        self.assertIn(timezone.localtime(User.objects.get(pk=con.pk).last_login).strftime('%d/%m/%Y %H:%M'), html)
        self.assertIn('Nunca', html)                 # tiene contraseña pero jamás entró
        self.assertIn('Invitación pendiente', html)  # invitado sin activar
