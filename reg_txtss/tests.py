"""
Tests de regresión para la auditoría de seguridad y portabilidad.

Cubren:
- Autenticación obligatoria en endpoints antes anónimos (PDF/preview, fotos).
- Control de propiedad a nivel de objeto (IDOR): un ITO no puede tocar
  registros de otro ITO.
- El QuerySet `with_estado()` centralizado corre en SQLite (portabilidad Q2).
"""

import datetime
import json

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from core.models.sites import Site
from reg_txtss.models import RegTxtss
from actividades.models import DatoPaso

User = get_user_model()


class OwnershipAndAuthTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(
            name='Sitio Test', pti_cell_id='PTI-1', operator_id='OP-1', tipo_sitio='POSTE'
        )
        cls.ito_a = User.objects.create_user(username='ito_a', password='pw', user_type='ITO')
        cls.ito_b = User.objects.create_user(username='ito_b', password='pw', user_type='ITO')
        cls.reg = RegTxtss.objects.create(
            sitio=cls.site, user=cls.ito_a, fecha=datetime.date(2026, 1, 1), alternativa='A'
        )

    # ── PDF / preview: antes accesibles sin login (S1) ──────────────────────
    def test_pdf_anonymous_redirected_to_login(self):
        resp = self.client.get(reverse('reg_txtss:pdf', kwargs={'registro_id': self.reg.id}))
        self.assertEqual(resp.status_code, 302)

    def test_pdf_non_owner_forbidden(self):
        self.client.force_login(self.ito_b)
        resp = self.client.get(reverse('reg_txtss:pdf', kwargs={'registro_id': self.reg.id}))
        self.assertEqual(resp.status_code, 403)

    def test_preview_non_owner_forbidden(self):
        self.client.force_login(self.ito_b)
        resp = self.client.get(reverse('reg_txtss:preview', kwargs={'registro_id': self.reg.id}))
        self.assertEqual(resp.status_code, 403)

    def test_preview_anonymous_redirected_to_login(self):
        resp = self.client.get(reverse('reg_txtss:preview', kwargs={'registro_id': self.reg.id}))
        self.assertEqual(resp.status_code, 302)

    # ── update_fecha: rol + ownership (S5) ──────────────────────────────────
    def _update_fecha(self, registro_id, fecha='2026-02-02'):
        return self.client.post(
            reverse('reg_txtss:api_update_fecha', kwargs={'registro_id': registro_id}),
            data=json.dumps({'fecha': fecha}),
            content_type='application/json',
        )

    def test_update_fecha_owner_ok(self):
        self.client.force_login(self.ito_a)
        resp = self._update_fecha(self.reg.id)
        self.assertEqual(resp.status_code, 200)
        self.reg.refresh_from_db()
        self.assertEqual(self.reg.fecha, datetime.date(2026, 2, 2))

    def test_update_fecha_non_owner_forbidden(self):
        self.client.force_login(self.ito_b)
        resp = self._update_fecha(self.reg.id)
        self.assertEqual(resp.status_code, 403)
        self.reg.refresh_from_db()
        self.assertEqual(self.reg.fecha, datetime.date(2026, 1, 1))  # sin cambios

    def test_update_fecha_anonymous_redirected(self):
        resp = self._update_fecha(self.reg.id)
        self.assertEqual(resp.status_code, 302)

    # ── toggle_concluido: rol + ownership (S5) ──────────────────────────────
    def test_toggle_concluido_owner_ok(self):
        self.client.force_login(self.ito_a)
        resp = self.client.post(
            reverse('reg_txtss:api_toggle_concluido', kwargs={'registro_id': self.reg.id})
        )
        self.assertEqual(resp.status_code, 200)
        self.reg.refresh_from_db()
        self.assertTrue(self.reg.concluido)

    def test_toggle_concluido_non_owner_forbidden(self):
        self.client.force_login(self.ito_b)
        resp = self.client.post(
            reverse('reg_txtss:api_toggle_concluido', kwargs={'registro_id': self.reg.id})
        )
        self.assertEqual(resp.status_code, 403)
        self.reg.refresh_from_db()
        self.assertFalse(self.reg.concluido)

    # ── Steps (página de detalle): ownership (S5) ───────────────────────────
    def test_steps_non_owner_forbidden(self):
        self.client.force_login(self.ito_b)
        resp = self.client.get(reverse('reg_txtss:steps', kwargs={'registro_id': self.reg.id}))
        self.assertEqual(resp.status_code, 403)


