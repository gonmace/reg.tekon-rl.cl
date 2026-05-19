(function () {
    'use strict';

    var cfg = window.pasoCatalogoConfig || {};
    var modal = document.getElementById('paso-modal');
    var modalTitle = document.getElementById('paso-modal-title');
    var modalContent = document.getElementById('paso-modal-content');

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

    function attachFormSubmit(pasoId) {
        var form = document.getElementById('paso-form');
        if (!form) return;

        form.addEventListener('submit', function (e) {
            e.preventDefault();
            var btn = document.getElementById('paso-submit-btn');
            if (btn) btn.disabled = true;

            var url = pasoId
                ? cfg.editModalUrl + pasoId + '/modal/'
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

    // Observar cuando el modal carga contenido para adjuntar submit
    var observer = new MutationObserver(function () {
        var form = document.getElementById('paso-form');
        if (form && !form.dataset.submitAttached) {
            form.dataset.submitAttached = 'true';
            var editingId = modal.dataset.editingId || null;
            attachFormSubmit(editingId);
        }
    });
    if (modalContent) observer.observe(modalContent, { childList: true });

    // Botón "Nuevo Paso"
    var addBtn = document.getElementById('addPasoBtn');
    if (addBtn) {
        addBtn.addEventListener('click', function () {
            modal.dataset.editingId = '';
            loadModal(cfg.createModalUrl, 'Nuevo Paso');
        });
    }

    // Delegación: Editar, Clonar, Eliminar
    document.addEventListener('click', function (e) {
        var editBtn = e.target.closest('.paso-edit-btn');
        if (editBtn) {
            var id = editBtn.dataset.id;
            var titulo = editBtn.dataset.titulo;
            modal.dataset.editingId = id;
            loadModal(cfg.editModalUrl + id + '/modal/', 'Editar Paso — ' + titulo);
            return;
        }

        var cloneBtn = e.target.closest('.paso-clone-btn');
        if (cloneBtn) {
            var id = cloneBtn.dataset.id;
            var titulo = cloneBtn.dataset.titulo;
            window.Alert.confirm(
                '¿Clonar el paso "' + titulo + '"?',
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
                    title: 'Clonar paso',
                    confirmText: 'Clonar',
                    cancelText: 'Cancelar',
                    type: 'info',
                    confirmClass: 'btn-info',
                    icon: 'fa-solid fa-copy',
                }
            );
            return;
        }

        var delBtn = e.target.closest('.paso-delete-btn');
        if (delBtn) {
            var id = delBtn.dataset.id;
            var titulo = delBtn.dataset.titulo;
            window.Alert.confirm(
                '¿Eliminar el paso "' + titulo + '"?',
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
                    title: 'Eliminar paso',
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
