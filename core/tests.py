"""
Sitios: PTI ID y nombre son únicos solo entre sitios NO eliminados (soft delete).
"""
import json

import tablib
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from core.models.sites import Site
from core.resources import SiteResource
from core.serializers import SiteSerializer
from users.models import User


def sitio(pti, nombre, **kw):
    kw.setdefault('tipo_sitio', Site.TORRE)
    return Site.objects.create(pti_cell_id=pti, name=nombre, operator_id='1', **kw)


class UnicidadSoloActivosTests(TestCase):
    def test_un_sitio_eliminado_libera_su_pti_y_su_nombre(self):
        viejo = sitio('CL-LI-0000', 'Sitio Prueba')
        viejo.is_deleted = True
        viejo.save()
        nuevo = sitio('CL-LI-0000', 'Sitio Prueba')  # mismo PTI y nombre: ya no choca
        self.assertEqual(Site.objects.filter(pti_cell_id='CL-LI-0000').count(), 2)
        self.assertFalse(nuevo.is_deleted)

    def test_dos_sitios_activos_no_pueden_repetir_pti_ni_nombre(self):
        sitio('P-1', 'Uno')
        with self.assertRaises(ValidationError) as cm:
            sitio('P-1', 'Otro')
        self.assertIn('PTI ID', ' '.join(cm.exception.messages))
        with self.assertRaises(ValidationError) as cm:
            sitio('P-2', 'Uno')
        self.assertIn('nombre', ' '.join(cm.exception.messages))

    def test_sitios_sin_pti_no_chocan_entre_si(self):
        sitio(None, 'A'); sitio(None, 'B')
        self.assertEqual(Site.objects.filter(pti_cell_id__isnull=True).count(), 2)

    def test_no_se_puede_reactivar_un_sitio_si_su_pti_ya_lo_usa_otro_activo(self):
        viejo = sitio('P-9', 'Viejo')
        viejo.is_deleted = True
        viejo.save()
        sitio('P-9', 'Nuevo')
        viejo.is_deleted = False
        with self.assertRaises(ValidationError):
            viejo.save()


class SerializerYApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = User.objects.create_superuser('root', 'r@x.cl', 'pw', user_type='')
        cls.a = sitio('P-1', 'Uno')
        cls.b = sitio('P-2', 'Dos')
        cls.borrado = sitio('P-3', 'Tres')
        cls.borrado.is_deleted = True
        cls.borrado.save()

    def test_serializer_valida_contra_activos_y_excluye_la_propia_instancia(self):
        s = SiteSerializer(self.b, data={'pti_cell_id': 'P-1'}, partial=True)
        self.assertFalse(s.is_valid())
        self.assertIn('pti_cell_id', s.errors)
        # su propio PTI y el de un sitio eliminado sí se pueden usar
        self.assertTrue(SiteSerializer(self.b, data={'pti_cell_id': 'P-2'}, partial=True).is_valid())
        self.assertTrue(SiteSerializer(self.b, data={'pti_cell_id': 'P-3'}, partial=True).is_valid())

    def test_api_responde_400_y_no_500_ante_un_duplicado_activo(self):
        self.client.force_login(self.root)
        r = self.client.put(f'/api/v1/sitios/{self.b.pk}/', data=json.dumps({'name': 'Uno'}),
                            content_type='application/json')
        self.assertEqual(r.status_code, 400, r.content)
        r = self.client.put(f'/api/v1/sitios/{self.b.pk}/', data=json.dumps({'pti_cell_id': 'P-3'}),
                            content_type='application/json')
        self.assertEqual(r.status_code, 200, r.content)


class ModalEdicionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = User.objects.create_superuser('root', 'r@x.cl', 'pw', user_type='')
        cls.sitio = sitio(None, 'San Antonio Oriente')
        sitio('CL-LI-1111', 'Otro Activo')
        borrado = sitio('CL-LI-0000', 'Sitio Prueba', tipo_sitio=Site.POSTE)
        borrado.is_deleted = True
        borrado.save()

    def post(self, pti):
        self.client.force_login(self.root)
        datos = {'pti_cell_id': pti, 'operator_id': '25_230', 'name': 'San Antonio Oriente',
                 'tipo_sitio': 'TORRE', 'tipo_estructura': '', 'alt': '', 'region': '', 'comuna': '',
                 'tipo_coordenada': 'MAN', 'lat': None, 'lon': None}
        return self.client.post(f'/api/v1/sitios/{self.sitio.pk}/edit-modal/', data=json.dumps(datos),
                                content_type='application/json')

    def test_puede_usar_el_pti_de_un_sitio_eliminado(self):
        r = self.post('CL-LI-0000')
        self.assertEqual(r.status_code, 200, r.content)
        self.sitio.refresh_from_db()
        self.assertEqual(self.sitio.pti_cell_id, 'CL-LI-0000')

    def test_el_pti_de_un_sitio_activo_se_rechaza_con_un_mensaje_claro(self):
        r = self.post('CL-LI-1111')
        self.assertEqual(r.status_code, 400)
        self.assertIn('Ya existe un sitio activo con este PTI ID', json.dumps(r.json()))


class ImportacionExcelTests(TestCase):
    def test_actualiza_el_sitio_activo_aunque_exista_un_eliminado_con_el_mismo_pti(self):
        borrado = sitio('P-7', 'Antiguo')
        borrado.is_deleted = True
        borrado.save()
        activo = sitio('P-7', 'Vigente')
        ds = tablib.Dataset(headers=['PTI ID', 'Nombre del Sitio', 'Tipo de sitio', 'Region / Provincia'])
        ds.append(['P-7', 'Vigente', 'TORRE', 'Valparaíso'])
        result = SiteResource().import_data(ds, dry_run=False, raise_errors=False)
        self.assertFalse(result.has_errors() or result.has_validation_errors(), result.row_errors())
        activo.refresh_from_db(); borrado.refresh_from_db()
        self.assertEqual(activo.region, 'Valparaíso')
        self.assertIsNone(borrado.region)
        self.assertEqual(Site.objects.filter(pti_cell_id='P-7').count(), 2)
