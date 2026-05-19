(function () {
    'use strict';

    var cfg = window.widgetCamposConfig || {};
    var modal = document.getElementById('campo-modal');
    var modalTitle = document.getElementById('campo-modal-title');
    var modalContent = document.getElementById('campo-modal-content');

    function showSpinner() {
        modalContent.innerHTML = '<div class="flex justify-center py-8"><span class="loading loading-spinner loading-md"></span></div>';
    }

    function applyTipo(tipo) {
        var numeric = ['INTEGER', 'FLOAT', 'DECIMAL', 'PORCENTAJE'];
        var isButton  = tipo === 'BUTTON';
        var isTextBtn = tipo === 'TEXT_BTN';

        // Secciones estándar
        document.getElementById('campo-sec-numeric').classList.toggle('hidden', numeric.indexOf(tipo) === -1);
        document.getElementById('campo-sec-text').classList.toggle('hidden', tipo !== 'TEXT');
        document.getElementById('campo-sec-select').classList.toggle('hidden', tipo !== 'SELECT');

        // Sección botón: visible para BUTTON y TEXT_BTN
        document.getElementById('campo-sec-button').classList.toggle('hidden', !isButton && !isTextBtn);

        // Separador "Campo de texto": solo para TEXT_BTN
        var textHeader = document.getElementById('campo-textbtn-text-header');
        if (textHeader) textHeader.classList.toggle('hidden', !isTextBtn);

        // Bloque ayuda/unidad (para campos normales): ocultar para BUTTON y TEXT_BTN
        var ayudaGrid = document.getElementById('campo-ayuda-unidad-grid');
        if (ayudaGrid) {
            ayudaGrid.classList.toggle('hidden', isButton || isTextBtn);
            var ayudaInput = document.getElementById('campo-ayuda-input');
            if (ayudaInput) ayudaInput.disabled = isButton || isTextBtn;
        }

        // Ícono BUTTON (name=placeholder): visible solo para BUTTON
        var iconRow = document.getElementById('campo-btn-icon-row');
        if (iconRow) iconRow.classList.toggle('hidden', !isButton);
        var btnPlaceholderInput = document.getElementById('campo-btn-placeholder-input');
        if (btnPlaceholderInput) btnPlaceholderInput.disabled = !isButton;

        // Ícono TEXT_BTN (name=ayuda, separado): visible solo para TEXT_BTN
        var textbtnIconRow = document.getElementById('campo-textbtn-icon-row');
        if (textbtnIconRow) textbtnIconRow.classList.toggle('hidden', !isTextBtn);
        var textbtnAyudaInput = document.getElementById('campo-textbtn-ayuda-input');
        if (textbtnAyudaInput) textbtnAyudaInput.disabled = !isTextBtn;

        // Nota "etiqueta": solo para BUTTON
        var etiquetaNote = document.getElementById('campo-btn-etiqueta-note');
        if (etiquetaNote) etiquetaNote.classList.toggle('hidden', !isButton);

        // Placeholder: ocultar para BUTTON (el ícono está en campo-sec-button)
        var placeholderGroup = document.getElementById('campo-placeholder-group');
        if (placeholderGroup) placeholderGroup.classList.toggle('hidden', isButton);

        // Unidad texto: ocultar+deshabilitar para BUTTON y TEXT_BTN
        var unidadTextInput = document.getElementById('campo-unidad-text-input');
        if (unidadTextInput) {
            unidadTextInput.disabled = isButton || isTextBtn;
            unidadTextInput.closest('.form-control').classList.toggle('hidden', isButton || isTextBtn);
        }

        // Select oculto de unidad: activo solo cuando la sección botón está visible
        var unidadSelect = document.getElementById('campo-btn-unidad-select');
        if (unidadSelect) unidadSelect.disabled = !isButton && !isTextBtn;

        // Alineación: solo para BUTTON puro (no TEXT_BTN)
        var alignRow = document.getElementById('campo-btn-align-row');
        if (alignRow) alignRow.classList.toggle('hidden', !isButton);
        var alignInput = document.getElementById('campo-btn-align-input');
        if (alignInput) alignInput.disabled = !isButton;
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

    function refreshPage() {
        fetch(window.location.href)
            .then(function(r) { return r.text(); })
            .then(function(html) {
                var doc = new DOMParser().parseFromString(html, 'text/html');
                var newTable = doc.querySelector('#campo-table-wrapper');
                var newPreview = doc.querySelector('#form-preview');
                if (newTable) document.querySelector('#campo-table-wrapper').innerHTML = newTable.innerHTML;
                if (newPreview) document.querySelector('#form-preview').innerHTML = newPreview.innerHTML;
            })
            .catch(function() {});
    }

    function attachFormSubmit(postUrl) {
        var form = document.getElementById('campo-form');
        if (!form) return;
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            var btn = document.getElementById('campo-submit-btn');
            if (btn) btn.disabled = true;
            fetch(postUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': cfg.csrfToken },
                body: new FormData(form),
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success) {
                    modal.close();
                    window.Alert.success(data.message, { autoHide: 2500 });
                    setTimeout(refreshPage, 1000);
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

    function initStylePicker() {
        var picker = document.getElementById('campo-btn-style-picker');
        var hidden = document.getElementById('campo-btn-unidad-select');
        if (!picker || !hidden) return;
        var swatches = picker.querySelectorAll('.style-swatch');
        var current = hidden.value;
        swatches.forEach(function (btn) {
            if (btn.dataset.val === current) btn.classList.add('selected');
            btn.addEventListener('click', function () {
                swatches.forEach(function (b) { b.classList.remove('selected'); });
                btn.classList.add('selected');
                hidden.value = btn.dataset.val;
            });
        });
    }

    function initAlignPicker() {
        var picker = document.getElementById('campo-btn-align-picker');
        var hidden = document.getElementById('campo-btn-align-input');
        if (!picker || !hidden) return;
        var swatches = picker.querySelectorAll('.style-swatch');
        var current = hidden.value;
        swatches.forEach(function (btn) {
            if (btn.dataset.align === current) btn.classList.add('selected');
            btn.addEventListener('click', function () {
                swatches.forEach(function (b) { b.classList.remove('selected'); });
                btn.classList.add('selected');
                hidden.value = btn.dataset.align;
            });
        });
    }

    function buildPrompt() {
        var nombreInput = document.querySelector('#campo-form [name="nombre"]');
        var tipoSelect  = document.getElementById('campo-tipo-select');
        var nombre = nombreInput ? nombreInput.value.trim() : '';
        var tipo   = tipoSelect  ? tipoSelect.value : 'BUTTON';
        var campos = (cfg.campos || []).filter(function (c) {
            return c.tipo !== 'BUTTON' && c.tipo !== 'TEXT_BTN';
        });

        var isTextBtn = tipo === 'TEXT_BTN';
        var ctx = isTextBtn
            ? '- `this` = el botón\n- `this.closest(\'label\').querySelector(\'input\')` = el campo de texto del propio botón\n- `this.closest(\'form\')` = el formulario completo'
            : '- `this` = el botón\n- `this.closest(\'form\')` = el formulario';

        var camposList = campos.length
            ? campos.map(function (c) { return '- ' + c.nombre + ' (' + c.tipo + ' — ' + c.etiqueta + ')'; }).join('\n')
            : '(sin campos adicionales en este widget)';

        return (
            'Realizar un código JavaScript para que cuando se ejecute el botón "' + (nombre || 'accion') + '", se haga lo siguiente: [DESCRIBIR AQUÍ].\n\n' +
            'Contexto de ejecución (onclick del botón):\n' +
            ctx + '\n' +
            '- No usar eval() ni new Function() (restricción CSP)\n\n' +
            'Campos disponibles en el formulario:\n' +
            camposList + '\n\n' +
            'Generar solo el cuerpo del código JavaScript, sin función envolvente ni comentarios innecesarios.'
        );
    }

    function initCopyPromptBtn() {
        var btn = document.getElementById('copy-prompt-btn');
        if (!btn) return;
        btn.addEventListener('click', function () {
            var text = buildPrompt();
            navigator.clipboard.writeText(text).then(function () {
                var orig = btn.innerHTML;
                btn.innerHTML = '<i class="fa-solid fa-check"></i>¡Copiado!';
                setTimeout(function () { btn.innerHTML = orig; }, 2000);
            });
        });
    }

    var observer = new MutationObserver(function () {
        var form = document.getElementById('campo-form');
        if (form && !form.dataset.submitAttached) {
            form.dataset.submitAttached = 'true';
            attachFormSubmit(form.getAttribute('data-post-url'));
            var select = document.getElementById('campo-tipo-select');
            if (select) {
                applyTipo(select.value);
                select.addEventListener('change', function () { applyTipo(this.value); });
            }
            initStylePicker();
            initAlignPicker();
            initCopyPromptBtn();
        }
    });
    if (modalContent) observer.observe(modalContent, { childList: true });

    // Nuevo campo
    var addBtn = document.getElementById('addCampoBtn');
    if (addBtn) {
        addBtn.addEventListener('click', function () {
            var url = cfg.createModalUrl;
            loadModal(url, 'Nuevo Campo');
            modalContent.dataset.postUrl = url;
        });
    }

    // Nueva acción/botón — carga modal en modo botón (is_button=True en el backend)
    var addBotonBtn = document.getElementById('addBotonBtn');
    if (addBotonBtn) {
        addBotonBtn.addEventListener('click', function () {
            var url = cfg.createModalUrl + '?tipo=BUTTON';
            loadModal(url, 'Nueva Acción');
        });
    }

    // Delegación: Editar y Eliminar
    document.addEventListener('click', function (e) {
        var editBtn = e.target.closest('.campo-edit-btn');
        if (editBtn) {
            var id = editBtn.dataset.id;
            var etiqueta = editBtn.dataset.etiqueta;
            var editUrl = '/actividades/widgets/' + cfg.widgetPk + '/campos/' + id + '/editar/';
            loadModal(editUrl, 'Editar Campo — ' + etiqueta);
            // Store post URL in the content div so the observer can pick it up
            modalContent.dataset.postUrl = editUrl;
            return;
        }

        var delBtn = e.target.closest('.campo-delete-btn');
        if (delBtn) {
            var id = delBtn.dataset.id;
            var etiqueta = delBtn.dataset.etiqueta;
            window.Alert.confirm(
                '¿Eliminar el campo "' + etiqueta + '"?',
                function () {
                    delBtn.disabled = true;
                    fetch('/actividades/widgets/' + cfg.widgetPk + '/campos/' + id + '/eliminar/', {
                        method: 'POST',
                        headers: { 'X-CSRFToken': cfg.csrfToken },
                    })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (data.success) {
                            window.Alert.success(data.message, { autoHide: 2500 });
                            setTimeout(refreshPage, 1000);
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
                    title: 'Eliminar campo',
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
