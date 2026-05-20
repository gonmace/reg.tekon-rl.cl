(function () {
  'use strict';

  // ── CSRF ────────────────────────────────────────────────────────────────
  function getCsrfToken() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : '';
  }

  function postJson(url, body) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify(body),
    });
  }

  function notify(type, message) {
    window.Alert?.[type]?.(message, { autoHide: 4000 });
  }

  // ── Selection ────────────────────────────────────────────────────────────
  function getSelectedIds() {
    return Array.from(document.querySelectorAll('.photo-checkbox:checked')).map((cb) => cb.value);
  }

  function updateBulkBar() {
    const count = getSelectedIds().length;
    const bar = document.getElementById('bulk-actions');
    const counter = document.getElementById('selected-count');
    if (!bar || !counter) return;
    bar.classList.toggle('hidden', count === 0);
    counter.textContent = count;

    const allCbs = document.querySelectorAll('.photo-checkbox');
    const selectAll = document.getElementById('select-all-photos');
    if (selectAll) {
      selectAll.indeterminate = count > 0 && count < allCbs.length;
      selectAll.checked = count > 0 && count === allCbs.length;
    }
  }

  function updateSelectedRings() {
    document.querySelectorAll('[data-photo-id]').forEach((card) => {
      const cb = card.querySelector('.photo-checkbox');
      const ring = card.querySelector('.photo-selected-ring');
      const selectBtn = card.querySelector('.photo-select-btn');
      const checkIcon = card.querySelector('.photo-check-icon');
      const selected = cb && cb.checked;

      if (ring) ring.style.opacity = selected ? '1' : '0';
      if (selectBtn) {
        if (selected) {
          selectBtn.style.backgroundColor = 'oklch(var(--er))';
          selectBtn.style.borderColor = 'oklch(var(--er))';
        } else {
          selectBtn.style.backgroundColor = '';
          selectBtn.style.borderColor = '';
        }
      }
      if (checkIcon) checkIcon.style.opacity = selected ? '1' : '0';
    });
  }

  // ── Reload grid ───────────────────────────────────────────────────────────
  function reloadGrid() {
    const wrapper = document.getElementById('gallery-grid-wrapper');
    if (wrapper && window.htmx) {
      htmx.ajax('GET', window.location.pathname + window.location.search, {
        target: '#gallery-grid-wrapper',
        swap: 'innerHTML',
      });
    } else {
      window.location.reload();
    }
  }

  // ── Lightbox ─────────────────────────────────────────────────────────────
  function openLightbox(btn) {
    const img = document.getElementById('lightbox-img');
    const info = document.getElementById('lightbox-info');
    const modal = document.getElementById('lightbox-modal');
    if (!img || !modal) return;

    img.src = btn.dataset.fullUrl || '';
    const parts = [
      btn.dataset.descripcion,
      btn.dataset.etapa ? `Etapa: ${btn.dataset.etapa}` : '',
      btn.dataset.exifDatetime ? `EXIF: ${btn.dataset.exifDatetime}` : '',
      btn.dataset.created ? `Subida: ${btn.dataset.created}` : '',
    ].filter(Boolean);
    if (info) info.textContent = parts.join('  ·  ');
    modal.showModal();
  }

  // ── Event delegation ─────────────────────────────────────────────────────
  document.addEventListener('click', function (e) {
    // Select button (circular) → toggle selection
    const selectBtn = e.target.closest('.photo-select-btn');
    if (selectBtn) {
      e.stopPropagation();
      const cb = selectBtn.querySelector('.photo-checkbox');
      if (cb) {
        cb.checked = !cb.checked;
        updateBulkBar();
        updateSelectedRings();
      }
      return;
    }

    // Image thumbnail → lightbox
    const thumb = e.target.closest('.photo-thumb');
    if (thumb) {
      openLightbox(thumb);
      return;
    }

    // Select-all checkbox
    if (e.target.id === 'select-all-photos') {
      return; // handled by change event
    }
  });

  // Select-all / deselect via change event
  document.addEventListener('change', function (e) {
    if (e.target.id === 'select-all-photos') {
      const checked = e.target.checked;
      document.querySelectorAll('.photo-checkbox').forEach((cb) => { cb.checked = checked; });
      updateBulkBar();
      updateSelectedRings();
      return;
    }
    if (e.target.classList.contains('photo-checkbox')) {
      updateBulkBar();
      updateSelectedRings();
    }
  });

  // Select/deselect all buttons
  document.addEventListener('click', function (e) {
    if (e.target.closest('#select-all-btn')) {
      document.querySelectorAll('.photo-checkbox').forEach((cb) => { cb.checked = true; });
      updateBulkBar();
      updateSelectedRings();
      return;
    }
    if (e.target.closest('#deselect-all-btn')) {
      document.querySelectorAll('.photo-checkbox').forEach((cb) => { cb.checked = false; });
      const sa = document.getElementById('select-all-photos');
      if (sa) { sa.checked = false; sa.indeterminate = false; }
      updateBulkBar();
      updateSelectedRings();
    }
  });

  // ── Bulk delete ───────────────────────────────────────────────────────────
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('#bulk-delete-btn');
    if (!btn) return;
    const ids = getSelectedIds();
    if (!ids.length) return;

    const doDelete = () => {
      postJson(btn.dataset.url, { ids })
        .then((r) => r.json())
        .then((data) => {
          if (data.success) { notify('success', data.message); reloadGrid(); }
          else notify('error', data.message);
        })
        .catch(() => notify('error', 'Error al eliminar las fotos'));
    };

    if (window.Alert?.confirm) {
      window.Alert.confirm(
        `¿Eliminar ${ids.length} foto(s)? Esta acción no se puede deshacer.`,
        doDelete, null,
        { title: 'Eliminar fotos', confirmText: 'Eliminar', type: 'error', icon: 'fa-solid fa-trash' }
      );
    } else if (confirm(`¿Eliminar ${ids.length} foto(s)?`)) {
      doDelete();
    }
  });

  // ── Bulk download ─────────────────────────────────────────────────────────
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('#bulk-download-btn');
    if (!btn) return;
    const ids = getSelectedIds();
    if (!ids.length) return;
    btn.disabled = true;
    btn.classList.add('loading');
    postJson(btn.dataset.url, { ids })
      .then((r) => { if (!r.ok) throw new Error('Error al generar el ZIP'); return r.blob(); })
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'fotos.zip';
        document.body.appendChild(a); a.click(); a.remove();
        URL.revokeObjectURL(url);
      })
      .catch((err) => notify('error', err.message || 'Error al descargar'))
      .finally(() => { btn.disabled = false; btn.classList.remove('loading'); });
  });

  // ── Compress ──────────────────────────────────────────────────────────────
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('#bulk-compress-btn');
    if (!btn) return;
    const ids = getSelectedIds();
    if (!ids.length) return;

    const doCompress = () => {
      btn.disabled = true; btn.classList.add('loading');
      postJson(btn.dataset.url, { ids, quality: 70 })
        .then((r) => r.json())
        .then((data) => {
          if (data.success) { notify('success', data.message); reloadGrid(); }
          else notify('error', data.message);
        })
        .catch(() => notify('error', 'Error al comprimir las fotos'))
        .finally(() => { btn.disabled = false; btn.classList.remove('loading'); });
    };

    if (window.Alert?.confirm) {
      window.Alert.confirm(
        `¿Comprimir ${ids.length} foto(s) al 70% de calidad? Los metadatos EXIF se preservarán.`,
        doCompress, null,
        { title: 'Comprimir fotos', confirmText: 'Comprimir', type: 'warning', icon: 'fa-solid fa-compress' }
      );
    } else if (confirm(`¿Comprimir ${ids.length} foto(s)?`)) {
      doCompress();
    }
  });

  // ── Reset on HTMX swap ────────────────────────────────────────────────────
  document.body.addEventListener('htmx:afterSwap', function (e) {
    if (e.detail.target && e.detail.target.id === 'gallery-grid-wrapper') {
      document.querySelectorAll('.photo-checkbox').forEach((cb) => { cb.checked = false; });
      const sa = document.getElementById('select-all-photos');
      if (sa) { sa.checked = false; sa.indeterminate = false; }
      updateBulkBar();
    }
  });
})();
