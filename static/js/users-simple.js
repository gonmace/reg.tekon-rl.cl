(function () {
  const userModal = document.querySelector('#userModal');
  const modalTitle = document.querySelector('#userModalTitle');
  const modalContent = document.querySelector('#userModalContent');

  let currentUserId = null;

  window.closeUserModal = function () {
    userModal?.close();
  };

  function getCsrfToken() {
    const match = document.cookie.match(new RegExp('(^|;\\s*)csrftoken=([^;]*)'));
    return match ? decodeURIComponent(match[2]) : '';
  }

  function notify(type, message) {
    window.Alert?.[type]?.(message, { autoHide: 3000 });
  }

  function reloadTable() {
    const wrapper = document.getElementById('users-table-wrapper');
    if (wrapper && window.htmx) {
      htmx.ajax('GET', window.location.pathname + window.location.search, {
        target: '#users-table-wrapper',
        swap: 'innerHTML',
      });
    } else {
      window.location.reload();
    }
  }

  // ── Validación ──────────────────────────────────────────────────────
  function clearFormErrors() {
    document.querySelectorAll('#userForm .field-error').forEach((el) => el.remove());
    document.querySelectorAll('#userForm .input-error').forEach((el) => el.classList.remove('input-error'));
  }

  function showFieldError(field, message) {
    field.classList.add('input-error');
    const div = document.createElement('div');
    div.className = 'field-error text-error text-xs mt-1';
    div.textContent = message;
    field.parentNode.appendChild(div);
  }

  function validateForm() {
    const form = document.querySelector('#userForm');
    if (!form) return false;
    clearFormErrors();
    let valid = true;

    const username = form.querySelector('[name="username"]');
    if (username && !username.value.trim()) {
      showFieldError(username, 'El usuario es obligatorio');
      valid = false;
    }

    const firstName = form.querySelector('[name="first_name"]');
    if (firstName && !firstName.value.trim()) {
      showFieldError(firstName, 'El nombre es obligatorio');
      valid = false;
    }

    const contractor = form.querySelector('[name="contractor"]');
    if (contractor && !contractor.value) {
      showFieldError(contractor, 'La empresa es obligatoria');
      valid = false;
    }

    const password = form.querySelector('[name="password"]');
    if (password && !currentUserId && !password.value.trim()) {
      showFieldError(password, 'La contraseña es obligatoria');
      valid = false;
    }

    return valid;
  }

  // ── Cargar formulario ───────────────────────────────────────────────
  function loadUserForm(userId = null, nombre = null) {
    modalContent.innerHTML = `
      <div class="flex items-center justify-center py-8">
        <div class="loading loading-spinner loading-lg text-primary"></div>
        <span class="ml-3 text-base-content">Cargando formulario...</span>
      </div>`;

    const url = userId ? `/api/v1/users/${userId}/edit-modal/` : '/api/v1/users/create-modal/';

    fetch(url, { headers: { 'X-CSRFToken': getCsrfToken(), Accept: 'application/json' } })
      .then((r) => r.json())
      .then((data) => {
        if (!data.success) { notify('error', data.message); return; }
        modalContent.innerHTML = data.form_html;
        modalTitle.textContent = userId ? `Editar Usuario: ${nombre}` : 'Nuevo Usuario';
        currentUserId = userId;
        userModal.showModal();

        const form = document.querySelector('#userForm');
        if (form) {
          form.addEventListener('submit', (e) => { e.preventDefault(); saveUser(); });
        }
      })
      .catch(() => notify('error', 'Error al cargar el formulario'));
  }

  // ── Guardar ─────────────────────────────────────────────────────────
  function saveUser() {
    if (!validateForm()) return;
    const form = document.querySelector('#userForm');
    const formData = new FormData(form);
    const payload = {};
    formData.forEach((v, k) => (payload[k] = v));

    const isActiveCheckbox = form.querySelector('[name="is_active"]');
    if (isActiveCheckbox) payload['is_active'] = isActiveCheckbox.checked;

    // Recoger checkboxes múltiples de report_access
    delete payload['report_access'];
    const reportCheckboxes = form.querySelectorAll('[name="report_access"]:checked');
    payload['report_access'] = Array.from(reportCheckboxes).map((cb) => cb.value);

    const url = currentUserId ? `/api/v1/users/${currentUserId}/` : '/api/v1/users/';
    const method = currentUserId ? 'PUT' : 'POST';

    const btn = document.querySelector('#saveUserBtn');
    const originalText = btn?.innerHTML;
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="loading loading-spinner loading-xs"></span> Guardando...'; }

    fetch(url, {
      method,
      headers: { 'X-CSRFToken': getCsrfToken(), 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.success) {
          userModal.close();
          notify('success', data.message);
          reloadTable();
        } else {
          notify('error', data.message || 'Error al guardar');
        }
      })
      .catch(() => notify('error', 'Error de red o del servidor.'))
      .finally(() => { if (btn) { btn.innerHTML = originalText; btn.disabled = false; } });
  }

  // ── Eliminar ────────────────────────────────────────────────────────
  function deleteUser(userId, nombre) {
    window.Alert?.confirm(
      `¿Estás seguro de que quieres eliminar el usuario "${nombre}"?`,
      () => {
        fetch(`/api/v1/users/${userId}/`, {
          method: 'DELETE',
          headers: { 'X-CSRFToken': getCsrfToken(), Accept: 'application/json' },
        })
          .then((r) => r.json())
          .then((data) => {
            if (data.success) { notify('success', data.message); reloadTable(); }
            else { notify('error', data.message); }
          })
          .catch(() => notify('error', 'Error al eliminar el usuario'));
      },
      null,
      { title: 'Eliminar usuario', confirmText: 'Eliminar', confirmClass: 'btn-delete', icon: 'fa-solid fa-trash' }
    );
  }

  // ── Event listeners ─────────────────────────────────────────────────
  if (userModal) {
    userModal.addEventListener('close', () => { currentUserId = null; });
  }

  document.addEventListener('click', (e) => {
    if (e.target.closest('#addUserBtn')) {
      e.preventDefault();
      loadUserForm();
      return;
    }
    const editBtn = e.target.closest('.user-edit-btn');
    if (editBtn) {
      e.preventDefault();
      loadUserForm(editBtn.dataset.id, editBtn.dataset.nombre);
      return;
    }
    const delBtn = e.target.closest('.user-delete-btn');
    if (delBtn) {
      e.preventDefault();
      deleteUser(delBtn.dataset.id, delBtn.dataset.nombre);
    }
  });
})();
