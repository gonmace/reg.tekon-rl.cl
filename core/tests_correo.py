import json
from unittest import mock

from django.core import mail
from django.core.mail.backends.locmem import EmailBackend as LocmemBackend
from django.test import TestCase, override_settings
from django.urls import reverse

from core.email_backend import ConfigurableEmailBackend
from core.email_config import get_email_config
from core.models.contractors import Contractor
from core.models.correo import ConfiguracionCorreo
from users.models import User

PLAIN_STATIC = {
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
}
ENV_SMTP = dict(EMAIL_HOST='smtp.env.cl', EMAIL_PORT=465, EMAIL_USE_SSL=True, EMAIL_USE_TLS=False,
                EMAIL_HOST_USER='env@x.cl', EMAIL_HOST_PASSWORD='clave-env-xyz',
                DEFAULT_FROM_EMAIL='Reportes <env@x.cl>')
PERSONALIZADA = {'origen': 'personalizada', 'host': 'smtp.nueva.cl', 'port': 587, 'seguridad': 'tls',
                 'usuario': 'nueva@x.cl', 'password': 'clave-nueva-xyz', 'remitente': 'Tekon <nueva@x.cl>'}


@override_settings(STORAGES=PLAIN_STATIC)
class CorreoBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        empresa = Contractor.objects.create(name='AJ', code='AJ')
        cls.root = User.objects.create_superuser('root', 'root@x.cl', 'pw', user_type='')
        cls.admin = User.objects.create_user('adm@x.cl', 'adm@x.cl', 'pw', user_type=User.ADMINISTRADOR)
        cls.coord = User.objects.create_user('coord@x.cl', 'coord@x.cl', 'pw', user_type=User.ADMINISTRADOR, contractor=empresa)

    def post(self, nombre, datos):
        return self.client.post(reverse(f'correo:{nombre}'), json.dumps(datos), content_type='application/json')


class AccesoTests(CorreoBase):
    @override_settings(**ENV_SMTP)
    def test_la_pagina_muestra_la_config_y_nunca_las_contrasenas(self):
        ConfiguracionCorreo.objects.create(pk=1, host='smtp.nueva.cl', password='clave-nueva-xyz', activa=False)
        self.client.force_login(self.root)
        r = self.client.get(reverse('correo:config'))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        for dato in ('smtp.env.cl', 'SSL/TLS', 'env@x.cl', 'smtp.nueva.cl'):
            self.assertIn(dato, html)
        for secreto in ('clave-env-xyz', 'clave-nueva-xyz'):
            self.assertNotIn(secreto, html)
        self.assertEqual(r.context['correo_prueba'], 'root@x.cl')

    def test_solo_el_superusuario(self):
        for user in (self.admin, self.coord):
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse('correo:config')).status_code, 302, user.username)
            for nombre in ('guardar', 'conexion', 'probar'):
                self.assertEqual(self.post(nombre, {}).status_code, 403, (user.username, nombre))
        self.client.logout()
        self.assertEqual(self.client.get(reverse('correo:config')).status_code, 302)

    def test_menu_solo_para_el_superusuario(self):
        from django.test import RequestFactory
        from core.menu.menu_builder import MenuBuilder
        def nombres(user):
            request = RequestFactory().get('/'); request.user, request.session = user, {}
            return {i.name for i in MenuBuilder.get_menu(user, '/', request)}
        self.assertIn('Correo', nombres(self.root))
        self.assertNotIn('Correo', nombres(self.admin))


