// Widget tabla_avance_widget: tabla de ítems con totales en vivo.
// Lee el estado inicial de <script id="tabla-avance-data"> y escribe el resultado
// en los inputs ocultos "partidas" (JSON) y "plantilla" del form del paso.
(function () {
  function fmt(n, d) {
    return Number(n || 0).toLocaleString('es-CL', { minimumFractionDigits: d, maximumFractionDigits: d });
  }
  function clamp(v) {
    var n = parseFloat(String(v).replace(',', '.'));
    if (isNaN(n)) n = 0;
    return Math.min(100, Math.max(0, n));
  }
  function uid() { return Math.random().toString(36).slice(2, 14); }

  function init(root) {
    var data;
    try { data = JSON.parse(document.getElementById('tabla-avance-data').textContent); }
    catch (e) { return; }
    var puedeEstructura = !!data.puede_editar_estructura;
    var tbody = root.querySelector('tbody');
    var hidden = root.querySelector('.tabla-avance-json');
    var hiddenPlantilla = root.querySelector('.tabla-avance-plantilla-hidden');
    var selPlantilla = root.querySelector('#tabla-avance-plantilla');
    var aviso = root.querySelector('.tabla-avance-aviso');
    var filas = (data.filas || []).map(function (f) {
      return { id: f.id, nombre: f.nombre, incidencia: f.incidencia, anterior: f.anterior, actual: f.actual };
    });
    hiddenPlantilla.value = data.plantilla || '';

    // si el form volvió con error, el hidden trae lo que el usuario había escrito
    try {
      var vigente = JSON.parse(hidden.value);
      if (Array.isArray(vigente) && vigente.length) {
        var previos = {};
        filas.forEach(function (f) { previos[f.id] = f.anterior; });
        filas = vigente.map(function (p) {
          return { id: p.id, nombre: p.nombre, incidencia: p.incidencia, actual: p.actual, anterior: previos[p.id] || 0 };
        });
      }
    } catch (e) { /* estado del servidor */ }

    if (puedeEstructura) {
      root.querySelector('.tabla-avance-estructura').classList.remove('hidden');
      root.querySelector('.tabla-avance-estructura').classList.add('flex');
      root.querySelectorAll('.tabla-avance-col-acc').forEach(function (c) { c.classList.remove('hidden'); });
      (data.plantillas || []).forEach(function (p, i) {
        var o = document.createElement('option');
        o.value = String(i); o.textContent = p.nombre;
        selPlantilla.appendChild(o);
      });
    }

    function celdaNum(txt, extra) {
      var td = document.createElement('td');
      td.className = 'text-right tabular-nums ' + (extra || '');
      td.textContent = txt;
      return td;
    }

    function inputNum(valor, onChange) {
      var i = document.createElement('input');
      i.type = 'number'; i.min = '0'; i.max = '100'; i.step = '0.1'; i.inputMode = 'decimal';
      i.className = 'input input-bordered input-xs w-20 text-right';
      i.value = valor;
      i.addEventListener('input', function () { onChange(i.value); });
      return i;
    }

    function render() {
      tbody.textContent = '';
      filas.forEach(function (f, idx) {
        var tr = document.createElement('tr');
        var tdN = document.createElement('td');
        if (puedeEstructura) {
          var n = document.createElement('input');
          n.type = 'text'; n.className = 'input input-bordered input-xs w-full min-w-40';
          n.value = f.nombre; n.maxLength = 120;
          n.addEventListener('input', function () { f.nombre = n.value; guardar(); });
          tdN.appendChild(n);
        } else { tdN.textContent = f.nombre; }
        tr.appendChild(tdN);

        var tdI = document.createElement('td'); tdI.className = 'text-right';
        if (puedeEstructura) {
          tdI.appendChild(inputNum(f.incidencia, function (v) { f.incidencia = clamp(v); calcular(); guardar(); }));
        } else { tdI.textContent = fmt(f.incidencia, 1); }
        tr.appendChild(tdI);

        tr.appendChild(celdaNum(fmt(f.anterior, 1), 'text-base-content/60'));

        var tdA = document.createElement('td'); tdA.className = 'text-right';
        tdA.appendChild(inputNum(f.actual, function (v) { f.actual = clamp(v); calcular(); guardar(); }));
        tr.appendChild(tdA);

        var tdAc = celdaNum('', ''); tdAc.dataset.col = 'acum'; tr.appendChild(tdAc);
        var tdT = celdaNum('', 'font-medium'); tdT.dataset.col = 'total'; tr.appendChild(tdT);

        if (puedeEstructura) {
          var tdX = document.createElement('td');
          var b = document.createElement('button');
          b.type = 'button'; b.className = 'btn btn-xs btn-ghost btn-circle'; b.title = 'Quitar ítem';
          var ic = document.createElement('i'); ic.className = 'fa-solid fa-trash text-delete';
          b.appendChild(ic);
          b.addEventListener('click', function () { filas.splice(idx, 1); render(); });
          tdX.appendChild(b); tr.appendChild(tdX);
        }
        tbody.appendChild(tr);
      });
      calcular(); guardar();
    }

    function calcular() {
      var total = 0, incid = 0;
      Array.prototype.forEach.call(tbody.rows, function (tr, i) {
        var f = filas[i];
        var acum = Math.min(100, (f.anterior || 0) + (f.actual || 0));
        var t = (f.incidencia || 0) * acum / 100;
        total += t; incid += (f.incidencia || 0);
        tr.querySelector('[data-col=acum]').textContent = fmt(acum, 1);
        tr.querySelector('[data-col=total]').textContent = fmt(t, 1);
      });
      root.querySelector('.tabla-avance-total').textContent = fmt(total, 1) + ' %';
      root.querySelector('.tabla-avance-suma-incidencia').textContent = fmt(incid, 1);
      var mal = puedeEstructura && filas.length && Math.abs(incid - 100) > 0.001;
      aviso.classList.toggle('hidden', !(mal || (!filas.length)));
      if (!filas.length) {
        aviso.textContent = puedeEstructura
          ? 'Este sitio aún no tiene ítems: aplica una plantilla o agrega ítems.'
          : 'Este sitio aún no tiene ítems definidos. Pide a un administrador que los configure.';
      } else if (mal) {
        aviso.textContent = 'La suma de incidencias es ' + fmt(incid, 1) + '% (debería ser 100%).';
      }
    }

    function guardar() {
      hidden.value = JSON.stringify(filas.map(function (f) {
        return { id: f.id, nombre: f.nombre, incidencia: f.incidencia, actual: f.actual };
      }));
    }

    if (puedeEstructura) {
      root.querySelector('.tabla-avance-aplicar').addEventListener('click', function () {
        var p = (data.plantillas || [])[parseInt(selPlantilla.value, 10)];
        if (!p) return;
        if (filas.length && !window.confirm('Esto reemplaza los ítems actuales. ¿Continuar?')) return;
        filas = (p.partidas || []).map(function (x) {
          return { id: uid(), nombre: x.nombre, incidencia: Number(x.incidencia) || 0, anterior: 0, actual: 0 };
        });
        hiddenPlantilla.value = p.nombre;
        render();
      });
      root.querySelector('.tabla-avance-agregar').addEventListener('click', function () {
        filas.push({ id: uid(), nombre: 'Nuevo ítem', incidencia: 0, anterior: 0, actual: 0 });
        render();
      });
    }
    render();
  }

  function boot() { var r = document.getElementById('tabla-avance'); if (r) init(r); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
