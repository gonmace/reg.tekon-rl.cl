// Construcción Sitios: listado y cabecera de visita (nueva visita, editar, eliminar, navegar).
// Los handlers se adjuntan aquí (no en <script> del HTML inyectado): ver CLAUDE.md.
(function () {
  var cfg = document.getElementById('obra-config');
  if (!cfg) return;
  var BASE = cfg.dataset.baseUrl;               // /reg_construccion/
  function csrf() {
    var el = cfg.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }
  function toast(msg, ok) {
    if (window.Alert) (ok ? window.Alert.success : window.Alert.error)(msg, { autoHide: 3500 });
    else window.alert(msg);
  }
  function post(url, body) {
    return fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' },
      body: body,
    }).then(function (r) { return r.json().then(function (j) { return { ok: r.ok, data: j }; }); });
  }
  function hoy() {
    var d = new Date();
    var m = ('0' + (d.getMonth() + 1)).slice(-2), day = ('0' + d.getDate()).slice(-2);
    return d.getFullYear() + '-' + m + '-' + day;
  }

  // ── Nueva visita ───────────────────────────────────────────────────────────
  var modalVisita = document.getElementById('obra-visita-modal');
  var visitaBaseId = null;
  function abrirNuevaVisita(id, nombre) {
    visitaBaseId = id;
    document.getElementById('obra-visita-sitio').textContent = nombre || '';
    document.getElementById('obra-visita-fecha').value = hoy();
    document.getElementById('obra-visita-error').classList.add('hidden');
    modalVisita.showModal();
  }
  document.getElementById('obra-visita-cancel').addEventListener('click', function () { modalVisita.close(); });
  document.getElementById('obra-visita-crear').addEventListener('click', function () {
    var btn = this, err = document.getElementById('obra-visita-error');
    var fecha = document.getElementById('obra-visita-fecha').value;
    if (!fecha) { err.textContent = 'Indica la fecha del reporte.'; err.classList.remove('hidden'); return; }
    btn.disabled = true;
    post(BASE + 'api/registros/' + visitaBaseId + '/nueva-visita/', JSON.stringify({ fecha: fecha }))
      .then(function (res) {
        if (res.ok && res.data.success) { window.location.href = res.data.redirect_url; return; }
        err.textContent = res.data.message || 'No se pudo crear el reporte.';
        err.classList.remove('hidden'); btn.disabled = false;
      })
      .catch(function () { err.textContent = 'Error de red.'; err.classList.remove('hidden'); btn.disabled = false; });
  });

  // ── Editar datos de la visita ──────────────────────────────────────────────
  var modalEdit = document.getElementById('obra-edit-modal');
  var editContent = document.getElementById('obra-edit-content');
  function abrirEditar(id) {
    editContent.innerHTML = '<span class="loading loading-spinner loading-sm"></span>';
    modalEdit.showModal();
    fetch(BASE + 'api/registros/' + id + '/edit-form/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { if (!r.ok) throw new Error(); return r.text(); })
      .then(function (html) {
        editContent.innerHTML = html;
        var form = document.getElementById('obra-edit-form');
        if (!form) return;
        document.getElementById('obra-edit-cancel').addEventListener('click', function () { modalEdit.close(); });
        form.addEventListener('submit', function (e) {
          e.preventDefault();
          var err = document.getElementById('obra-edit-error');
          err.classList.add('hidden');
          post(BASE + 'api/registros/' + form.dataset.registroId + '/update/', new FormData(form))
            .then(function (res) {
              if (res.ok && res.data.success) { window.location.reload(); return; }
              err.textContent = res.data.message || 'No se pudo guardar.';
              err.classList.remove('hidden');
            });
        });
      })
      .catch(function () { editContent.textContent = 'No se pudo cargar el formulario.'; });
  }

  // ── Eliminar (superusuario) ────────────────────────────────────────────────
  function eliminar(id, nombre) {
    if (!window.confirm('¿Eliminar el reporte ' + nombre + '?')) return;
    post(BASE + 'api/registros/' + id + '/delete/', null).then(function (res) {
      if (res.ok && res.data.success) window.location.reload();
      else toast(res.data.message || 'No se pudo eliminar.', false);
    });
  }

  // ── Tabla de sitios → panel de visitas ─────────────────────────────────────
  var panel = document.getElementById('obra-visitas-panel');
  function marcarSitio(id) {
    document.querySelectorAll('.reg-obra-sitios-table tbody tr').forEach(function (tr) {
      var m = tr.querySelector('.obra-sitio-id');
      tr.classList.toggle('row-seleccionada', !!m && !!id && m.dataset.id === String(id));
    });
  }
  function cargarVisitas(id, url) {
    if (!panel || !window.htmx) { window.location.href = BASE + '?sitio=' + id; return; }
    window.htmx.ajax('GET', url, { target: '#obra-visitas-panel', swap: 'innerHTML' });
    panel.dataset.sitio = id;
    marcarSitio(id);
    // La selección queda en la URL (compartible y «Atrás» vuelve a este sitio).
    var u = new URL(window.location.href);
    u.searchParams.set('sitio', id);
    window.history.replaceState(null, '', u);
    if (window.matchMedia('(max-width: 768px)').matches) panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  marcarSitio(panel && panel.dataset.sitio);
  // La búsqueda/paginación de sitios re-pinta la tabla: se vuelve a resaltar la fila elegida.
  document.body.addEventListener('htmx:afterSwap', function () { marcarSitio(panel && panel.dataset.sitio); });

  // Delegación: las filas se re-pintan con HTMX (búsqueda, paginación, orden).
  document.addEventListener('click', function (e) {
    var t = e.target.closest('.obra-nueva-btn, .obra-edit-btn, .obra-delete-btn');
    if (t) {
      e.stopPropagation();
      if (t.classList.contains('obra-nueva-btn')) abrirNuevaVisita(t.dataset.id, t.dataset.nombre);
      else if (t.classList.contains('obra-edit-btn')) abrirEditar(t.dataset.id);
      else eliminar(t.dataset.id, t.dataset.nombre);
      return;
    }
    // click en una fila (no si fue un enlace/botón/campo): sitio → ver sus visitas; visita → abrirla
    if (e.target.closest('a, button, input, select, label')) return;
    var row = e.target.closest('tbody tr');
    if (!row) return;
    var sitio = row.querySelector('.obra-sitio-id');
    if (sitio) { cargarVisitas(sitio.dataset.id, sitio.dataset.url); return; }
    var marca = row.querySelector('.obra-row-id');
    if (marca) window.location.href = BASE + marca.dataset.id + '/';
  });

  // ── Selector de visitas en la cabecera ─────────────────────────────────────
  var sel = document.getElementById('obra-visita-selector');
  if (sel) sel.addEventListener('change', function () { window.location.href = BASE + sel.value + '/'; });
})();
