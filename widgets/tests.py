from decimal import Decimal

from django import forms
from django.test import SimpleTestCase

from widgets.fields import TextListField
from widgets.widget_types.tabla_avance import (
    PartidasField, TablaAvanceWidget, calcular_serie, normalizar_partidas, redondear,
)

# Partidas del informe CL-VS-1458 (22-12-2025): (nombre, incidencia, % actual de la visita)
CL_VS_1458 = [
    ('Instalación de faenas', 5, 100), ('Replanteo y Trazado', 5, 100),
    ('Excavación para la fundación', 5, 100), ('Enfierradura de la fundación', 15, 100),
    ('Hormigonado de la fundación', 15, 100), ('Relleno y compactado', 5, 50),
    ('Montaje de la Torre', 15, 1), ('Losa Radier de Equipos', 5, 0),
    ('Cierre perimetral', 5, 0), ('Sistema puesta a tierra', 5, 0),
    ('Sistema Eléctrico', 5, 0), ('Línea Eléctrica Provisoria', 5, 0),
    ('Línea Eléctrica definitiva', 5, 30), ('Trabajos Finales / Adicionales', 5, 0),
]


def _visita(filas):
    return [{'id': f'p{i}', 'nombre': n, 'incidencia': inc, 'actual': act}
            for i, (n, inc, act) in enumerate(filas)]


class CalculoAvanceTests(SimpleTestCase):
    def test_total_del_informe_de_ejemplo(self):
        # El PDF muestra 3,0 % en la línea definitiva, pero 5 % × 30 % = 1,5 %:
        # el total correcto es 49,15 → 49,2 % (el PDF suma 50,7 por esa fila).
        resultado = calcular_serie([_visita(CL_VS_1458)])[0]
        self.assertEqual(resultado['total'], Decimal('49.15'))
        self.assertEqual(redondear(resultado['total']), Decimal('49.2'))
        montaje = next(f for f in resultado['filas'] if f['nombre'] == 'Montaje de la Torre')
        self.assertEqual(redondear(montaje['total']), Decimal('0.2'))

    def test_encadena_anterior_y_acumulada(self):
        v1 = _visita([('A', 50, 40), ('B', 50, 0)])
        v2 = _visita([('A', 50, 30), ('B', 50, 20)])
        v3 = _visita([('A', 50, 50), ('B', 50, 10)])
        s = calcular_serie([v1, v2, v3])
        self.assertEqual(s[1]['filas'][0]['anterior'], Decimal('40'))
        self.assertEqual(s[1]['filas'][0]['acumulada'], Decimal('70'))
        self.assertEqual(s[2]['filas'][0]['acumulada'], Decimal('100'))  # tope 100
        self.assertEqual(s[2]['filas'][1]['anterior'], Decimal('20'))

    def test_editar_visita_antigua_se_propaga(self):
        v1 = _visita([('A', 100, 10)])
        v2 = _visita([('A', 100, 10)])
        self.assertEqual(calcular_serie([v1, v2])[1]['total'], Decimal('20'))
        v1[0]['actual'] = 30
        self.assertEqual(calcular_serie([v1, v2])[1]['total'], Decimal('40'))

    def test_visita_sin_datos_hereda_estructura(self):
        v1 = _visita([('A', 60, 50), ('B', 40, 25)])
        s = calcular_serie([v1, []])
        self.assertEqual([f['nombre'] for f in s[1]['filas']], ['A', 'B'])
        self.assertEqual(s[1]['filas'][0]['anterior'], Decimal('50'))
        self.assertEqual(s[1]['filas'][0]['actual'], Decimal('0'))
        self.assertEqual(s[1]['total'], s[0]['total'])

    def test_sitio_sin_partidas(self):
        self.assertEqual(calcular_serie([[]])[0], {'filas': [], 'total': Decimal('0')})


class ValidacionTests(SimpleTestCase):
    def test_normaliza_y_genera_ids(self):
        out = normalizar_partidas([{'nombre': ' A ', 'incidencia': '10,5', 'actual': '5'}])
        self.assertEqual(out[0]['nombre'], 'A')
        self.assertEqual(out[0]['incidencia'], 10.5)
        self.assertTrue(out[0]['id'])

    def test_rechaza_valores_fuera_de_rango_o_sin_nombre(self):
        for fila in ({'nombre': 'A', 'incidencia': 101, 'actual': 0},
                     {'nombre': 'A', 'incidencia': 5, 'actual': -1},
                     {'nombre': '  ', 'incidencia': 5, 'actual': 0}):
            with self.assertRaises(forms.ValidationError):
                normalizar_partidas([fila])

    def test_ids_repetidos(self):
        with self.assertRaises(forms.ValidationError):
            normalizar_partidas([{'id': 'x', 'nombre': 'A', 'incidencia': 1, 'actual': 0},
                                 {'id': 'x', 'nombre': 'B', 'incidencia': 1, 'actual': 0}])

    def test_campo_json(self):
        self.assertEqual(PartidasField().clean('[]'), [])
        with self.assertRaises(forms.ValidationError):
            PartidasField().clean('no es json')
        self.assertEqual(TextListField().clean('[" uno ", "", "dos"]'), ['uno', 'dos'])

    def test_plantilla_debe_sumar_100(self):
        w = TablaAvanceWidget()
        ok = {'plantillas': [{'nombre': 'T', 'partidas': [{'nombre': 'a', 'incidencia': 60},
                                                           {'nombre': 'b', 'incidencia': 40}]}]}
        mal = {'plantillas': [{'nombre': 'T', 'partidas': [{'nombre': 'a', 'incidencia': 60}]}]}
        self.assertEqual(w.validate_config(ok), [])
        self.assertTrue(w.validate_config(mal))
