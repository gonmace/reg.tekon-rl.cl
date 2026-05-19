const state = {
  signedDegrees: 0,
  coordType: "",
};

document.addEventListener("DOMContentLoaded", function () {

  document.querySelectorAll("button[data-target]").forEach((button) => {
    button.addEventListener("click", () => {
      state.coordType = button.dataset.target;
      if (state.coordType === "lat") {
        convertir(state.coordType);
      } else if (state.coordType === "lon") {
        convertir(state.coordType);
      }
    });
  });

  const direction_lat = `
        <div class="mb-4">
          <label>Dirección</label>
          <div class="flex space-x-4">
            <label class="flex items-center">
              <input type="radio" name="direction" value="S" class="radio radio-warning radio-xs" checked>
              <span class="text-sm ml-1">S (Sur)</span>
            </label>
            <label class="flex items-center">
              <input type="radio" name="direction" value="N" class="radio radio-warning radio-xs">
              <span class="text-sm ml-1">N (Norte)</span>
            </label>
          </div>
        </div>`;

  const direction_lon = `
        <div class="mb-4">
          <label>Dirección</label>
          <div class="flex space-x-4">
            <label class="flex items-center">
              <input type="radio" name="direction" value="W" class="radio radio-warning radio-xs" checked>
              <span class="text-sm ml-1">W (Oeste)</span>
            </label>
            <label class="flex items-center">
              <input type="radio" name="direction" value="E" class="radio radio-warning radio-xs">
              <span class="text-sm ml-1">E (Este)</span>
            </label>
          </div>
        </div>`;

  function convertir() {
    const modal = document.createElement("dialog");
    modal.id = `modal-${state.coordType}`;
    modal.classList.add("modal", "modal-bottom", "sm:modal-middle");
    // Elige el bloque correcto según el tipo
    const direction_html = state.coordType === "lat" ? direction_lat : direction_lon;

    const modal_html = `
    <div class="modal-box bg-base-200">
      <form method="dialog">
        <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>
      </form>
      <!-- Header -->
      <h3 class="text-lg font-bold">Convierte DMS a DD</h3>

      <!-- Form -->
      <form id="coords-form" class="p-6 space-y-4">

        <!-- Direction Selector -->
        ${direction_html}

        <div class="grid grid-cols-3 gap-3">
          <div>
            <label for="degrees" class="block text-sm font-medium mb-1">Grados</label>
            <input type="number" id="degrees" name="degrees"
                   required
                   class="input validator input-success"
                   title="Deben ser grados de 0 a ${
                     state.coordType === "lat" ? "90" : "180"
                   }"
                   min="0" max="${
                     state.coordType === "lat" ? "90" : "180"
                   }" placeholder="0 a ${state.coordType === "lat" ? "90" : "180"}">
                   <p class="validator-hint">Debe estar entre 0 y ${
                     state.coordType === "lat" ? "90" : "180"
                   }</p>
          </div>
          <div>
            <label for="minutes" class="block text-sm font-medium mb-1">Minutos</label>
            <input type="number" id="minutes" name="minutes" 
                   class="input validator input-success"
                   title="Deben ser minutos de 0 a 59.999"
                   min="0" max="59.999" placeholder="0 a 59.999">
                   <p class="validator-hint">Debe estar entre 0 y 59.999</p>
          </div>
          <div>
            <label for="seconds" class="block text-sm font-medium mb-1">Segundos</label>
            <input type="number" id="seconds" name="seconds" 
                   class="input validator input-success"
                   title="Deben ser segundos de 0 a 59.999"
                   min="0" max="59.999" step="0.001" placeholder="0 a 59.999">
                   <p class="validator-hint">Debe estar entre 0 y 59.999</p>
          </div>
        </div>

        <!-- Result Display -->
        <div id="result-display" class="hidden">
          <div class="bg-secondary border border-success rounded-md p-4">
            <h3 class="text-sm font-medium mb-2">Resultado:</h3>
            <p id="result-text" class="text-lg font-mono text-secondary-content"></p>
          </div>
        </div>

        <!-- Error Display -->
        <div id="error-display" class="hidden">
          <div class="bg-error/50 border border-error rounded-md p-4">
            <p id="error-text" class="text-sm text-error-content"></p>
          </div>
        </div>

        <!-- Buttons -->
        <div class="flex justify-end space-x-3">
          <button id="button-capturar-coord" type="button" class="btn btn-success">
            Capturar coordenada
          </button>
        </div>
      </form>
    </div>`;
    // Inserta el bloque correcto
    modal.innerHTML = modal_html;
    document.body.appendChild(modal);
    modal.showModal();

    // Agregar event listeners para validación en tiempo real
    const inputs = modal.querySelectorAll('input[type="number"]');
    inputs.forEach((input) => {
      input.addEventListener("input", () => validateInputs(state.coordType));
    });

    // Agregar event listeners para los radio buttons de dirección
    const directionRadios = modal.querySelectorAll('input[name="direction"]');
    directionRadios.forEach((radio) => {
      radio.addEventListener("change", () => validateInputs(state.coordType));
    });

    // Agregar event listener para el botón de cerrar (X)
    const closeButton = modal.querySelector('button[class*="btn-circle"]');
    if (closeButton) {
      closeButton.addEventListener("click", function () {
        state.coordType = "";
        state.signedDegrees = 0;
        modal.close();
        modal.remove();
      });
    }

    // Agregar event listener para cerrar con Escape
    modal.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        modal.close();
        modal.remove();
      }
    });

    // Agregar event listener para el evento 'close' del modal
    modal.addEventListener("close", function () {
      state.coordType = "";
      state.signedDegrees = 0;
      modal.remove();
    });

    const btnCapturarCoord = document.getElementById("button-capturar-coord");
    if (btnCapturarCoord) {
      btnCapturarCoord.addEventListener("click", function () {
        calculateAndCloseModal(modal);
      });
    }
  }

});

