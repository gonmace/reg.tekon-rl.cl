from django.test import TestCase, override_settings
from django.urls import reverse

from registros.registry import all_registro_models, get_registro_model
from users.models import User

PLAIN_STATIC = {
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
}


class RegistryAndGalleryTests(TestCase):
    def test_txtss_registrado(self):
        from reg_txtss.models import RegTxtss
        self.assertIs(get_registro_model('reg_txtss'), RegTxtss)
        self.assertIn(RegTxtss, all_registro_models())

    @override_settings(STORAGES=PLAIN_STATIC)
    def test_galeria_renderiza(self):
        root = User.objects.create_superuser('root', 'r@x.cl', 'pw', user_type='')
        self.client.force_login(root)
        self.assertEqual(self.client.get(reverse('photos:gallery')).status_code, 200)
        self.assertEqual(self.client.get(reverse('photos:gallery') + '?tipo=POSTE&sort=sitio_asc').status_code, 200)
