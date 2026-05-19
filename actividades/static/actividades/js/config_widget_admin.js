(function () {
    'use strict';

    var MAP_TYPES = ['MAP_1', 'MAP_2', 'MAP_3'];

    function fieldRow(id) {
        var el = document.getElementById('id_' + id);
        if (!el) return null;
        // Django admin wraps each field in a .form-row
        return el.closest('.form-row') || el.closest('p') || el.parentElement;
    }

    function applyVisibility(tipo) {
        // Ocultar todas las secciones de config
        document.querySelectorAll('.widget-section').forEach(function (section) {
            section.style.display = 'none';
        });

        if (tipo === 'CAMERA') {
            document.querySelectorAll('.widget-camera').forEach(function (s) {
                s.style.display = '';
            });
        } else if (MAP_TYPES.indexOf(tipo) !== -1) {
            document.querySelectorAll('.widget-map').forEach(function (s) {
                s.style.display = '';
            });

            // Punto 2: solo MAP_2 y MAP_3
            var show2 = (tipo === 'MAP_2' || tipo === 'MAP_3');
            ['map_lat_field_2', 'map_lon_field_2'].forEach(function (id) {
                var row = fieldRow(id);
                if (row) row.style.display = show2 ? '' : 'none';
            });

            // Punto 3: solo MAP_3
            var show3 = (tipo === 'MAP_3');
            ['map_lat_field_3', 'map_lon_field_3'].forEach(function (id) {
                var row = fieldRow(id);
                if (row) row.style.display = show3 ? '' : 'none';
            });
        }
        // FORM: sin configuración extra — nada que mostrar
    }

    document.addEventListener('DOMContentLoaded', function () {
        var tipoSelect = document.getElementById('id_tipo');
        if (!tipoSelect) return;

        applyVisibility(tipoSelect.value);

        tipoSelect.addEventListener('change', function () {
            applyVisibility(this.value);
        });
    });
})();