// Función para validar inputs en tiempo real
function validateInputs(coordType) {
  const degrees = parseFloat(document.getElementById("degrees")?.value) || 0;
  const minutes = parseFloat(document.getElementById("minutes")?.value) || 0;
  const seconds = parseFloat(document.getElementById("seconds")?.value) || 0;
  const direction =
    document.querySelector('input[name="direction"]:checked')?.value || "S";
  const errorDisplay = document.getElementById("error-display");
  const resultDisplay = document.getElementById("result-display");

  // Validaciones
  let errors = [];
  // Validar límites según el tipo de coordenada
  if (coordType === "lat") {
    if (degrees < 0 || degrees > 90) {
      errors.push("Los grados de latitud deben estar entre 0 y 90");
    }
  } else {
    if (degrees < 0 || degrees > 180) {
      errors.push("Los grados de longitud deben estar entre 0 y 180");
    }
  }

  if (minutes < 0 || minutes >= 60) {
    errors.push("Los minutos deben estar entre 0 y 59");
  }
  if (seconds < 0 || seconds >= 60) {
    errors.push("Los segundos deben estar entre 0 y 59.999");
  }

  if (errors.length > 0) {
    errorDisplay.classList.remove("hidden");
    resultDisplay.classList.add("hidden");
    document.getElementById("error-text").textContent = errors.join(". ");
  } else {
    errorDisplay.classList.add("hidden");
    // Calcular y mostrar resultado en tiempo real
    const decimalDegrees = degrees + minutes / 60 + seconds / 3600;

    // Aplicar signo según la dirección
    state.signedDegrees = decimalDegrees;
    if (direction === "S" || direction === "W") {
      state.signedDegrees = -decimalDegrees;
    }

    resultDisplay.classList.remove("hidden");
    document.getElementById(
      "result-text"
    ).textContent = `${state.signedDegrees.toFixed(6)}°`;
  }
}

// Función para calcular y cerrar el modal
function calculateAndCloseModal(modal) {
  const degrees = parseFloat(document.getElementById("degrees").value) || 0;
  const minutes = parseFloat(document.getElementById("minutes").value) || 0;
  const seconds = parseFloat(document.getElementById("seconds").value) || 0;
  const direction = document.querySelector(
    'input[name="direction"]:checked'
  )?.value;

  const id_field_coord = `id_${state.coordType}`;
  const field_coord = document.getElementById(id_field_coord);
  field_coord.value = state.signedDegrees.toFixed(6);
  field_coord.dispatchEvent(new Event("input"));

  const help_text = document.getElementById(`help-text-${state.coordType}`);
  if (help_text) {
    help_text.textContent = `${degrees}° ${minutes}' ${seconds}" ${direction}`;
  }

  state.coordType = "";
  state.signedDegrees = 0;

  modal.close();
  modal.remove();
}