class UpdateRegistroFormTests(TestCase):
    """El endpoint admin de edición valida el responsable vía Form (Q5)."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name='S3', pti_cell_id='PTI-3', tipo_sitio='POSTE')
        cls.superuser = User.objects.create_user(username='super', password='pw', user_type='')
        cls.ito = User.objects.create_user(username='ito_c', password='pw', user_type='ITO')
        cls.visita = User.objects.create_user(username='vis', password='pw', user_type='VISITA')
        cls.reg = RegTxtss.objects.create(
            sitio=cls.site, user=cls.ito, fecha=datetime.date(2026, 4, 1), alternativa='A'
        )

    def test_update_registro_rejects_non_ito_user(self):
        self.client.force_login(self.superuser)
        url = reverse('reg_txtss:api_update', kwargs={'registro_id': self.reg.id})
        resp = self.client.post(url, data={'user_id': self.visita.id, 'alternativa': 'B'})
        self.assertEqual(resp.status_code, 400)
        self.reg.refresh_from_db()
        self.assertEqual(self.reg.user_id, self.ito.id)  # sin cambios

    def test_update_registro_updates_alternativa(self):
        self.client.force_login(self.superuser)
        url = reverse('reg_txtss:api_update', kwargs={'registro_id': self.reg.id})
        resp = self.client.post(url, data={'user_id': self.ito.id, 'alternativa': 'C'})
        self.assertEqual(resp.status_code, 200)
        self.reg.refresh_from_db()
        self.assertEqual(self.reg.alternativa, 'C')


class ImageUploadValidationTests(TestCase):
    """Validación real de imágenes en la subida (S6)."""

    def test_rejects_non_image_content(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from photos.views import validate_image_upload
        fake = SimpleUploadedFile('foto.jpg', b'esto no es una imagen', content_type='image/jpeg')
        ok, msg = validate_image_upload(fake)
        self.assertFalse(ok)

    def test_rejects_disallowed_extension(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from photos.views import validate_image_upload
        f = SimpleUploadedFile('malicioso.svg', b'<svg></svg>', content_type='image/svg+xml')
        ok, msg = validate_image_upload(f)
        self.assertFalse(ok)


class WithEstadoQuerySetTests(TestCase):
    """El QuerySet centralizado debe correr en SQLite (portabilidad, Q2)."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name='S2', pti_cell_id='PTI-2', tipo_sitio='POSTE')
        cls.user = User.objects.create_user(username='u2', password='pw', user_type='ITO')
        cls.reg = RegTxtss.objects.create(
            sitio=cls.site, user=cls.user, fecha=datetime.date(2026, 3, 1), alternativa='A'
        )

    def test_with_estado_runs_and_flags_empty_registro(self):
        reg = RegTxtss.objects.filter(id=self.reg.id).with_estado().first()
        self.assertIsNotNone(reg)
        self.assertFalse(reg.has_widgets)          # sin datos/fotos/mapas
        self.assertEqual(reg.orden_estado, 3)      # rojo / vacío

    def test_with_estado_detects_datos(self):
        ct = ContentType.objects.get_for_model(RegTxtss)
        DatoPaso.objects.create(
            content_type=ct, object_id=self.reg.id, paso_nombre='mandato',
            datos={'lat': '-33.4', 'lon': '-70.6'},
        )
        reg = RegTxtss.objects.filter(id=self.reg.id).with_estado().first()
        self.assertTrue(reg.has_widgets)
        self.assertEqual(reg.orden_estado, 1)      # amarillo / en proceso
