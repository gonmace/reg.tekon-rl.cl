// Script para manejar la navegación entre páginas y evitar flash del tema
(function() {
    'use strict';
    
    // Función para aplicar el tema inmediatamente
    function applyTheme() {
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const theme = savedTheme || (prefersDark ? 'dark' : 'light');
        document.documentElement.setAttribute('data-theme', theme);
    }
    
    // Aplicar tema inmediatamente si no está ya aplicado
    if (!document.documentElement.hasAttribute('data-theme')) {
        applyTheme();
    }
    
    // Interceptar navegación para aplicar tema antes de la carga
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a');
        if (link && link.href && !link.href.startsWith('javascript:') && !link.href.startsWith('#')) {
            // Guardar el tema actual antes de navegar
            const currentTheme = document.documentElement.getAttribute('data-theme');
            if (currentTheme) {
                localStorage.setItem('theme', currentTheme);
            }
        }
    });
    
    // Aplicar tema en navegación con el botón atrás/adelante
    window.addEventListener('pageshow', function(e) {
        if (e.persisted) {
            // La página se cargó desde el cache del navegador
            applyTheme();
        }
    });
    
    // Aplicar tema cuando la página se vuelve visible
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            applyTheme();
        }
    });
})(); 