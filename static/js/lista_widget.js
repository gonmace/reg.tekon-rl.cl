// Widget lista_widget: ítems (numerados o no; una línea o textarea) con agregar / quitar / reordenar.
// El estado viaja como JSON en <input name="entradas" class="lista-json">.
(function () {
  function init(root) {
    var ol = root.querySelector('.lista-items');
    var vacia = root.querySelector('.lista-vacia');
    var hidden = root.querySelector('.lista-json');
    var placeholder = root.dataset.placeholder || '';
    var max = parseInt(root.dataset.maxItems || '50', 10);
    var multilinea = root.dataset.multilinea === '1';
    var numerada = root.dataset.numerada !== '0';
    var inicial = [];
    try {
      var el = document.getElementById('lista-inicial');
      inicial = JSON.parse(el.textContent) || [];
      if (!Array.isArray(inicial)) inicial = [];
    } catch (e) { inicial = []; }
    // si el form se volvió a pintar tras un error, el hidden trae el estado vigente
    try {
      var vigente = JSON.parse(hidden.value);
      if (Array.isArray(vigente) && vigente.length) inicial = vigente;
    } catch (e) { /* se usa el inicial */ }

    function sync() {
      var vals = [];
      ol.querySelectorAll('input[type=text], textarea').forEach(function (i) { vals.push(i.value); });
      hidden.value = JSON.stringify(vals);
      vacia.hidden = vals.length > 0;
      ol.querySelectorAll('.lista-num').forEach(function (n, idx) { n.textContent = (idx + 1) + '.'; });
      var add = root.querySelector('.lista-add');
      if (add) add.disabled = vals.length >= max;
    }

    function btn(icon, title, onClick) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn btn-xs btn-ghost btn-circle';
      b.title = title;
      var i = document.createElement('i');
      i.className = icon;
      b.appendChild(i);
      b.addEventListener('click', onClick);
      return b;
    }

    function addItem(texto, focus) {
      var li = document.createElement('li');
      li.className = 'flex items-start gap-2';
      var n = document.createElement('span');
      n.className = 'lista-num w-6 pt-2 text-sm text-base-content/60 text-right shrink-0';
      if (!numerada) n.hidden = true;
      var input;
      if (multilinea) {
        input = document.createElement('textarea');
        input.rows = 3;
        input.className = 'textarea textarea-bordered textarea-sm flex-1 min-w-0';
      } else {
        input = document.createElement('input');
        input.type = 'text';
        input.className = 'input input-bordered input-sm flex-1 min-w-0';
      }
      input.placeholder = placeholder;
      input.value = texto || '';
      input.addEventListener('input', sync);
      if (!multilinea) {
        input.addEventListener('keydown', function (e) {
          if (e.key === 'Enter') { e.preventDefault(); addItem('', true); }
        });
      }
      var acciones = document.createElement('div');
      acciones.className = 'flex shrink-0';
      acciones.appendChild(btn('fa-solid fa-arrow-up', 'Subir', function () {
        if (li.previousElementSibling) { ol.insertBefore(li, li.previousElementSibling); sync(); }
      }));
      acciones.appendChild(btn('fa-solid fa-arrow-down', 'Bajar', function () {
        if (li.nextElementSibling) { ol.insertBefore(li.nextElementSibling, li); sync(); }
      }));
      acciones.appendChild(btn('fa-solid fa-trash text-delete', 'Quitar', function () {
        li.remove(); sync();
      }));
      li.appendChild(n); li.appendChild(input); li.appendChild(acciones);
      ol.appendChild(li);
      sync();
      if (focus) input.focus();
    }

    inicial.forEach(function (t) { addItem(String(t), false); });
    // Lista vacía: arranca con un campo listo para escribir («Agregar» es solo para sumar más).
    if (!inicial.length) addItem('', false);
    root.querySelector('.lista-add').addEventListener('click', function () {
      if (ol.children.length < max) addItem('', true);
    });
    sync();
  }

  function boot() { document.querySelectorAll('.lista-widget').forEach(init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
