/*
 * photo-reorder.js — Reordenar tarjetas de fotos arrastrando y soltando.
 *
 * Sin dependencias. Funciona con mouse y touch usando Pointer Events y un
 * "handle" (icono de arrastre) en cada tarjeta, para no chocar con el scroll
 * del grid ni con los clicks de la imagen / inputs de descripción.
 *
 * Reordena en vivo: la tarjeta arrastrada se mueve de celda en celda dentro
 * del grid según la posición del puntero (no usa un clon flotante con
 * position:fixed, que se descuadra si algún ancestro tiene CSS transform).
 *
 * Uso:
 *   PhotoReorder.enable(containerEl, {
 *     item: '[data-photo-id]',     // selector de cada tarjeta arrastrable
 *     handle: '.reorder-handle',   // selector del tirador dentro de la tarjeta
 *     onReorder: function (ids) {} // recibe el nuevo orden de data-photo-id
 *   });
 *
 * Detecta tarjetas agregadas dinámicamente (event delegation), así que basta
 * con llamar enable() una vez sobre el contenedor.
 */
(function () {
  'use strict';

  function enable(container, opts) {
    if (!container || container.dataset.reorderInit) return;
    container.dataset.reorderInit = '1';

    opts = opts || {};
    var itemSel = opts.item || '[data-photo-id]';
    var handleSel = opts.handle || null;
    var onReorder = opts.onReorder || function () {};

    var dragging = null;
    var pointerId = null;
    var moved = false;

    function getItem(node) {
      if (!node || !node.closest) return null;
      var el = node.closest(itemSel);
      return el && container.contains(el) ? el : null;
    }

    // Tarjeta que está justo debajo del puntero (ignorando la que arrastramos).
    function itemUnderPoint(x, y) {
      var prev = dragging.style.pointerEvents;
      dragging.style.pointerEvents = 'none';
      var below = document.elementFromPoint(x, y);
      dragging.style.pointerEvents = prev;
      return below ? getItem(below) : null;
    }

    function onDown(e) {
      if (e.button != null && e.button !== 0) return;
      if (!handleSel || !e.target.closest(handleSel)) return;
      var item = getItem(e.target);
      if (!item) return;

      e.preventDefault();
      pointerId = e.pointerId;
      dragging = item;
      moved = false;
      item.classList.add('reorder-dragging');
      item.style.opacity = '0.55';
      item.style.transform = 'scale(1.03)';
      try { e.target.setPointerCapture(e.pointerId); } catch (err) {}
      if (navigator.vibrate) { try { navigator.vibrate(8); } catch (err) {} }

      window.addEventListener('pointermove', onMove, { passive: false });
      window.addEventListener('pointerup', onUp);
      window.addEventListener('pointercancel', onUp);
    }

    function onMove(e) {
      if (e.pointerId !== pointerId || !dragging) return;
      e.preventDefault();
      moved = true;

      var target = itemUnderPoint(e.clientX, e.clientY);
      if (!target || target === dragging) return;

      var box = target.getBoundingClientRect();
      // Insertar antes o después según el lado del centro de la celda destino.
      var after = e.clientX > box.left + box.width / 2;
      if (after) {
        container.insertBefore(dragging, target.nextSibling);
      } else {
        container.insertBefore(dragging, target);
      }
    }

    function onUp(e) {
      if (pointerId != null && e.pointerId !== pointerId) return;
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      window.removeEventListener('pointercancel', onUp);

      if (dragging) {
        dragging.classList.remove('reorder-dragging');
        dragging.style.opacity = '';
        dragging.style.transform = '';
        if (moved) {
          var ids = [].map.call(
            container.querySelectorAll(itemSel),
            function (el) { return el.dataset.photoId; }
          ).filter(Boolean);
          onReorder(ids);
        }
      }
      dragging = null;
      pointerId = null;
      moved = false;
    }

    container.addEventListener('pointerdown', onDown);
  }

  window.PhotoReorder = { enable: enable };
})();
