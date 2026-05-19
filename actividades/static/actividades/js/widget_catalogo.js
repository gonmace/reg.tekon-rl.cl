(function () {
    'use strict';

    var cfg = window.widgetCatalogoConfig || {};
    var modal = document.getElementById('widget-modal');
    var modalTitle = document.getElementById('widget-modal-title');
    var modalContent = document.getElementById('widget-modal-content');

    function showSpinner() {
        modalContent.innerHTML = '<div class="flex justify-center py-8"><span class="loading loading-spinner loading-md"></span></div>';
    }

    function loadModal(url, title) {
        modalTitle.textContent = title;
        showSpinner();
        modal.showModal();
        fetch(url)
            .then(function (r) { return r.text(); })
            .then(function (html) { modalContent.innerHTML = html; })
            .catch(function () {
                modalContent.innerHTML = '<p class="text-error text-sm">Error al cargar el formulario.</p>';
            });
    }

    function attachFormSubmit(widgetId) {
        var form = document.getElementById('widget-form');
        if (!form) return;

        form.addEventListener('submit', function (e) {
            e.preventDefault();
            var btn = document.getElementById('widget-submit-btn');
            if (btn) btn.disabled = true;

            var url = widgetId
                ? cfg.editModalUrl + widgetId + '/modal/'
                : cfg.createModalUrl;

            fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': cfg.csrfToken },
                body: new FormData(form),
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success) {
                    modal.close();
                    window.Alert.success(data.message, { autoHide: 2500 });
                    setTimeout(function () { window.location.reload(); }, 1000);
                } else {
                    window.Alert.error(data.message || 'Error al guardar.', { autoHide: 0, dismissible: true });
                    if (btn) btn.disabled = false;
                }
            })
            .catch(function () {
                window.Alert.error('Error de conexión.', { autoHide: 0, dismissible: true });
                if (btn) btn.disabled = false;
            });
        });
    }

    function applyCoordSource(source) {
        var p1fields = document.getElementById('map-p1-fields');
        if (p1fields) p1fields.classList.toggle('hidden', source !== 'form');
    }

    function applyTipo(tipo) {
        document.querySelectorAll('.widget-params-section').forEach(function (s) {
            s.classList.add('hidden');
        });
        if (tipo === 'CAMERA') {
            var el = document.querySelector('.widget-camera');
            if (el) el.classList.remove('hidden');
        } else if (['MAP_1', 'MAP_2', 'MAP_3'].indexOf(tipo) !== -1) {
            var el = document.querySelector('.widget-map');
            if (el) el.classList.remove('hidden');
            var show2 = tipo === 'MAP_2' || tipo === 'MAP_3';
            var show3 = tipo === 'MAP_3';
            var p2 = document.querySelector('.widget-map-p2');
            var p3 = document.querySelector('.widget-map-p3');
            if (p2) p2.classList.toggle('hidden', !show2);
            if (p3) p3.classList.toggle('hidden', !show3);

            // coord_source is per-assignment for MAP_1, not set in catalog
            var coordSection = document.getElementById('map-coord-source-section');
            if (coordSection) coordSection.classList.add('hidden');
            if (tipo !== 'MAP_1') {
                var p1fields = document.getElementById('map-p1-fields');
                if (p1fields) p1fields.classList.remove('hidden');
            }
        }
    }

    function applyIconPreview(value) {
        var preview = document.getElementById('widget-icon-preview');
        if (!preview) return;
        var v = (value || '').trim();
        if (!v) {
            preview.innerHTML = '<i class="fas fa-puzzle-piece opacity-30"></i>';
        } else if (v.charAt(0) === '<') {
            preview.innerHTML = v;
        } else {
            preview.innerHTML = '<i class="' + v + '"></i>';
        }
    }

    // Observar cuando el modal carga contenido para adjuntar submit y mostrar secciones
    var observer = new MutationObserver(function () {
        var form = document.getElementById('widget-form');
        if (form && !form.dataset.submitAttached) {
            form.dataset.submitAttached = 'true';
            var editingId = modal.dataset.editingId || null;
            attachFormSubmit(editingId);

            var select = document.getElementById('widget-tipo-select');
            if (select) {
                applyTipo(select.value);
                select.addEventListener('change', function () { applyTipo(this.value); });
            }
            var coordSelect = document.getElementById('map-coord-source-select');
            if (coordSelect) {
                coordSelect.addEventListener('change', function () { applyCoordSource(this.value); });
            }

            var iconInput = document.getElementById('widget-icono-input');
            if (iconInput) {
                applyIconPreview(iconInput.value);
                iconInput.addEventListener('input', function () { applyIconPreview(this.value); });
            }
        }
    });
    if (modalContent) observer.observe(modalContent, { childList: true });

    // Botón "Nuevo Widget"
    // Preview modal
    var previewModal = document.getElementById('widget-preview-modal');
    document.addEventListener('click', function (e) {
        var previewBtn = e.target.closest('.widget-preview-btn');
        if (!previewBtn) return;
        var tipo = previewBtn.dataset.tipo;
        var nombre = previewBtn.dataset.nombre;
        var title = document.getElementById('preview-modal-title');
        if (title) title.innerHTML = '<i class="fas fa-eye mr-2 text-success"></i>Vista previa — ' + nombre;
        document.querySelectorAll('[id^="preview-"]').forEach(function (el) { el.classList.add('hidden'); });
        var section = document.getElementById('preview-' + tipo.toLowerCase());
        if (section) section.classList.remove('hidden');
        if (previewModal) previewModal.showModal();
    });

    var addBtn = document.getElementById('addWidgetBtn');
    if (addBtn) {
        addBtn.addEventListener('click', function () {
            modal.dataset.editingId = '';
            loadModal(cfg.createModalUrl, 'Nuevo Widget');
        });
    }

    // Delegación: Editar y Eliminar
    document.addEventListener('click', function (e) {
        var editBtn = e.target.closest('.widget-edit-btn');
        if (editBtn) {
            var id = editBtn.dataset.id;
            var nombre = editBtn.dataset.nombre;
            modal.dataset.editingId = id;
            loadModal(cfg.editModalUrl + id + '/modal/', 'Editar Widget — ' + nombre);
            return;
        }

        var cloneBtn = e.target.closest('.widget-clone-btn');
        if (cloneBtn) {
            var id = cloneBtn.dataset.id;
            var nombre = cloneBtn.dataset.nombre;
            window.Alert.confirm(
                '¿Clonar el widget "' + nombre + '"?',
                function () {
                    cloneBtn.disabled = true;
                    fetch(cfg.deleteUrl + id + '/clonar/', {
                        method: 'POST',
                        headers: { 'X-CSRFToken': cfg.csrfToken },
                    })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (data.success) {
                            window.Alert.success(data.message, { autoHide: 2500 });
                            setTimeout(function () { window.location.reload(); }, 1000);
                        } else {
                            window.Alert.error(data.message, { autoHide: 0, dismissible: true });
                            cloneBtn.disabled = false;
                        }
                    })
                    .catch(function () {
                        window.Alert.error('Error de conexión.', { autoHide: 0, dismissible: true });
                        cloneBtn.disabled = false;
                    });
                },
                null,
                {
                    title: 'Clonar widget',
                    confirmText: 'Clonar',
                    cancelText: 'Cancelar',
                    type: 'info',
                    confirmClass: 'btn-info',
                    icon: 'fa-solid fa-copy',
                }
            );
            return;
        }

        var delBtn = e.target.closest('.widget-delete-btn');
        if (delBtn) {
            var id = delBtn.dataset.id;
            var nombre = delBtn.dataset.nombre;
            var usos = parseInt(delBtn.dataset.usos || '0', 10);

            if (usos > 0) {
                window.Alert.error(
                    'No se puede eliminar: el widget está asignado a ' + usos + ' paso(s).',
                    { autoHide: 0, dismissible: true }
                );
                return;
            }

            window.Alert.confirm(
                '¿Eliminar el widget "' + nombre + '"?',
                function () {
                    delBtn.disabled = true;
                    fetch(cfg.deleteUrl + id + '/eliminar/', {
                        method: 'POST',
                        headers: { 'X-CSRFToken': cfg.csrfToken },
                    })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (data.success) {
                            window.Alert.success(data.message, { autoHide: 2500 });
                            setTimeout(function () { window.location.reload(); }, 1000);
                        } else {
                            window.Alert.error(data.message, { autoHide: 0, dismissible: true });
                            delBtn.disabled = false;
                        }
                    })
                    .catch(function () {
                        window.Alert.error('Error de conexión.', { autoHide: 0, dismissible: true });
                        delBtn.disabled = false;
                    });
                },
                null,
                {
                    title: 'Eliminar widget',
                    confirmText: 'Eliminar',
                    cancelText: 'Cancelar',
                    type: 'error',
                    confirmClass: 'btn-error',
                    icon: 'fa-solid fa-trash',
                }
            );
        }
    });
})();
