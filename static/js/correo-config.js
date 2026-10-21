// Configuración de correo: elegir origen (.env / personalizada), guardar y probar (conexión / envío).
// La lógica vive aquí, no en la plantilla.
(function () {
  var root = document.getElementById('correo-config');
  if (!root) return;
  var form = document.getElementById('correo-form');
  var personalizada = document.getElementById('correo-personalizada');
  var salida = document.getElementById('correo-resultado');
  var botones = ['correo-guardar-btn', 'correo-conexion-btn', 'correo-enviar-btn'].map(function (id) { return document.getElementById(id); });

  function csrf() {
    var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/);
    if (m) return decodeURIComponent(m[1]);
    var el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }

  function origen() { return form.querySelector('[name=origen]:checked').value; }

  function configActual() {
    var d = { origen: origen() };
    ['host', 'port', 'seguridad', 'usuario', 'password', 'remitente'].forEach(function (n) { d[n] = form.elements[n].value; });
    return d;
  }

  // Los campos de la configuración personalizada solo se editan si está seleccionada
  function sincronizar() {
    var activa = origen() === 'personalizada';
    personalizada.disabled = !activa;
    personalizada.classList.toggle('opacity-50', !activa);
  }

  function mostrar(ok, texto) {
    salida.className = 'mt-3 text-sm alert ' + (ok ? 'alert-success' : 'alert-error');
    salida.textContent = texto;
  }

  function llamar(url, datos, btn, textoCargando) {
    var original = btn.innerHTML;
    botones.forEach(function (b) { b.disabled = true; });
    btn.innerHTML = '<span class="loading loading-spinner loading-xs"></span> ' + textoCargando;
    salida.className = 'hidden';
    return fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf(), 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(datos),
    })
      .then(function (r) { return r.json().catch(function () { return { success: false, message: 'Respuesta inválida del servidor' }; }); })
      .catch(function () { return { success: false, message: 'Error de red o del servidor.' }; })
      .then(function (data) {
        botones.forEach(function (b) { b.disabled = false; });
        btn.innerHTML = original;
        mostrar(!!data.success, data.message || (data.success ? 'Listo' : 'Error'));
        return data;
      });
  }

  form.querySelectorAll('[name=origen]').forEach(function (r) { r.addEventListener('change', sincronizar); });
  sincronizar();

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    llamar(root.dataset.guardarUrl, configActual(), document.getElementById('correo-guardar-btn'), 'Guardando...')
      .then(function (data) { if (data.success) setTimeout(function () { window.location.reload(); }, 900); });
  });

  document.getElementById('correo-conexion-btn').addEventListener('click', function () {
    llamar(root.dataset.conexionUrl, configActual(), this, 'Probando...');
  });

  document.getElementById('correo-enviar-btn').addEventListener('click', function () {
    var datos = configActual();
    datos.to = document.getElementById('correo-destino').value.trim();
    llamar(root.dataset.probarUrl, datos, this, 'Enviando...');
  });
})();
