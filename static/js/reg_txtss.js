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

    // ── Init ────────────────────────────────────────────────────────────────
    function init() {
        initRowClick();
        initAlternativaEdit();
        initFechaEdit();
        initCopy();
        initDelete();
        initEditModal();
    }

    init();
    document.addEventListener('htmx:afterSwap', function () {
        initRowClick();
    });
})();
