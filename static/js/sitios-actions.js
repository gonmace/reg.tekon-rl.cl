// Acciones de la tabla de sitios: crear, editar, eliminar e importar Excel.
// La tabla la renderiza django-tables2; este script solo maneja botones/modales.

(function () {
  const editModal = document.getElementById('edit_site_modal');
  const editModalContent = document.getElementById('modal-content');
  const editModalTitle = document.getElementById('edit_site_modal_title');
  const importModal = document.getElementById('import_site_modal');

  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^|;\\s*)' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[2]) : null;
  }

  function reloadTable() {
    const wrapper = document.getElementById('sitios-table-wrapper');
    if (wrapper && window.htmx) {
      htmx.ajax('GET', window.location.pathname + window.location.search, {
        target: '#sitios-table-wrapper',
        swap: 'innerHTML',
      });
    } else {
      window.location.reload();
    }
  }

  // Expuesto globalmente porque el form de SiteForm usa onclick="closeModal()"
  window.closeModal = function () {
    editModal?.close();
  };

  function bindFormSubmit(form, url, successMsg) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const payload = {};
      const COORD_FIELDS = [
        'lat_man', 'lon_man',
        'lat_ing', 'lon_ing',
        'lat_con', 'lon_con',
        'lat', 'lon',  // del form custom (selector)
      ];
      formData.forEach((v, k) => {
        if (COORD_FIELDS.includes(k)) {
          const n = parseFloat(String(v).replace(',', '.').trim());
          payload[k] = isNaN(n) ? null : n;
        } else {
          payload[k] = v;
        }
      });

      fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(payload),
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.success) {
            window.Alert?.success(successMsg || data.message, { autoHide: 3000 });
            editModal.close();
            reloadTable();
          } else {
            window.Alert?.error(data.message || 'Error al guardar.');
          }
        })
        .catch(() => window.Alert?.error('Error de red o del servidor.'));
    });
  }

  // Mapeo tipo → campos del modelo (debe coincidir con TIPO_TO_FIELDS en forms.py)
  const TIPO_TO_FIELDS = {
    MAN: ['lat_man', 'lon_man'],
    ING: ['lat_ing', 'lon_ing'],
    CON: ['lat_con', 'lon_con'],
  };

  // Coords permitidas según tipo de sitio
  const TIPOS_COORD_POR_SITIO = {
    POSTE: ['MAN'],
    TORRE: ['MAN', 'ING', 'CON'],
  };

  function bindTipoSelector(siteData) {
    // Crispy renderiza un id="-id-" duplicado, por eso seleccionamos por name
    const form = document.getElementById('edit-site-form');
    if (!form) return;
    const tipoCoordSel = form.querySelector('[name="tipo_coordenada"]');
    const tipoSitioSel = form.querySelector('[name="tipo_sitio"]');
    const latIn = form.querySelector('[name="lat"]');
    const lonIn = form.querySelector('[name="lon"]');
    if (!tipoCoordSel || !latIn || !lonIn) return;

    // Filtra las opciones del selector de coord según el tipo de sitio actual
    function applyTipoSitioFilter() {
      const allowed = TIPOS_COORD_POR_SITIO[tipoSitioSel?.value] || ['MAN', 'ING', 'CON'];
      [...tipoCoordSel.options].forEach((opt) => {
        opt.hidden = !allowed.includes(opt.value);
        opt.disabled = !allowed.includes(opt.value);
      });
      // Si el seleccionado quedó oculto, cambiar a la primera opción válida
      if (!allowed.includes(tipoCoordSel.value)) {
        tipoCoordSel.value = allowed[0];
        tipoCoordSel.dispatchEvent(new Event('change'));
      }
    }

    function fillCoordsFromTipo() {
      const [latKey, lonKey] = TIPO_TO_FIELDS[tipoCoordSel.value] || ['lat_man', 'lon_man'];
      latIn.value = siteData?.[latKey] ?? '';
      lonIn.value = siteData?.[lonKey] ?? '';
    }

    tipoCoordSel.addEventListener('change', fillCoordsFromTipo);
    tipoSitioSel?.addEventListener('change', applyTipoSitioFilter);
    applyTipoSitioFilter();
  }

  function openEditModal(siteId) {
    fetch(`/api/v1/sitios/${siteId}/edit-modal/`, {
      headers: { 'X-CSRFToken': getCookie('csrftoken'), Accept: 'application/json' },
    })
      .then((r) => r.json())
      .then((data) => {
        if (!data.success) {
          window.Alert?.error('Error al cargar los datos del sitio.');
          return;
        }
        editModalTitle.textContent = 'Editar Sitio';
        editModalContent.innerHTML = data.form_html;
        editModal.showModal();
        const form = document.getElementById('edit-site-form');
        if (form) {
          bindFormSubmit(form, `/api/v1/sitios/${siteId}/edit-modal/`, data.message);
          bindTipoSelector(data.site_data);
        }
      })
      .catch(() => window.Alert?.error('Error de red o del servidor.'));
  }

  function openCreateModal() {
    fetch('/api/v1/sitios/create-modal/', {
      headers: { 'X-CSRFToken': getCookie('csrftoken'), Accept: 'application/json' },
    })
      .then((r) => r.json())
      .then((data) => {
        if (!data.success) {
          window.Alert?.error('Error al cargar el formulario.');
          return;
        }
        editModalTitle.textContent = 'Agregar Sitio';
        editModalContent.innerHTML = data.form_html;
        editModal.showModal();
        const form = document.getElementById('edit-site-form');
        if (form) bindFormSubmit(form, '/api/v1/sitios/create-modal/');
      })
      .catch(() => window.Alert?.error('Error de red o del servidor.'));
  }

  function deleteSite(siteId, siteName) {
    window.Alert?.confirm(
      `¿Estás seguro que deseas eliminar el sitio "${siteName}"?`,
      () => {
        fetch(`/api/v1/sitios/${siteId}/`, {
          method: 'PUT',
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          body: JSON.stringify({ is_deleted: true }),
        })
          .then((r) => r.json())
          .then((data) => {
            if (data.success) {
              window.Alert?.success(data.message, { autoHide: 3000 });
              reloadTable();
            } else {
              window.Alert?.error(data.message || 'Error al eliminar el sitio.');
            }
          })
          .catch(() => window.Alert?.error('Error de red o del servidor.'));
      },
      null,
      { title: 'Eliminar sitio', confirmText: 'Eliminar', confirmClass: 'btn-delete', icon: 'fa-solid fa-trash' }
    );
  }

  // ── Import Excel ───────────────────────────────────────────────────
  const importForm = document.getElementById('importSiteForm');
  const importResult = document.getElementById('importSiteResult');
  const importBtn = document.getElementById('importSiteSubmitBtn');

  if (importForm) {
    importForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const fileInput = document.getElementById('importSiteFile');
      if (!fileInput.files.length) return;

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);

      const originalText = importBtn.innerHTML;
      importBtn.disabled = true;
      importBtn.innerHTML = '<span class="loading loading-spinner loading-xs"></span> Importando...';
      importResult.classList.add('hidden');
      importResult.innerHTML = '';

      fetch('/api/v1/sitios/import/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: formData,
      })
        .then((r) => r.json().then((d) => ({ ok: r.ok, data: d })))
        .then(({ ok, data }) => {
          if (ok && data.success) {
            window.Alert?.success(data.message, { autoHide: 4000 });
            importModal.close();
            importForm.reset();
            reloadTable();
          } else {
            const errorList = (data.errors || []).map((e) => `<li>${e}</li>`).join('');
            importResult.innerHTML = `
              <div class="alert alert-error">
                <div>
                  <div class="font-semibold">${data.message || 'Error al importar.'}</div>
                  ${errorList ? `<ul class="list-disc ml-5 text-xs mt-1">${errorList}</ul>` : ''}
                </div>
              </div>`;
            importResult.classList.remove('hidden');
          }
        })
        .catch(() => {
          importResult.innerHTML = '<div class="alert alert-error">Error de red o del servidor.</div>';
          importResult.classList.remove('hidden');
        })
        .finally(() => {
          importBtn.innerHTML = originalText;
          importBtn.disabled = false;
        });
    });
  }

  // ── Delegación global (sobrevive HTMX swaps y orden de carga) ──────
  document.addEventListener('click', (e) => {
    if (e.target.closest('#addSiteBtn')) {
      e.preventDefault();
      openCreateModal();
      return;
    }
    if (e.target.closest('#importSiteBtn')) {
      e.preventDefault();
      document.getElementById('import_site_modal')?.showModal();
      return;
    }
    const editBtn = e.target.closest('.site-edit-btn');
    if (editBtn) {
      e.preventDefault();
      openEditModal(editBtn.dataset.id);
      return;
    }
    const delBtn = e.target.closest('.site-delete-btn');
    if (delBtn) {
      e.preventDefault();
      deleteSite(delBtn.dataset.id, delBtn.dataset.nombre);
    }
  });
})();
