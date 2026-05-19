(function () {
    'use strict';

    var cfg = window.tipoPasosConfig || {};

    // ── Auto-slug desde el título ────────────────────────────────────
    var tituloInput = document.getElementById('np-titulo');
    var nombreInput = document.getElementById('np-nombre');
    var slugManual  = false;

    function slugify(text) {
        return text
            .toLowerCase()
            .normalize('NFD').replace(/[̀-ͯ]/g, '')
            .replace(/[^a-z0-9\s-]/g, '')
            .trim()
            .replace(/\s+/g, '-')
            .replace(/-+/g, '-');
    }

    if (tituloInput && nombreInput) {
        nombreInput.addEventListener('input', function () { slugManual = this.value.trim() !== ''; });
        tituloInput.addEventListener('input', function () {
            if (!slugManual) nombreInput.value = slugify(this.value);
        });
    }

    // ── Crear paso ───────────────────────────────────────────────────
    var newForm = document.getElementById('new-paso-form');
    if (newForm) {
        newForm.addEventListener('submit', function (e) {
            e.preventDefault();
            var titulo = tituloInput ? tituloInput.value.trim() : '';
            var nombre = nombreInput ? nombreInput.value.trim() : '';
            var ordenEl = document.getElementById('np-orden');
            var orden = ordenEl ? ordenEl.value : '0';

            if (!titulo) {
                window.Alert && window.Alert.error('El título es obligatorio.', { autoHide: 3000 });
                tituloInput && tituloInput.focus();
                return;
            }
            if (!nombre) {
                window.Alert && window.Alert.error('El slug es obligatorio.', { autoHide: 3000 });
                nombreInput && nombreInput.focus();
                return;
            }

            var btn = document.getElementById('np-submit-btn');
            if (btn) { btn.disabled = true; btn.innerHTML = '<span class="loading loading-spinner loading-xs"></span>'; }

            var fd = new FormData();
            fd.append('titulo', titulo);
            fd.append('nombre', nombre);
            fd.append('orden', orden);

            fetch(cfg.createUrl, { method: 'POST', headers: { 'X-CSRFToken': cfg.csrfToken }, body: fd })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.success) {
                        window.Alert && window.Alert.success(data.message, { autoHide: 2500 });
                        setTimeout(function () { location.reload(); }, 900);
                    } else {
                        window.Alert && window.Alert.error(data.message || 'Error al crear.', { autoHide: 0, dismissible: true });
                        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fa-solid fa-plus"></i> Agregar'; }
                    }
                })
                .catch(function () {
                    window.Alert && window.Alert.error('Error de conexión.', { autoHide: 0, dismissible: true });
                    if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fa-solid fa-plus"></i> Agregar'; }
                });
        });
    }

    // ── Editar paso ──────────────────────────────────────────────────
    var editModal        = document.getElementById('tp-edit-modal');
    var editModalTitle   = document.getElementById('tp-edit-modal-title');
    var editModalContent = document.getElementById('tp-edit-modal-content');

    function loadEditModal(pasoId, titulo, cpId, cpOrden) {
        if (!editModal) return;
        editModalTitle.textContent = 'Editar Paso — ' + titulo;
        editModalContent.innerHTML = '<div class="flex justify-center py-8"><span class="loading loading-spinner loading-md"></span></div>';
        editModal.showModal();
        var url = cfg.editBase + pasoId + '/modal/';
        if (cpId) url += '?cp_pk=' + encodeURIComponent(cpId);
        fetch(url)
            .then(function (r) { return r.text(); })
            .then(function (html) {
                editModalContent.innerHTML = html;
                attachEditFormSubmit(pasoId);
            })
            .catch(function () {
                editModalContent.innerHTML = '<p class="text-error text-sm">Error al cargar el formulario.</p>';
            });
    }

    function attachEditFormSubmit(pasoId) {
        var f = document.getElementById('paso-form');
        if (!f || f.dataset.submitAttached) return;
        f.dataset.submitAttached = 'true';
        f.addEventListener('submit', function (e) {
            e.preventDefault();
            var btn = document.getElementById('paso-submit-btn');
            if (btn) btn.disabled = true;
            fetch(cfg.editBase + pasoId + '/modal/', {
                method: 'POST',
                headers: { 'X-CSRFToken': cfg.csrfToken },
                body: new FormData(f),
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success) {
                    editModal.close();
                    window.Alert && window.Alert.success(data.message, { autoHide: 2500 });
                    setTimeout(function () { location.reload(); }, 900);
                } else {
                    window.Alert && window.Alert.error(data.message || 'Error al guardar.', { autoHide: 0, dismissible: true });
                    if (btn) btn.disabled = false;
                }
            })
            .catch(function () {
                window.Alert && window.Alert.error('Error de conexión.', { autoHide: 0, dismissible: true });
                if (btn) btn.disabled = false;
            });
        });
    }

    // ── Widget picker — drag-and-drop orden + config persist ─────────
    var widgetModal    = document.getElementById('tp-widget-modal');
    var widgetTitle    = document.getElementById('tp-widget-modal-title');
    var widgetSubtitle = document.getElementById('tp-widget-modal-subtitle');
    var widgetSaveBtn  = document.getElementById('tp-widget-save-btn');
    var orderList      = document.getElementById('tp-order-list');
    var orderEmpty     = document.getElementById('tp-order-empty');
    var activePasoId   = null;
    var draggingChip   = null;

    // ── Chips de orden ───────────────────────────────────────────────
    function slugLabel(slug) {
        return slug.replace(/_widget$/, '').replace(/_/g, ' ')
            .replace(/\b\w/g, function (c) { return c.toUpperCase(); });
    }

    function updateOrderEmpty() {
        if (!orderEmpty) return;
        var chips = orderList ? orderList.querySelectorAll('.order-chip') : [];
        orderEmpty.classList.toggle('hidden', chips.length > 0);
    }

    function makeOrderChip(slug) {
        var iconClass = (cfg.widgetIconMap || {})[slug] || 'fa-solid fa-puzzle-piece';
        var chip = document.createElement('div');
        chip.className = 'order-chip badge badge-lg badge-primary gap-2 cursor-grab select-none px-3 py-3';
        chip.draggable = true;
        chip.dataset.slug = slug;
        chip.innerHTML = '<i class="' + iconClass + ' text-xs pointer-events-none"></i>'
            + '<span class="text-sm pointer-events-none">' + slugLabel(slug) + '</span>';

        chip.addEventListener('dragstart', function (e) {
            draggingChip = chip;
            e.dataTransfer.effectAllowed = 'move';
            setTimeout(function () { chip.classList.add('opacity-40'); }, 0);
        });
        chip.addEventListener('dragend', function () {
            chip.classList.remove('opacity-40');
            draggingChip = null;
            if (orderList) orderList.classList.remove('border-primary', 'bg-primary/5');
        });
        return chip;
    }

    if (orderList) {
        orderList.addEventListener('dragover', function (e) {
            e.preventDefault();
            if (!draggingChip) return;
            orderList.classList.add('border-primary', 'bg-primary/5');
            var chips = Array.from(orderList.querySelectorAll('.order-chip'));
            var insertBefore = null;
            for (var i = 0; i < chips.length; i++) {
                if (chips[i] === draggingChip) continue;
                var r = chips[i].getBoundingClientRect();
                if (e.clientX < r.left + r.width / 2) { insertBefore = chips[i]; break; }
            }
            orderList.insertBefore(draggingChip, insertBefore || orderEmpty || null);
        });
        orderList.addEventListener('dragleave', function (e) {
            if (!orderList.contains(e.relatedTarget)) {
                orderList.classList.remove('border-primary', 'bg-primary/5');
            }
        });
        orderList.addEventListener('drop', function (e) {
            e.preventDefault();
            orderList.classList.remove('border-primary', 'bg-primary/5');
        });
    }

    function addChip(slug) {
        if (!orderList || orderList.querySelector('[data-slug="' + slug + '"]')) return;
        orderList.insertBefore(makeOrderChip(slug), orderEmpty || null);
        updateOrderEmpty();
    }

    function removeChip(slug) {
        if (!orderList) return;
        var chip = orderList.querySelector('[data-slug="' + slug + '"]');
        if (chip) chip.remove();
        updateOrderEmpty();
    }

    // ── Config fields toggle (también actualiza chips) ───────────────
    function toggleConfigFields(cb) {
        var wrap = cb.closest('.widget-option-wrap');
        if (!wrap) return;
        var configDiv = wrap.querySelector('.widget-config-fields');
        if (configDiv) configDiv.classList.toggle('hidden', !cb.checked);
        if (cb.checked) { addChip(cb.value); } else { removeChip(cb.value); }
    }

    widgetModal && widgetModal.querySelectorAll('.widget-checkbox').forEach(function (cb) {
        cb.addEventListener('change', function () { toggleConfigFields(cb); });
    });

    // ── Abrir modal con estado pre-cargado ───────────────────────────
    function openWidgetModal(pasoId, pasoTitulo) {
        if (!widgetModal) return;
        activePasoId = pasoId;
        widgetTitle.textContent = 'Widgets — ' + pasoTitulo;

        var currentData   = (window.pasoWidgetsData || {})[pasoId] || [];
        var currentSlugs  = currentData.map(function (w) { return w.slug; });
        var currentConfigs = {};
        currentData.forEach(function (w) { currentConfigs[w.slug] = w.config || {}; });

        widgetSubtitle.textContent = currentSlugs.length
            ? 'Actuales: ' + currentSlugs.join(', ')
            : 'Sin widgets asignados';

        // Limpiar chips existentes
        if (orderList) {
            Array.from(orderList.querySelectorAll('.order-chip')).forEach(function (c) { c.remove(); });
        }
        updateOrderEmpty();

        // Resetear checkboxes y configs
        widgetModal.querySelectorAll('input[name=widget_choice]').forEach(function (cb) {
            var isChecked = currentSlugs.indexOf(cb.value) !== -1;
            cb.checked = isChecked;
            var wrap = cb.closest('.widget-option-wrap');
            var configDiv = wrap && wrap.querySelector('.widget-config-fields');
            if (configDiv) configDiv.classList.toggle('hidden', !isChecked);

            // Pre-llenar o limpiar config inputs
            if (wrap) {
                var config = isChecked ? (currentConfigs[cb.value] || {}) : {};
                wrap.querySelectorAll('[name^="cfg_"]').forEach(function (inp) {
                    var parts = inp.name.slice(4).split('__', 2);
                    if (parts.length === 2) {
                        var val = config[parts[1]];
                        if (val === undefined || val === null) {
                            inp.value = '';
                        } else if (Array.isArray(val)) {
                            inp.value = val.join(', ');
                        } else if (typeof val === 'object') {
                            inp.value = JSON.stringify(val);
                        } else {
                            inp.value = String(val);
                        }
                    }
                });
            }
        });

        // Añadir chips en el orden guardado
        currentSlugs.forEach(function (slug) { addChip(slug); });

        widgetModal.showModal();
    }

    // ── Guardar widgets en el orden de los chips ─────────────────────
    if (widgetSaveBtn) {
        widgetSaveBtn.addEventListener('click', function () {
            if (!activePasoId) return;

            // Orden determinado por los chips (drag-and-drop)
            var orderedSlugs = orderList
                ? Array.from(orderList.querySelectorAll('.order-chip')).map(function (c) { return c.dataset.slug; })
                : Array.from(widgetModal.querySelectorAll('input[name=widget_choice]:checked')).map(function (cb) { return cb.value; });

            widgetSaveBtn.disabled = true;
            widgetSaveBtn.innerHTML = '<span class="loading loading-spinner loading-xs"></span>';

            var fd = new FormData();
            orderedSlugs.forEach(function (s) { fd.append('widget_slugs', s); });

            orderedSlugs.forEach(function (slug) {
                var cb = widgetModal.querySelector('input[name=widget_choice][value="' + slug + '"]');
                var wrap = cb && cb.closest('.widget-option-wrap');
                if (!wrap) return;
                wrap.querySelectorAll('[name^="cfg_"]').forEach(function (inp) {
                    if (inp.value.trim()) fd.append(inp.name, inp.value.trim());
                });
            });

            fetch(cfg.widgetsSetBase + activePasoId + '/widgets/', {
                method: 'POST',
                headers: { 'X-CSRFToken': cfg.csrfToken },
                body: fd,
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                widgetSaveBtn.disabled = false;
                widgetSaveBtn.innerHTML = '<i class="fa-solid fa-save"></i> Guardar';
                if (data.success) {
                    widgetModal.close();
                    window.Alert && window.Alert.success(data.message, { autoHide: 2500 });
                    setTimeout(function () { location.reload(); }, 900);
                } else {
                    window.Alert && window.Alert.error(data.message || 'Error al guardar.', { autoHide: 0, dismissible: true });
                }
            })
            .catch(function () {
                widgetSaveBtn.disabled = false;
                widgetSaveBtn.innerHTML = '<i class="fa-solid fa-save"></i> Guardar';
                window.Alert && window.Alert.error('Error de conexión.', { autoHide: 0, dismissible: true });
            });
        });
    }

    // ── Delegación de eventos (widget / editar / quitar) ─────────────
    document.addEventListener('click', function (e) {
        var widgetBtn = e.target.closest('.tp-widget-btn');
        if (widgetBtn) {
            openWidgetModal(widgetBtn.dataset.pasoId, widgetBtn.dataset.pasoTitulo);
            return;
        }

        var editBtn = e.target.closest('.tp-edit-btn');
        if (editBtn) {
            loadEditModal(editBtn.dataset.id, editBtn.dataset.titulo, editBtn.dataset.cpId, editBtn.dataset.cpOrden);
            return;
        }

        var removeBtn = e.target.closest('.tp-remove-btn');
        if (!removeBtn) return;

        window.Alert && window.Alert.confirm(
            '¿Eliminar el paso "' + removeBtn.dataset.titulo + '" de este tipo?',
            function () {
                removeBtn.disabled = true;
                fetch(cfg.removeBase + removeBtn.dataset.id + '/quitar/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': cfg.csrfToken },
                })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.success) {
                        window.Alert && window.Alert.success(data.message, { autoHide: 2500 });
                        setTimeout(function () { location.reload(); }, 900);
                    } else {
                        window.Alert && window.Alert.error(data.message, { autoHide: 0, dismissible: true });
                        removeBtn.disabled = false;
                    }
                })
                .catch(function () {
                    window.Alert && window.Alert.error('Error de conexión.', { autoHide: 0, dismissible: true });
                    removeBtn.disabled = false;
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
    });

    // ── Importar pasos ────────────────────────────────────────────────
    var importBtn = document.getElementById('tp-import-btn');
    var importModal = document.getElementById('tp-import-modal');
    var importForm = document.getElementById('tp-import-form');

    if (importBtn && importModal) {
        importBtn.addEventListener('click', function () {
            importModal.showModal();
        });
    }

    if (importForm) {
        importForm.addEventListener('submit', function (e) {
            e.preventDefault();
            var fileInput = document.getElementById('tp-import-file');
            if (!fileInput || !fileInput.files.length) return;

            var fd = new FormData();
            fd.append('file', fileInput.files[0]);

            var submitBtn = document.getElementById('tp-import-submit');
            var resultDiv = document.getElementById('tp-import-result');
            var originalHtml = submitBtn.innerHTML;

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading loading-spinner loading-xs"></span> Importando...';
            if (resultDiv) { resultDiv.classList.add('hidden'); resultDiv.innerHTML = ''; }

            fetch(cfg.importUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': cfg.csrfToken },
                body: fd,
            })
            .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
            .then(function (_a) {
                var ok = _a.ok, data = _a.data;
                if (ok && data.success) {
                    window.Alert && window.Alert.success(data.message, { autoHide: 4000 });
                    importModal.close();
                    importForm.reset();
                    setTimeout(function () { location.reload(); }, 900);
                } else {
                    var errorList = (data.errors || []).map(function (e) { return '<li>' + e + '</li>'; }).join('');
                    var html = '<div class="alert alert-error"><div><div class="font-semibold">' + (data.message || 'Error al importar.') + '</div>'
                        + (errorList ? '<ul class="list-disc ml-5 text-xs mt-1">' + errorList + '</ul>' : '')
                        + '</div></div>';
                    if (resultDiv) { resultDiv.innerHTML = html; resultDiv.classList.remove('hidden'); }
                }
            })
            .catch(function () {
                if (resultDiv) {
                    resultDiv.innerHTML = '<div class="alert alert-error text-sm">Error de conexión.</div>';
                    resultDiv.classList.remove('hidden');
                }
            })
            .finally(function () {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHtml;
            });
        });
    }
})();
