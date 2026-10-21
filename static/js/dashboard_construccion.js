/* Mapa de obras del dashboard (Construcción Sitios). Leaflet se carga bajo demanda. */
(function () {
    'use strict';

    var el = document.getElementById('dashboard-mapa');
    if (!el) return;

    var COLORES = {
        construccion: '#0ea5e9',
        paralizado: '#f59e0b',
        cancelado: '#6b7280',
        concluido: '#22c55e',
    };

    function loadLeaflet() {
        return new Promise(function (resolve) {
            if (window.L) { resolve(); return; }
            if (!document.querySelector('link[href*="leaflet.css"]')) {
                var link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = window.LEAFLET_CSS_URL;
                document.head.appendChild(link);
            }
            var script = document.createElement('script');
            script.src = window.LEAFLET_JS_URL;
            script.onload = resolve;
            document.head.appendChild(script);
        });
    }

    function esc(valor) {
        var d = document.createElement('div');
        d.textContent = valor == null ? '' : String(valor);
        return d.innerHTML;
    }

    function popup(p) {
        return '<div style="min-width:170px;line-height:1.35">' +
            '<strong>' + esc(p.pti) + ' · ' + esc(p.nombre) + '</strong><br>' +
            '<span style="color:' + (COLORES[p.estado] || '#6b7280') + '">● ' + esc(p.estado_label) + '</span> · ' +
            esc(Math.round(p.avance)) + '% de avance<br>' +
            (p.contratista ? esc(p.contratista) + '<br>' : '') +
            (p.ultima_fecha ? 'Última visita: ' + esc(p.ultima_fecha) + '<br>' : '') +
            '<a href="' + esc(p.url) + '">Ver visitas →</a></div>';
    }

    async function init() {
        await loadLeaflet();
        var map = L.map(el, { scrollWheelZoom: false }).setView([-33.45, -70.66], 5);

        var calles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19, attribution: '© OpenStreetMap',
            referrerPolicy: 'origin',  // OSM bloquea las teselas sin Referer ("Access blocked")
        }).addTo(map);
        var satelite = L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            { maxZoom: 19, attribution: 'Esri' });
        L.control.layers({ 'Calles': calles, 'Satélite': satelite }).addTo(map);

        // la rueda del mouse solo hace zoom tras hacer clic en el mapa (no atrapa el scroll de la página)
        map.on('click', function () { map.scrollWheelZoom.enable(); });
        map.on('mouseout', function () { map.scrollWheelZoom.disable(); });

        var data;
        try {
            var resp = await fetch(el.dataset.url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
            if (!resp.ok) throw new Error(resp.status);
            data = await resp.json();
        } catch (e) {
            data = { features: [] };
        }

        var puntos = [];
        data.features.forEach(function (f) {
            var p = f.properties;
            var ll = [f.geometry.coordinates[1], f.geometry.coordinates[0]];
            var color = COLORES[p.estado] || '#6b7280';
            L.circleMarker(ll, {
                radius: 7 + Math.round((p.avance || 0) / 25),  // 7–11 px: más grande a mayor avance
                color: '#ffffff', weight: 2, fillColor: color, fillOpacity: 0.9,
            }).bindPopup(popup(p)).addTo(map);
            puntos.push(ll);
        });

        if (puntos.length) {
            map.fitBounds(L.latLngBounds(puntos), { padding: [30, 30], maxZoom: 13 });
        } else {
            var vacio = document.getElementById('dashboard-mapa-vacio');
            if (vacio) { vacio.classList.remove('hidden'); vacio.classList.add('flex'); }
        }
    }

    init();
})();
