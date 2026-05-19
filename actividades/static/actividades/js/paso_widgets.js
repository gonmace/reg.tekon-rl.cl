(function () {
    'use strict';

    var cfg = window.pasoWidgetsConfig || {};
    var configModal = document.getElementById('cw-config-modal');
    var configModalTitle = document.getElementById('cw-config-modal-title');
    var configModalContent = document.getElementById('cw-config-modal-content');

    // Auto-open config modal if one was queued from an add action
    var pendingConfig = sessionStorage.getItem('pw_open_config');
    if (pendingConfig && configModal) {
        try {
            var pending = JSON.parse(pendingConfig);
            sessionStorage.removeItem('pw_open_config');
            setTimeout(function () { loadConfigModal(pending.cwId, pending.nombre); }, 300);
        } catch (e) {
            sessionStorage.removeItem('pw_open_config');
        }
    }

    function submitConfigForm(form) {
        var btn = document.getElementById('cw-config-submit-btn');
        if (btn) btn.disabled = true;
        var cwId = form.dataset.cwId;
        var url = cfg.configUrlBase + cwId + '/config/';
        fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': cfg.csrfToken },
            body: new FormData(form),
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                configModal.close();
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
    }

    function loadConfigModal(cwId, nombre) {
        configModalTitle.textContent = 'Configurar — ' + nombre;
        configModalContent.innerHTML = '<div class="flex justify-center py-8"><span class="loading loading-spinner loading-md"></span></div>';
        configModal.showModal();

        var url = cfg.configUrlBase + cwId + '/config/';
        fetch(url)
            .then(function (r) { return r.text(); })
            .then(function (html) {
                configModalContent.innerHTML = html;
                var form = document.getElementById('cw-config-form');
                if (form) {
                    form.dataset.cwId = cwId;
                    form.addEventListener('submit', function (e) {
                        e.preventDefault();
                        submitConfigForm(form);
                    });
                }
            })
            .catch(function () {
                configModalContent.innerHTML = '<p class="text-error text-sm">Error al cargar la configuración.</p>';
            });
    }

    document.addEventListener('click', function (e) {
        // Agregar widget
        var addBtn = e.target.closest('.pw-add-btn');
        if (addBtn) {
            var widgetId = addBtn.dataset.widgetId;
            var nombre = addBtn.dataset.nombre;
            addBtn.disabled = true;

            var formData = new FormData();
            formData.append('widget_id', widgetId);

            fetch(cfg.addUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': cfg.csrfToken },
                body: formData,
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success) {
                    window.Alert.success(data.message, { autoHide: 2000 });
                    if (data.needs_config && data.cw_pk) {
                        // Set sessionStorage BEFORE reload so config modal opens after page loads
                        sessionStorage.setItem('pw_open_config', JSON.stringify({
                            cwId: data.cw_pk, nombre: data.nombre
                        }));
                        setTimeout(function () { window.location.reload(); }, 800);
                    } else {
                        setTimeout(function () { window.location.reload(); }, 1000);
                    }
                } else {
                    window.Alert.error(data.message || 'Error al agregar.', { autoHide: 0, dismissible: true });
                    addBtn.disabled = false;
                }
            })
            .catch(function () {
                window.Alert.error('Error de conexión.', { autoHide: 0, dismissible: true });
                addBtn.disabled = false;
            });
            return;
        }

        // Configurar widget (CAMERA / MAP)
        var configBtn = e.target.closest('.pw-config-btn');
        if (configBtn) {
            var cwId = configBtn.dataset.id;
            var nombre = configBtn.dataset.nombre;
            loadConfigModal(cwId, nombre);
            return;
        }

        // Quitar widget
        var removeBtn = e.target.closest('.pw-remove-btn');
        if (removeBtn) {
            var id = removeBtn.dataset.id;
            var nombre = removeBtn.dataset.nombre;
            window.Alert.confirm(
                '¿Quitar el widget "' + nombre + '" de este paso?',
                function () {
                    removeBtn.disabled = true;
                    fetch(cfg.removeBase + cfg.pasoPk + '/widgets/' + id + '/quitar/', {
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
                            removeBtn.disabled = false;
                        }
                    })
                    .catch(function () {
                        window.Alert.error('Error de conexión.', { autoHide: 0, dismissible: true });
                        removeBtn.disabled = false;
                    });
                },
                null,
                {
                    title: 'Quitar widget',
                    confirmText: 'Quitar',
                    cancelText: 'Cancelar',
                    type: 'warning',
                    confirmClass: 'btn-warning',
                    icon: 'fa-solid fa-times',
                }
            );
        }
    });
})();
