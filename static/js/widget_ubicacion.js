(function () {
  'use strict';

  // ── Ícono de marcador inline (sin imágenes externas) ─────────────────────
  function makeMarkerIcon() {
    return L.divIcon({
      className: '',
      html: '<div style="width:20px;height:20px;border-radius:50%;background:#2563eb;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.45);"></div>',
      iconSize: [20, 20],
      iconAnchor: [10, 10],
      popupAnchor: [0, -14],
    });
  }

  // ── Referencias DOM ─────────────────────────────────────────────────────────
  var modal      = document.getElementById('mapa');
  var btnGuardar = document.getElementById('btn-guardar-ubicacion');
  var btnUbicar  = document.getElementById('btn-ubicar-mapa');
  var latInput   = document.getElementById('id_lat');
  var lonInput   = document.getElementById('id_lon');

  var map           = null;
  var currentMarker = null;
  var isMobile      = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

  // ── Mapa ────────────────────────────────────────────────────────────────────

  function initMap() {
    if (map) return;

    var opts = { zoomControl: false };
    if (isMobile) {
      opts.tap             = true;
      opts.touchZoom       = true;
      opts.scrollWheelZoom = false;
      opts.doubleClickZoom = false;
    }

    map = L.map('map', opts).setView([-33.45, -70.66], isMobile ? 10 : 13);

    var osm  = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    });
    var esri = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles © Esri'
    });
    esri.addTo(map);
    L.control.layers({ OpenStreetMap: osm, 'Esri Satellite': esri }).addTo(map);
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    if (window.L && L.control && L.control.locate) {
      L.control.locate({
        flyTo: true, position: 'topright',
        drawCircle: false, drawMarker: false
      }).addTo(map);
      map.on('locationfound', function (e) {
        setMarker(e.latitude, e.longitude, 'Tu ubicación');
      });
    }

    if (isMobile) {
      map.setZoom(10);
      map.on('touchstart', function () { map.doubleClickZoom.disable(); });
      map.on('touchend',   function () { setTimeout(function () { map.doubleClickZoom.enable(); }, 300); });
    }

    map.on('click', function (e) { setMarker(e.latlng.lat, e.latlng.lng); });
  }

  function setMarker(lat, lng, popup) {
    if (currentMarker) {
      map.removeLayer(currentMarker);
    } else {
      btnGuardar.classList.remove('btn-disabled');
    }
    currentMarker = L.marker([lat, lng], { icon: makeMarkerIcon() }).addTo(map);
    if (popup) currentMarker.bindPopup(popup).openPopup();
  }

  function clearMarker() {
    if (currentMarker) { map.removeLayer(currentMarker); currentMarker = null; }
    btnGuardar.classList.add('btn-disabled');
  }

  modal.addEventListener('close', clearMarker);

  btnGuardar.addEventListener('click', function () {
    if (!currentMarker) return;
    latInput.value = currentMarker.getLatLng().lat.toFixed(7);
    lonInput.value = currentMarker.getLatLng().lng.toFixed(7);
    modal.close();
  });

  btnUbicar.addEventListener('click', function () {
    var helpLat = document.getElementById('help-text-lat');
    var helpLon = document.getElementById('help-text-lon');
    if (helpLat) helpLat.textContent = 'Grados decimales.';
    if (helpLon) helpLon.textContent = 'Grados decimales.';

    initMap();

    if (latInput.value && lonInput.value) {
      var lat = parseFloat(latInput.value);
      var lng = parseFloat(lonInput.value);
      if (!isNaN(lat) && !isNaN(lng)) {
        map.setView([lat, lng], isMobile ? 15 : 16);
        setMarker(lat, lng, 'Ubicación guardada');
      }
    }
    modal.showModal();
  });

  // ── Conversión DMS ──────────────────────────────────────────────────────────

  var dmsState = { signedDegrees: 0, coordType: '' };

  document.querySelectorAll('button[data-target]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      dmsState.coordType = btn.dataset.target;
      abrirModalDMS();
    });
  });

  function abrirModalDMS() {
    var tipo = dmsState.coordType;
    var maxGrados = tipo === 'lat' ? 90 : 180;

    var directionHTML = tipo === 'lat'
      ? '<label class="flex items-center"><input type="radio" name="direction" value="S" class="radio radio-warning radio-xs" checked><span class="text-sm ml-1">S (Sur)</span></label>' +
        '<label class="flex items-center"><input type="radio" name="direction" value="N" class="radio radio-warning radio-xs"><span class="text-sm ml-1">N (Norte)</span></label>'
      : '<label class="flex items-center"><input type="radio" name="direction" value="W" class="radio radio-warning radio-xs" checked><span class="text-sm ml-1">W (Oeste)</span></label>' +
        '<label class="flex items-center"><input type="radio" name="direction" value="E" class="radio radio-warning radio-xs"><span class="text-sm ml-1">E (Este)</span></label>';

    var dlg = document.createElement('dialog');
    dlg.id = 'modal-dms-' + tipo;
    dlg.className = 'modal modal-bottom sm:modal-middle';
    dlg.innerHTML =
      '<div class="modal-box bg-base-200">' +
        '<form method="dialog">' +
          '<button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>' +
        '</form>' +
        '<h3 class="text-lg font-bold">Convierte DMS a DD</h3>' +
        '<form id="dms-form" class="p-6 space-y-4">' +
          '<div class="mb-4">' +
            '<label>Dirección</label>' +
            '<div class="flex space-x-4 mt-1">' + directionHTML + '</div>' +
          '</div>' +
          '<div class="grid grid-cols-3 gap-3">' +
            '<div><label class="block text-sm font-medium mb-1">Grados</label>' +
              '<input type="number" id="dms-degrees" min="0" max="' + maxGrados + '" placeholder="0–' + maxGrados + '" class="input input-success w-full"></div>' +
            '<div><label class="block text-sm font-medium mb-1">Minutos</label>' +
              '<input type="number" id="dms-minutes" min="0" max="59.999" placeholder="0–59" class="input input-success w-full"></div>' +
            '<div><label class="block text-sm font-medium mb-1">Segundos</label>' +
              '<input type="number" id="dms-seconds" min="0" max="59.999" step="0.001" placeholder="0–59" class="input input-success w-full"></div>' +
          '</div>' +
          '<div id="dms-result" class="hidden">' +
            '<div class="bg-secondary border border-success rounded-md p-4">' +
              '<p class="text-sm font-medium mb-1">Resultado:</p>' +
              '<p id="dms-result-text" class="text-lg font-mono text-secondary-content"></p>' +
            '</div>' +
          '</div>' +
          '<div id="dms-error" class="hidden">' +
            '<div class="bg-error/50 border border-error rounded-md p-4">' +
              '<p id="dms-error-text" class="text-sm text-error-content"></p>' +
            '</div>' +
          '</div>' +
          '<div class="flex justify-end">' +
            '<button id="dms-capturar" type="button" class="btn btn-success">Capturar coordenada</button>' +
          '</div>' +
        '</form>' +
      '</div>';

    document.body.appendChild(dlg);
    dlg.showModal();

    dlg.querySelectorAll('input').forEach(function (inp) {
      inp.addEventListener('input', function () { validarDMS(dlg); });
    });

    dlg.querySelector('#dms-capturar').addEventListener('click', function () {
      capturarDMS(dlg);
    });

    dlg.addEventListener('close', function () {
      dmsState.coordType = '';
      dmsState.signedDegrees = 0;
      dlg.remove();
    });
  }

  function validarDMS(dlg) {
    var tipo    = dmsState.coordType;
    var grados  = parseFloat(dlg.querySelector('#dms-degrees').value)  || 0;
    var minutos = parseFloat(dlg.querySelector('#dms-minutes').value)  || 0;
    var segundos= parseFloat(dlg.querySelector('#dms-seconds').value)  || 0;
    var dir     = dlg.querySelector('input[name="direction"]:checked')?.value || 'S';
    var errorEl = dlg.querySelector('#dms-error');
    var resultEl= dlg.querySelector('#dms-result');
    var maxG    = tipo === 'lat' ? 90 : 180;
    var errores = [];

    if (grados < 0 || grados > maxG) errores.push('Grados: 0–' + maxG);
    if (minutos < 0 || minutos >= 60) errores.push('Minutos: 0–59');
    if (segundos < 0 || segundos >= 60) errores.push('Segundos: 0–59.999');

    if (errores.length) {
      errorEl.classList.remove('hidden');
      resultEl.classList.add('hidden');
      dlg.querySelector('#dms-error-text').textContent = errores.join('. ');
      return;
    }

    errorEl.classList.add('hidden');
    var dd = grados + minutos / 60 + segundos / 3600;
    dmsState.signedDegrees = (dir === 'S' || dir === 'W') ? -dd : dd;
    resultEl.classList.remove('hidden');
    dlg.querySelector('#dms-result-text').textContent = dmsState.signedDegrees.toFixed(6) + '°';
  }

  function capturarDMS(dlg) {
    var campo = document.getElementById('id_' + dmsState.coordType);
    if (!campo) return;
    campo.value = dmsState.signedDegrees.toFixed(6);
    campo.dispatchEvent(new Event('input'));

    var grados  = parseFloat(dlg.querySelector('#dms-degrees').value)  || 0;
    var minutos = parseFloat(dlg.querySelector('#dms-minutes').value)  || 0;
    var segundos= parseFloat(dlg.querySelector('#dms-seconds').value)  || 0;
    var dir     = dlg.querySelector('input[name="direction"]:checked')?.value || '';
    var helpEl  = document.getElementById('help-text-' + dmsState.coordType);
    if (helpEl) helpEl.textContent = grados + '° ' + minutos + "' " + segundos + '" ' + dir;

    dlg.close();
  }

})();
