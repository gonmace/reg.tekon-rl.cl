import "./convertCoords.js"
import "leaflet/dist/leaflet.css";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import { marker, icon } from "leaflet";

import { LocateControl } from "leaflet.locatecontrol";
import "leaflet.locatecontrol/dist/L.Control.Locate.min.css";

document.addEventListener("DOMContentLoaded", function () {
    const btnGuardarUbicacion = document.getElementById("btn-guardar-ubicacion");
    
    btnGuardarUbicacion.addEventListener("click", function () {
        const latInput = document.getElementById('id_lat');
        const lngInput = document.getElementById('id_lon');
        const lat = currentMarker.getLatLng().lat;
        const lon = currentMarker.getLatLng().lng;
        latInput.value = lat.toFixed(7);
        lngInput.value = lon.toFixed(7);
        modal.close();
    });

  function actualizarMarker(lat, lng, popup = null) {
    // Remover el marcador anterior si existe
    if (currentMarker) {
      map.removeLayer(currentMarker);
    } else {
        btnGuardarUbicacion.classList.remove("btn-disabled");
    }

    // Crear nuevo marcador en la posición del clic
    currentMarker = marker([lat, lng], {
      icon: icon({
        iconUrl: markerIcon,
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowUrl: markerShadow,
        shadowSize: [41, 41],
      }),
    }).addTo(map);

    if (popup) {
      currentMarker.bindPopup(popup).openPopup();
    }

    // Opcional: mostrar un popup con las coordenadas
    console.log(`Coordenadas: ${lat.toFixed(7)}, ${lng.toFixed(7)}`);
  }

  function limpiarModal() {
    if (currentMarker) {
        map.removeLayer(currentMarker);
        currentMarker = null;
    }
    btnGuardarUbicacion.classList.add("btn-disabled");
  }

  const modal = document.getElementById("mapa");
  modal.addEventListener("close", limpiarModal);

  const isMobile =
    /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent
    );

  // Configuración del mapa optimizada para móviles
  const mapOptions = {
    zoomControl: false,
  };

  if (isMobile) {
    mapOptions.tap = true;
    mapOptions.touchZoom = true;
    mapOptions.scrollWheelZoom = false;
    mapOptions.doubleClickZoom = false;
    mapOptions.dragging = true;
    mapOptions.zoomControl = false;
  }

  const map = L.map("map", mapOptions).setView(
    [-33.45, -70.66],
    isMobile ? 10 : 13
  );

  // Definir capas de mapas
  let openStreetMap_Mapnik = L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      attribution: "© OpenStreetMap contributors",
    }
  );

  let esri_WorldImagery = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    {
      attribution:
        "Tiles © Esri — Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
    }
  );

  esri_WorldImagery.addTo(map);

  // Opciones de capas base
  let baseMaps = {
    OpenStreetMap: openStreetMap_Mapnik,
    "Esri Satellite": esri_WorldImagery,
  };

  // Añadir control de capas base
  L.control.layers(baseMaps).addTo(map);
  L.control
    .zoom({
      position: "bottomright",
    })
    .addTo(map);

  const locateControl = new LocateControl();
  locateControl.options.flyTo = true;
  locateControl.options.position = "topright";
  locateControl.options.drawCircle = false;
  locateControl.options.drawMarker = false;

  locateControl.addTo(map);

  map.on("locationfound", function (e) {
    const lat = e.latitude;
    const lng = e.longitude;
    actualizarMarker(lat, lng, "Tu ubicación");
  });

  // Crear un marcador inicial
  let currentMarker = null;

//   // Función para actualizar los campos de latitud y longitud
//   function actualizarCampos(lat, lng) {
//     const latInput = document.getElementById("id_lat");
//     const lngInput = document.getElementById("id_lng");

//     if (latInput) {
//       latInput.value = lat.toFixed(7);
//     }
//     if (lngInput) {
//       lngInput.value = lng.toFixed(7);
//     }
//   }



  // Optimizaciones específicas para móviles
  if (isMobile) {
    // Ajustar el zoom inicial para móviles
    map.setZoom(10);

    // Mejorar la experiencia táctil
    map.on("touchstart", function () {
      // Prevenir zoom accidental en móviles
      map.doubleClickZoom.disable();
    });

    map.on("touchend", function () {
      // Rehabilitar después de un delay
      setTimeout(() => {
        map.doubleClickZoom.enable();
      }, 300);
    });
  }

  // Evento de clic en el mapa
  map.on("click", function (e) {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;

    actualizarMarker(lat, lng);
  });

  const btnUbicarMapa = document.getElementById("btn-ubicar-mapa");
  btnUbicarMapa.addEventListener("click", function () {
    // Verificar si los campos de latitud y longitud tienen valores
    const latInput = document.getElementById('id_lat');
    const lngInput = document.getElementById('id_lon');
    const help_text_lat = document.getElementById(`help-text-lat`);
    const help_text_lon = document.getElementById(`help-text-lon`);

    if (help_text_lat) {
        help_text_lat.textContent = "Grados decimales.";
    }
    if (help_text_lon) {
        help_text_lon.textContent = "Grados decimales.";
    }

    if (latInput && lngInput && latInput.value && lngInput.value) {
      // Convertir los valores a números
      const lat = parseFloat(latInput.value);
      const lng = parseFloat(lngInput.value);
      
      // Verificar que los valores son números válidos
      if (!isNaN(lat) && !isNaN(lng)) {
        // Ir a la ubicación especificada
        map.setView([lat, lng], isMobile ? 15 : 16);
        
        // Colocar el marcador en esa ubicación
        actualizarMarker(lat, lng, "Ubicación guardada");
      }
    }
    
    modal.showModal();
  });
});



