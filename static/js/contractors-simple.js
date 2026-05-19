// Acciones del modal de contratistas (la tabla la renderiza django-tables2).
// Maneja: crear, editar, eliminar + validación de formulario.

(function () {
  const contractorModal = document.querySelector('#contractorModal');
  const modalTitle = document.querySelector('#modalTitle');
  const modalContent = document.querySelector('#modalContent');

  let currentContractorId = null;

  // Expuesto globalmente para el onclick del botón Cancelar dentro del form cargado
  window.closeContractorModal = function () {
    contractorModal?.close();
  };

  function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
  }

  function notify(type, message) {
    window.Alert?.[type]?.(message, { autoHide: 3000 })
      ?? console.log(`${type}: ${message}`);
  }

  function reloadTable() {
    const wrapper = document.getElementById('contractors-table-wrapper');
    if (wrapper && window.htmx) {
      htmx.ajax('GET', window.location.pathname + window.location.search, {
        target: '#contractors-table-wrapper',
        swap: 'innerHTML',
      });
    } else {
      window.location.reload();
    }
  }

  // ── Validación ──────────────────────────────────────────────────────
  function clearFormErrors() {
    document.querySelectorAll('#contractorForm .field-error').forEach((el) => el.remove());
    document.querySelectorAll('#contractorForm .input-error').forEach((el) =>
      el.classList.remove('input-error')
    );
  }

  function showFieldError(field, message) {
    field.classList.add('input-error');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error text-error text-xs mt-1';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
  }

  function validateFormForSubmit() {
    const form = document.querySelector('#contractorForm');
    if (!form) return false;
    const nameField = form.querySelector('[name="name"]');
    const codeField = form.querySelector('[name="code"]');
    let isValid = true;
    clearFormErrors();
    if (!nameField.value.trim()) {
      showFieldError(nameField, 'El nombre es obligatorio');
      isValid = false;
    } else if (nameField.value.trim().length < 3) {
      showFieldError(nameField, 'El nombre debe tener al menos 3 caracteres');
      isValid = false;
    }
    if (!codeField.value.trim()) {
      showFieldError(codeField, 'El código es obligatorio');
      isValid = false;
    } else if (codeField.value.trim().length < 2) {
      showFieldError(codeField, 'El código debe tener al menos 2 caracteres');
      isValid = false;
    }
    return isValid;
  }

  // ── Cargar formulario en modal ──────────────────────────────────────
  function loadContractorForm(contractorId = null, nombre = null) {
    modalContent.innerHTML = `
      <div class="flex items-center justify-center py-8">
        <div class="loading loading-spinner loading-lg text-primary"></div>
        <span class="ml-3 text-base-content">Cargando formulario...</span>
      </div>`;

    const url = contractorId
      ? `/api/v1/contractors/${contractorId}/edit-modal/`
      : '/api/v1/contractors/create-modal/';

    fetch(url, {
      headers: { 'X-CSRFToken': getCSRFToken(), Accept: 'application/json' },
    })
      .then((r) => r.json())
      .then((data) => {
        if (!data.success) {
          notify('error', data.message);
          return;
        }
        modalContent.innerHTML = data.form_html;
        modalTitle.textContent = contractorId
          ? `Editar Contratista: ${nombre}`
          : 'Agregar Contratista';
        currentContractorId = contractorId;
        contractorModal.showModal();

        const form = document.querySelector('#contractorForm');
        if (form) {
          form.addEventListener('submit', (e) => {
            e.preventDefault();
            saveContractor();
          });
        }
      })
      .catch(() => notify('error', 'Error al cargar el formulario'));
  }

  // ── Guardar (POST/PUT) ──────────────────────────────────────────────
  function saveContractor() {
    if (!validateFormForSubmit()) return;
    const form = document.querySelector('#contractorForm');
    const formData = new FormData(form);
    const payload = {};
    formData.forEach((v, k) => (payload[k] = v));
    const isActiveCheckbox = form.querySelector('[name="is_active"]');
    if (isActiveCheckbox) {
      payload['is_active'] = isActiveCheckbox.checked;
    }

    const url = currentContractorId
      ? `/api/v1/contractors/${currentContractorId}/`
      : '/api/v1/contractors/';
    const method = currentContractorId ? 'PUT' : 'POST';

    const btn = document.querySelector('#saveContractorBtn');
    const originalText = btn?.innerHTML;
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="loading loading-spinner loading-xs"></span> Guardando...`;
    }

    fetch(url, {
      method,
      headers: {
        'X-CSRFToken': getCSRFToken(),
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.success) {
          contractorModal.close();
          notify('success', data.message);
          reloadTable();
        } else {
          notify('error', data.message || 'Error al guardar');
        }
      })
      .catch(() => notify('error', 'Error de red o del servidor.'))
      .finally(() => {
        if (btn) {
          btn.innerHTML = originalText;
          btn.disabled = false;
        }
      });
  }

  // ── Eliminar ────────────────────────────────────────────────────────
  function deleteContractor(contractorId, nombre) {
    window.Alert?.confirm(
      `¿Estás seguro de que quieres eliminar el contratista "${nombre}"?`,
      () => {
        fetch(`/api/v1/contractors/${contractorId}/`, {
          method: 'DELETE',
          headers: { 'X-CSRFToken': getCSRFToken(), Accept: 'application/json' },
        })
          .then((r) => r.json())
          .then((data) => {
            if (data.success) {
              notify('success', data.message);
              reloadTable();
            } else {
              notify('error', data.message);
            }
          })
          .catch(() => notify('error', 'Error al eliminar el contratista'));
      },
      null,
      { title: 'Eliminar contratista', confirmText: 'Eliminar', confirmClass: 'btn-delete', icon: 'fa-solid fa-trash' }
    );
  }

  // ── Event listeners ─────────────────────────────────────────────────
  if (contractorModal) {
    contractorModal.addEventListener('close', () => {
      currentContractorId = null;
    });
  }

  // Delegación: funciona también después de los swaps de HTMX
  document.addEventListener('click', (e) => {
    if (e.target.closest('#addContractorBtn')) {
      e.preventDefault();
      loadContractorForm();
      return;
    }
    const editBtn = e.target.closest('.contractor-edit-btn');
    if (editBtn) {
      e.preventDefault();
      loadContractorForm(editBtn.dataset.id, editBtn.dataset.nombre);
      return;
    }
    const delBtn = e.target.closest('.contractor-delete-btn');
    if (delBtn) {
      e.preventDefault();
      deleteContractor(delBtn.dataset.id, delBtn.dataset.nombre);
    }
  });
})();