class GuardarYResolverTests(CorreoBase):
    @override_settings(**ENV_SMTP)
    def test_por_defecto_rige_el_env(self):
        cfg = get_email_config()
        self.assertEqual((cfg['origen'], cfg['host'], cfg['usuario']), ('env', 'smtp.env.cl', 'env@x.cl'))

    @override_settings(**ENV_SMTP)
    def test_guardar_personalizada_la_activa_y_manda_sobre_el_env(self):
        self.client.force_login(self.root)
        with mock.patch('core.views.correo.conectar') as conectar:
            r = self.post('guardar', PERSONALIZADA)
        self.assertEqual(r.status_code, 200, r.content)
        conectar.assert_called_once()
        fila = ConfiguracionCorreo.objects.get(pk=1)
        self.assertTrue(fila.activa)
        self.assertEqual((fila.host, fila.port, fila.seguridad, fila.password), ('smtp.nueva.cl', 587, 'tls', 'clave-nueva-xyz'))
        cfg = get_email_config()
        self.assertEqual((cfg['origen'], cfg['host'], cfg['use_tls'], cfg['use_ssl']), ('personalizada', 'smtp.nueva.cl', True, False))
        # contraseña vacía en un nuevo guardado = mantener la guardada
        with mock.patch('core.views.correo.conectar'):
            self.post('guardar', {**PERSONALIZADA, 'password': '', 'port': 465, 'seguridad': 'ssl'})
        fila.refresh_from_db()
        self.assertEqual((fila.password, fila.port, fila.seguridad), ('clave-nueva-xyz', 465, 'ssl'))

    @override_settings(**ENV_SMTP)
    def test_volver_al_env(self):
        self.client.force_login(self.root)
        with mock.patch('core.views.correo.conectar'):
            self.post('guardar', PERSONALIZADA)
        r = self.post('guardar', {'origen': 'env'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(get_email_config()['origen'], 'env')
        self.assertEqual(ConfiguracionCorreo.objects.get(pk=1).host, 'smtp.nueva.cl')  # se conserva para después

    @override_settings(**ENV_SMTP)
    def test_no_activa_una_config_que_no_conecta(self):
        self.client.force_login(self.root)
        with mock.patch('core.views.correo.conectar', side_effect=OSError('rechazado: clave-nueva-xyz')):
            r = self.post('guardar', PERSONALIZADA)
        self.assertEqual(r.status_code, 400)
        self.assertIn('NO se activó', r.json()['message'])
        self.assertNotIn('clave-nueva-xyz', r.json()['message'])
        self.assertFalse(ConfiguracionCorreo.objects.get(pk=1).activa)
        self.assertEqual(get_email_config()['origen'], 'env')

    def test_validaciones(self):
        self.client.force_login(self.root)
        malos = [{'host': ''}, {'host': 'no valido!'}, {'port': 'abc'}, {'port': 70000}, {'seguridad': 'x'},
                 {'password': ''}, {'remitente': 'no-es-correo'}]
        for cambio in malos:
            with mock.patch('core.views.correo.conectar'):
                r = self.post('guardar', {**PERSONALIZADA, **cambio})
            self.assertEqual(r.status_code, 400, cambio)
        self.assertFalse(ConfiguracionCorreo.objects.filter(activa=True).exists())

    @override_settings(**ENV_SMTP)
    def test_el_backend_usa_la_config_activa_y_su_remitente(self):
        ConfiguracionCorreo.objects.create(pk=1, activa=True, host='smtp.nueva.cl', port=587, seguridad='tls',
                                           usuario='nueva@x.cl', password='clave-nueva-xyz', remitente='Tekon <nueva@x.cl>')
        backend = ConfigurableEmailBackend()
        self.assertEqual((backend.delegate.host, backend.delegate.port, backend.delegate.use_tls),
                         ('smtp.nueva.cl', 587, True))
        from django.core.mail import EmailMessage
        msg = EmailMessage('a', 'b', 'Reportes <env@x.cl>', ['d@x.cl'])   # remitente por defecto del .env
        with mock.patch.object(backend.delegate, 'send_messages', return_value=1) as enviar:
            backend.send_messages([msg])
        self.assertEqual(msg.from_email, 'Tekon <nueva@x.cl>')
        enviar.assert_called_once()

    @override_settings(EMAIL_HOST='', DEFAULT_FROM_EMAIL='noreply@localhost')
    def test_sin_servidor_el_backend_es_consola(self):
        from django.core.mail.backends.console import EmailBackend as Consola
        self.assertIsInstance(ConfigurableEmailBackend().delegate, Consola)


class PruebasTests(CorreoBase):
    def setUp(self):
        self.client.force_login(self.root)

    @override_settings(**ENV_SMTP)
    def test_probar_conexion_ok_y_con_error(self):
        with mock.patch('core.views.correo.conectar') as conectar:
            r = self.post('conexion', {'origen': 'env'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('smtp.env.cl:465', r.json()['message'])
        conectar.assert_called_once()
        with mock.patch('core.views.correo.conectar', side_effect=OSError('login falló con clave-env-xyz')):
            r = self.post('conexion', {'origen': 'env'})
        self.assertEqual(r.status_code, 502)
        self.assertIn('OSError', r.json()['message'])
        self.assertNotIn('clave-env-xyz', r.json()['message'])

    @override_settings(EMAIL_HOST='', DEFAULT_FROM_EMAIL='noreply@localhost')
    def test_probar_conexion_en_modo_consola(self):
        r = self.post('conexion', {'origen': 'env'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('Modo consola', r.json()['message'])

    @override_settings(**ENV_SMTP)
    def test_probar_conexion_usa_el_formulario_sin_guardar(self):
        with mock.patch('core.views.correo.conectar') as conectar:
            r = self.post('conexion', PERSONALIZADA)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(conectar.call_args[0][0]['host'], 'smtp.nueva.cl')
        self.assertFalse(ConfiguracionCorreo.objects.exists())

    @override_settings(**ENV_SMTP)
    def test_enviar_prueba_usa_la_config_elegida(self):
        with mock.patch('core.views.correo.crear_backend', return_value=LocmemBackend()) as crear:
            r = self.post('probar', {**PERSONALIZADA, 'to': 'destino@x.cl'})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(crear.call_args[0][0]['host'], 'smtp.nueva.cl')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual((mail.outbox[0].to, mail.outbox[0].from_email), (['destino@x.cl'], 'Tekon <nueva@x.cl>'))

    def test_enviar_prueba_valida_destino_y_reporta_errores(self):
        self.assertEqual(self.post('probar', {'origen': 'env', 'to': 'no-es-correo'}).status_code, 400)
        self.assertEqual(len(mail.outbox), 0)
        with mock.patch('core.views.correo.EmailMessage.send', side_effect=OSError('smtp caído')):
            r = self.post('probar', {'origen': 'env', 'to': 'destino@x.cl'})
        self.assertEqual(r.status_code, 502)
        self.assertIn('OSError', r.json()['message'])
