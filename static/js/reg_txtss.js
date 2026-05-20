(function () {
    'use strict';

    // ── Row click: navigate to registro detail ──────────────────────────────
    function initRowClick() {
        const tbody = document.querySelector('#registros-table-wrapper tbody');
        if (!tbody || tbody.dataset.rowClickInit) return;
        tbody.dataset.rowClickInit = 'true';

        tbody.addEventListener('click', function (e) {
            // Ignore clicks on buttons, links, selects or their children
            if (e.target.closest('button, a, select, input, .alternativa-cell-container, .fecha-cell-container')) return;

            const row = e.target.closest('tr');
            if (!row) return;

            // Get registro id from the row id span (always present for all roles)
            const idEl = row.querySelector('.reg-txtss-row-id, .reg-txtss-edit-btn');
            if (!idEl) return;

            const id = idEl.dataset.id;
            if (id) window.location.href = `/reg_txtss/${id}/`;
        });

        // Visual hint: pointer cursor on rows
        tbody.querySelectorAll('tr').forEach(tr => {
            tr.style.cursor = 'pointer';
        });
    }

    // ── Alternativa inline edit ─────────────────────────────────────────────
    function initAlternativaEdit() {
        // Show select on text click
        document.addEventListener('click', function (e) {
            const text = e.target.closest('.alternativa-text');
            if (!text) return;
            const container = text.closest('.alternativa-cell-container');
            if (!container) return;
            text.style.display = 'none';
            container.querySelector('.alternativa-select').style.display = 'block';
            container.querySelector('.alternativa-select').focus();
        });

        // Save on change
        document.addEventListener('change', async function (e) {
            const select = e.target;
            if (!select.classList.contains('alternativa-select')) return;

            const registroId = select.dataset.registroId;
            const value = select.value;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            try {
                const response = await fetch(`/reg_txtss/api/registros/${registroId}/update-alternativa/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify({ alternativa: value }),
                });

                const result = await response.json();
                const container = select.closest('.alternativa-cell-container');
                const textSpan = container.querySelector('.alternativa-text');

                if (response.ok && result.success) {
                    const badge = textSpan.querySelector('span');
                    badge.textContent = value || '—';
                    window.Alert.success('Alternativa actualizada', { autoHide: 2000 });
                } else {
                    window.Alert.error(result.message || 'Error al actualizar', { autoHide: 0, dismissible: true });
                }

                select.style.display = 'none';
                textSpan.style.display = 'inline';
            } catch {
                window.Alert.error('Error de conexión', { autoHide: 0, dismissible: true });
                select.style.display = 'none';
                const textSpan = select.closest('.alternativa-cell-container').querySelector('.alternativa-text');
                textSpan.style.display = 'inline';
            }
        });

        // Hide select on blur
        document.addEventListener('blur', function (e) {
            if (!e.target.classList.contains('alternativa-select')) return;
            setTimeout(() => {
                const container = e.target.closest('.alternativa-cell-container');
                if (!container) return;
                e.target.style.display = 'none';
                container.querySelector('.alternativa-text').style.display = 'inline';
            }, 150);
        }, true);
    }

    // ── Fecha inline edit ───────────────────────────────────────────────────
    function initFechaEdit() {
        document.addEventListener('click', function (e) {
            const btn = e.target.closest('.fecha-edit-btn');
            if (!btn) return;
            const container = btn.closest('.fecha-cell-container');
            if (!container) return;
            const input = container.querySelector('.fecha-input');
            input.style.display = 'block';
            input.focus();
        });

        document.addEventListener('change', async function (e) {
            const input = e.target;
            if (!input.classList.contains('fecha-input')) return;

            const registroId = input.dataset.registroId;
            const value = input.value;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            try {
                const response = await fetch(`/reg_txtss/api/registros/${registroId}/update-fecha/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                    body: JSON.stringify({ fecha: value }),
                });
                const result = await response.json();
                const container = input.closest('.fecha-cell-container');
                const textSpan = container.querySelector('.fecha-text');

                if (response.ok && result.success) {
                    textSpan.textContent = result.fecha;
                    window.Alert.success('Fecha actualizada', { autoHide: 2000 });
                } else {
                    window.Alert.error(result.message || 'Error al actualizar', { autoHide: 0, dismissible: true });
                }
                input.style.display = 'none';
            } catch {
                window.Alert.error('Error de conexión', { autoHide: 0, dismissible: true });
                input.style.display = 'none';
            }
        });

        document.addEventListener('blur', function (e) {
            if (!e.target.classList.contains('fecha-input')) return;
            setTimeout(() => {
                if (e.target.closest('.fecha-cell-container')) {
                    e.target.style.display = 'none';
                }
            }, 150);
        }, true);
    }

    // ── Copy registro ───────────────────────────────────────────────────────
    function initCopy() {
        document.addEventListener('click', function (e) {
            const btn = e.target.closest('.reg-txtss-copy-btn');
            if (!btn) return;

            const id = btn.dataset.id;
            const alt = btn.dataset.alternativa || 'A';
            const orden = ['A', 'B', 'C', 'D', 'E'];
            const siguiente = orden[orden.indexOf(alt) + 1];

            if (!siguiente) {
                window.Alert.error(`No hay alternativa después de ${alt}`, { autoHide: 3000 });
                return;
            }

            window.Alert.confirm(
                `¿Crear una copia de este registro con alternativa ${siguiente}?`,
                async function () {
                    btn.disabled = true;
                    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                    try {
                        const response = await fetch(`/reg_txtss/api/registros/${id}/copy/`, {
                            method: 'POST',
                            headers: { 'X-CSRFToken': csrfToken },
                        });
                        const result = await response.json();
                        if (response.ok && result.success) {
                            window.Alert.success(result.message, { autoHide: 2500 });
                            setTimeout(() => window.location.reload(), 1200);
                        } else {
                            window.Alert.error(result.message || 'Error al copiar', { autoHide: 0, dismissible: true });
                            btn.disabled = false;
                        }
                    } catch {
                        window.Alert.error('Error de conexión', { autoHide: 0, dismissible: true });
                        btn.disabled = false;
                    }
                },
                null,
                {
                    title: 'Copiar registro',
                    confirmText: 'Crear copia',
                    cancelText: 'Cancelar',
                    type: 'info',
                    confirmClass: 'btn-save',
                    icon: 'fa-solid fa-copy',
                }
            );
        });
    }

    // ── Delete registro ─────────────────────────────────────────────────────
    function initDelete() {
        document.addEventListener('click', function (e) {
            const btn = e.target.closest('.reg-txtss-delete-btn');
            if (!btn) return;

            const id = btn.dataset.id;
            const nombre = btn.dataset.nombre || 'este registro';

            window.Alert.confirm(
                `¿Ocultar el registro "${nombre}"? Podrá ser recuperado desde el administrador.`,
                async function () {
                    btn.disabled = true;
                    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                    try {
                        const response = await fetch(`/reg_txtss/api/registros/${id}/delete/`, {
                            method: 'POST',
                            headers: { 'X-CSRFToken': csrfToken },
                        });
                        const result = await response.json();
                        if (response.ok && result.success) {
                            window.Alert.success('Registro ocultado', { autoHide: 2500 });
                            setTimeout(() => window.location.reload(), 1200);
                        } else {
                            window.Alert.error(result.message || 'Error al ocultar', { autoHide: 0, dismissible: true });
                            btn.disabled = false;
                        }
                    } catch {
                        window.Alert.error('Error de conexión', { autoHide: 0, dismissible: true });
                        btn.disabled = false;
                    }
                },
                null,
                {
                    title: 'Ocultar registro',
                    confirmText: 'Ocultar',
                    cancelText: 'Cancelar',
                    type: 'warning',
                    confirmClass: 'btn-warning',
                    icon: 'fa-solid fa-eye-slash',
                }
            );
        });
    }

    // ── Edit modal ──────────────────────────────────────────────────────────
    function initEditModal() {
        const modal = document.getElementById('reg-txtss-edit-modal');
        if (!modal) return;

        // Open modal and load form
        document.addEventListener('click', async function (e) {
            const btn = e.target.closest('.reg-txtss-edit-btn');
            if (!btn) return;

            const id = btn.dataset.id;
            const content = document.getElementById('reg-txtss-edit-content');
            content.innerHTML = '<span class="loading loading-spinner loading-md"></span>';
            modal.showModal();

            try {
                const response = await fetch(`/reg_txtss/api/registros/${id}/edit-form/`);
                if (response.ok) {
                    content.innerHTML = await response.text();
                    attachEditFormSubmit(id);
                } else {
                    content.innerHTML = '<p class="text-error">Error al cargar formulario.</p>';
                }
            } catch {
                content.innerHTML = '<p class="text-error">Error de conexión.</p>';
            }
        });
    }

    function attachEditFormSubmit(registroId) {
        const form = document.getElementById('reg-txtss-edit-form');
        if (!form) return;

        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            const submitBtn = form.querySelector('#reg-txtss-edit-submit');
            if (submitBtn) submitBtn.disabled = true;

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            try {
                const response = await fetch(`/reg_txtss/api/registros/${registroId}/update/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken },
                    body: new FormData(form),
                });
                const result = await response.json();

                if (response.ok && result.success) {
                    document.getElementById('reg-txtss-edit-modal').close();
                    window.Alert.success('Registro actualizado', { autoHide: 2000 });
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    window.Alert.error(result.message || 'Error al guardar', { autoHide: 0, dismissible: true });
                    if (submitBtn) submitBtn.disabled = false;
                }
            } catch {
                window.Alert.error('Error de conexión', { autoHide: 0, dismissible: true });
                if (submitBtn) submitBtn.disabled = false;
            }
        });
    }

    // ── Formatear registro ──────────────────────────────────────────────────
    function initFormatear() {
        const modal = document.getElementById('reg-txtss-formatear-modal');
        if (!modal) return;

        const toggle = document.getElementById('reg-txtss-formatear-toggle');
        const btnConfirm = document.getElementById('reg-txtss-formatear-confirm');
        const btnCancel = document.getElementById('reg-txtss-formatear-cancel');
        let formatearUrl = null;

        document.addEventListener('click', async function (e) {
            const btn = e.target.closest('.reg-txtss-formatear-btn');
            if (!btn) return;
            e.stopPropagation();
            formatearUrl = btn.dataset.url;
            const nombreEl = document.getElementById('reg-txtss-formatear-nombre');
            const resumenEl = document.getElementById('reg-txtss-formatear-resumen');
            if (nombreEl) nombreEl.textContent = btn.dataset.nombre || '';
            if (resumenEl) resumenEl.innerHTML = '<span class="loading loading-spinner loading-xs"></span>';
            toggle.checked = false;
            btnConfirm.disabled = true;
            btnConfirm.innerHTML = 'Formatear';
            modal.showModal();

            // Cargar resumen de datos a eliminar
            if (btn.dataset.resumenUrl && resumenEl) {
                try {
                    const resp = await fetch(btn.dataset.resumenUrl);
                    const data = await resp.json();
                    const items = [];
                    if (data.widgets > 0) items.push(`<span class="badge badge-warning badge-sm">${data.widgets} formulario${data.widgets !== 1 ? 's' : ''}</span>`);
                    if (data.fotos > 0)   items.push(`<span class="badge badge-info badge-sm">${data.fotos} foto${data.fotos !== 1 ? 's' : ''}</span>`);
                    if (data.mapas > 0)   items.push(`<span class="badge badge-ghost badge-sm">${data.mapas} mapa${data.mapas !== 1 ? 's' : ''}</span>`);
                    resumenEl.innerHTML = items.length ? items.join('') : '<span class="text-xs text-base-content/50">Sin datos registrados</span>';
                } catch {
                    resumenEl.innerHTML = '';
                }
            }
        });

        toggle.addEventListener('change', function () {
            btnConfirm.disabled = !this.checked;
        });

        btnCancel.addEventListener('click', function () {
            modal.close();
        });

        modal.addEventListener('close', function () {
            toggle.checked = false;
            btnConfirm.disabled = true;
            btnConfirm.innerHTML = 'Formatear';
            formatearUrl = null;
        });

        btnConfirm.addEventListener('click', async function () {
            if (!formatearUrl) return;
            btnConfirm.disabled = true;
            btnConfirm.innerHTML = '<span class="loading loading-spinner loading-xs"></span> Formateando...';
            try {
                const csrf = document.querySelector('[name=csrfmiddlewaretoken]');
                const resp = await fetch(formatearUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrf ? csrf.value : '',
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                });
                const data = await resp.json();
                modal.close();
                if (data.success) {
                    window.Alert && window.Alert.success('Registro formateado correctamente');
                    setTimeout(() => window.location.reload(), 800);
                } else {
                    window.Alert && window.Alert.error(data.message || 'Error al formatear');
                }
            } catch (e) {
                modal.close();
                window.Alert && window.Alert.error('Error de conexión');
            }
        });
    }

    // ── Mapa de registros ───────────────────────────────────────────────────
    function initMapaRegistros() {
        const btn = document.getElementById('reg-txtss-mapa-btn');
        const modal = document.getElementById('reg-txtss-mapa-modal');
        if (!btn || !modal) return;

        let map = null;
        let normalMarkers = [];  // {marker, estado, props} — coords desde widget/fallback
        let azulMarkers = [];    // {marker, props} — coords mandato, color azul
        let initialized = false;

        const COLORS = {
            amarillo: '#ca8a04',
            verde:    '#16a34a',
            rojo:     '#dc2626',
            azul:     '#3b82f6',
        };


        function makeIcon(color, letter) {
            const size = 20;
            const inner = letter
                ? `<span style="font-size:9px;font-weight:bold;color:white;line-height:1;">${letter}</span>`
                : '';
            return L.divIcon({
                className: '',
                html: `<div style="width:${size}px;height:${size}px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;">${inner}</div>`,
                iconSize: [size, size],
                iconAnchor: [size / 2, size / 2],
                popupAnchor: [0, -(size / 2 + 4)],
            });
        }

        function filterMarkers() {
            const show = {
                amarillo: document.getElementById('mapa-toggle-amarillo')?.checked,
                verde:    document.getElementById('mapa-toggle-verde')?.checked,
                rojo:     document.getElementById('mapa-toggle-rojo')?.checked,
            };
            const query = (document.getElementById('mapa-buscar')?.value || '').toLowerCase().trim();
            normalMarkers.forEach(({ marker, estado, props }) => {
                const matchColor = show[estado];
                const matchSearch = !query || [props.pti_id, props.operador_id, props.nombre]
                    .some(v => v && v.toLowerCase().includes(query));
                if (matchColor && matchSearch) {
                    if (!map.hasLayer(marker)) marker.addTo(map);
                } else {
                    if (map.hasLayer(marker)) map.removeLayer(marker);
                }
            });
        }

        function applyAzulMode(on) {
            if (on) {
                azulMarkers.forEach(({ marker }) => { if (!map.hasLayer(marker)) marker.addTo(map); });
            } else {
                azulMarkers.forEach(({ marker }) => { if (map.hasLayer(marker)) map.removeLayer(marker); });
            }
        }

        const STORAGE_KEY = 'reg-txtss-mapa-filtros';

        function saveFilters() {
            const state = {
                amarillo: document.getElementById('mapa-toggle-amarillo')?.checked ?? true,
                verde:    document.getElementById('mapa-toggle-verde')?.checked ?? true,
                rojo:     document.getElementById('mapa-toggle-rojo')?.checked ?? true,
                azul:     document.getElementById('mapa-toggle-azul')?.checked ?? false,
            };
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        }

        function loadFilters() {
            try {
                const raw = localStorage.getItem(STORAGE_KEY);
                if (!raw) return;
                const state = JSON.parse(raw);
                const set = (id, val) => { const el = document.getElementById(id); if (el && val !== undefined) el.checked = val; };
                set('mapa-toggle-amarillo', state.amarillo);
                set('mapa-toggle-verde',    state.verde);
                set('mapa-toggle-rojo',     state.rojo);
                set('mapa-toggle-azul',     state.azul);
            } catch (_) {}
        }

        function fitVisibleMarkers() {
            if (!map) return;
            const latlngs = [];
            normalMarkers.filter(({ marker }) => map.hasLayer(marker)).forEach(({ marker }) => latlngs.push(marker.getLatLng()));
            azulMarkers.filter(({ marker }) => map.hasLayer(marker)).forEach(({ marker }) => latlngs.push(marker.getLatLng()));
            if (latlngs.length) map.fitBounds(L.latLngBounds(latlngs), { padding: [30, 30] });
        }

        function loadLeaflet() {
            return new Promise(resolve => {
                if (window.L) { resolve(); return; }
                if (!document.querySelector('link[href*="leaflet.css"]')) {
                    const link = document.createElement('link');
                    link.rel = 'stylesheet';
                    link.href = window.LEAFLET_CSS_URL;
                    document.head.appendChild(link);
                }
                const script = document.createElement('script');
                script.src = window.LEAFLET_JS_URL;
                script.onload = resolve;
                document.head.appendChild(script);
            });
        }

        async function initMap() {
            if (initialized) return;
            initialized = true;
            await loadLeaflet();

            map = L.map('reg-txtss-mapa-container', { zoomControl: true });

            const streets = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap',
                maxZoom: 19,
                referrerPolicy: 'origin',
            });
            const satellite = L.tileLayer(
                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                { attribution: 'Tiles © Esri', maxZoom: 19 }
            );
            streets.addTo(map);
            L.control.layers({ 'Calles': streets, 'Satélite': satellite }).addTo(map);

            try {
                const resp = await fetch('/reg_txtss/api/mapa-registros/');
                const geojson = await resp.json();

                const bounds = [];
                geojson.features.forEach(f => {
                    const [lon, lat] = f.geometry.coordinates;
                    const p = f.properties;

                    const popup = `<div style="min-width:160px;">
                        <div style="font-weight:bold;margin-bottom:4px;">${p.nombre || '—'}</div>
                        ${p.pti_id ? `<div style="font-size:0.78em;color:#555;">${p.pti_id}${p.operador_id ? ' · ' + p.operador_id : ''}</div>` : ''}
                        ${p.alternativa ? `<div style="font-size:0.78em;">Alt: ${p.alternativa}</div>` : ''}
                        ${p.fecha ? `<div style="font-size:0.78em;">Fecha: ${p.fecha}</div>` : ''}
                        <a href="#" onclick="verRegistroDesdeMapo(${p.id});return false;" style="font-size:0.82em;color:#3b82f6;text-decoration:underline;">Ver registro</a>
                    </div>`;

                    // Marcador normal (coloreado por estado, coords widget o fallback)
                    const letra = p.estado !== 'rojo' ? (p.alternativa || '') : '';
                    const zIndex = p.estado === 'amarillo' ? 200 : p.estado === 'verde' ? 100 : 0;
                    const normalMarker = L.marker([lat, lon], { icon: makeIcon(COLORS[p.estado] || '#888', letra), zIndexOffset: zIndex });
                    normalMarker.bindPopup(popup);
                    normalMarker.addTo(map);
                    normalMarkers.push({ marker: normalMarker, estado: p.estado, props: p });
                    bounds.push([lat, lon]);

                    // Marcador azul (coords mandato, se muestra solo en modo azul)
                    if (p.lat_man !== null && p.lon_man !== null) {
                        const popupMandato = `<div style="min-width:160px;">
                            <div style="font-weight:bold;margin-bottom:4px;">${p.nombre || '—'}</div>
                            ${p.pti_id ? `<div style="font-size:0.78em;color:#555;">${p.pti_id}${p.operador_id ? ' · ' + p.operador_id : ''}</div>` : ''}
                        </div>`;
                        const azulMarker = L.marker([p.lat_man, p.lon_man], { icon: makeIcon(COLORS.azul, 'M') });
                        azulMarker.bindPopup(popupMandato);
                        azulMarkers.push({ marker: azulMarker, props: p });
                    }
                });

                if (bounds.length) map.fitBounds(bounds, { padding: [30, 30] });
                else map.setView([-33.45, -70.66], 6);
            } catch (e) {
                console.error('Error cargando mapa:', e);
            }

            // Poblar select de sitios
            const sitioSelect = document.getElementById('mapa-sitio-select');
            if (sitioSelect) {
                const sorted = [...normalMarkers].sort((a, b) =>
                    (a.props.nombre || '').localeCompare(b.props.nombre || ''));
                sorted.forEach(({ props }) => {
                    const opt = document.createElement('option');
                    opt.value = props.id;
                    opt.textContent = [props.pti_id, props.operador_id, props.nombre].filter(Boolean).join(' · ');
                    sitioSelect.appendChild(opt);
                });
                sitioSelect.addEventListener('change', function () {
                    const id = parseInt(this.value);
                    if (!id) return;
                    const found = normalMarkers.find(m => m.props.id === id);
                    if (found) {
                        if (!map.hasLayer(found.marker)) found.marker.addTo(map);
                        map.flyTo(found.marker.getLatLng(), 17, { duration: 0.8 });
                        setTimeout(() => found.marker.openPopup(), 900);
                    }
                    this.value = '';
                });
            }

            ['mapa-toggle-amarillo', 'mapa-toggle-verde', 'mapa-toggle-rojo'].forEach(id => {
                document.getElementById(id)?.addEventListener('change', () => { filterMarkers(); saveFilters(); });
            });
            document.getElementById('mapa-toggle-azul')?.addEventListener('change', function () {
                applyAzulMode(this.checked);
                saveFilters();
            });
            document.getElementById('mapa-buscar')?.addEventListener('input', filterMarkers);
            document.getElementById('mapa-fit-btn')?.addEventListener('click', fitVisibleMarkers);

            // Restaurar estado guardado y aplicar filtros
            loadFilters();
            filterMarkers();
            applyAzulMode(document.getElementById('mapa-toggle-azul')?.checked || false);
        }

        btn.addEventListener('click', function (e) {
            e.preventDefault();
            modal.showModal();
            setTimeout(() => {
                initMap().then(() => {
                    if (map) map.invalidateSize();
                });
            }, 50);
        });

        modal.addEventListener('close', function () {
            if (map) map.invalidateSize();
        });
    }

    // ── Init ────────────────────────────────────────────────────────────────
    function init() {
        initRowClick();
        initAlternativaEdit();
        initFechaEdit();
        initCopy();
        initDelete();
        initEditModal();
        initFormatear();
        initMapaRegistros();
    }

    init();
    document.addEventListener('htmx:afterSwap', function () {
        initRowClick();
    });
})();

function flashRow(id) {
    if (!document.getElementById('row-flash-style')) {
        const style = document.createElement('style');
        style.id = 'row-flash-style';
        style.textContent = '@keyframes rowFlash{0%,100%{background-color:inherit;outline:none;}50%{background-color:#facc15;outline:3px solid #f59e0b;}}';
        document.head.appendChild(style);
    }
    const idEl = document.querySelector(`.reg-txtss-row-id[data-id="${id}"]`);
    const row = idEl ? idEl.closest('tr') : null;
    if (!row) return;
    row.scrollIntoView({ behavior: 'smooth', block: 'center' });
    row.style.animation = 'none';
    void row.offsetWidth;
    row.style.animation = 'rowFlash 0.6s ease-in-out 8';
    row.addEventListener('animationend', function () { row.style.animation = ''; row.style.outline = ''; }, { once: true });
}

// Al cargar la página, verificar si hay ?highlight=<id> en la URL
(function initHighlight() {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('highlight');
    if (!id) return;
    // Limpiar el parámetro de la URL sin recargar
    params.delete('highlight');
    const newUrl = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
    history.replaceState(null, '', newUrl);
    flashRow(parseInt(id, 10));
})();

// Global: llamado desde onclick en popup del mapa
window.verRegistroDesdeMapo = function (id) {
    const modal = document.getElementById('reg-txtss-mapa-modal');
    if (modal) modal.close();

    const listPath = window.location.pathname;
    fetch(`/reg_txtss/api/registros/${id}/locate/?list_path=${encodeURIComponent(listPath)}`)
        .then(r => r.json())
        .then(data => {
            const params = new URLSearchParams(window.location.search);
            params.set('page', data.page);
            params.set('highlight', id);
            window.location.href = window.location.pathname + '?' + params.toString();
        });
};
