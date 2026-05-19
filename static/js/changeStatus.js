/**
 * ChangeStatus.js - Lógica genérica para edición inline en tablas
 * Reutilizable para cualquier campo que necesite edición inline
 */

// Usar la librería de alertas global
// La librería ya está disponible como window.Alert desde alert-component.js

class ChangeStatus {
    constructor(config) {
        this.config = {
            textClass: config.textClass,           // Clase CSS del texto editable
            selectClass: config.selectClass,       // Clase CSS del select
            containerClass: config.containerClass, // Clase CSS del contenedor
            apiUrl: config.apiUrl,                 // URL de la API para actualizar
            fieldName: config.fieldName,           // Nombre del campo en el request
            responseField: config.responseField,   // Campo en la respuesta para mostrar
            options: config.options || [],         // Opciones para el select
            badgeMapping: config.badgeMapping || {}, // Mapeo de valores a clases de badge
            ...config
        };
        
        this.initialized = false;
        this.init();
    }
    
    async init() {
        if (this.initialized) return;
        
        this.setupEventListeners();
        
        // Si hay una API para cargar opciones, cargarlas primero
        if (this.config.loadOptionsFromAPI) {
            await this.loadOptionsFromAPI();
        } else {
            this.populateSelects();
        }
        
        this.initialized = true;
    }
    
    setupEventListeners() {
    
        
        // Event listeners para mostrar/ocultar selects usando delegación
        document.addEventListener('click', (e) => {
            // Buscar el elemento padre que tenga la clase textClass
            const textElement = e.target.closest(`.${this.config.textClass}`);
            if (textElement) {
                
                this.showSelect(textElement);
            }
        });
        
        // Event listeners para cambios en selects
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains(this.config.selectClass)) {
                const value = e.target.value;
                if (value) {
                    this.updateValue(e.target, value);
                }
            }
        });
        
        // Event listeners para perder foco en selects
        document.addEventListener('blur', (e) => {
            if (e.target.classList.contains(this.config.selectClass)) {
                setTimeout(() => {
                    this.hideSelect(e.target);
                }, 100);
            }
        }, true);
    }
    
    showSelect(textElement) {
        
        const container = textElement.closest(`.${this.config.containerClass}`);
        
        if (container) {
            const textSpan = container.querySelector(`.${this.config.textClass}`);
            const select = container.querySelector(`.${this.config.selectClass}`);

            
            if (textSpan && select) {
                // Ocultar texto y mostrar select
                textSpan.style.display = 'none';
                select.style.display = 'block';
                select.focus();
                
            }
        }
    }
    
    hideSelect(selectElement) {
        const container = selectElement.closest(`.${this.config.containerClass}`);
        if (container) {
            const textSpan = container.querySelector(`.${this.config.textClass}`);
            const select = container.querySelector(`.${this.config.selectClass}`);
            
            if (textSpan && select) {
                textSpan.style.display = 'inline';
                select.style.display = 'none';
            }
        }
    }
    
    async loadOptionsFromAPI() {
        try {
            const response = await fetch(this.config.loadOptionsFromAPI);
            if (response.ok) {
                const data = await response.json();
                
                // Formatear las opciones usando el formateador personalizado
                this.config.options = data.map(item => this.config.optionFormatter(item));
                
                this.populateSelects();
            } else {
                throw new Error('Error al cargar opciones desde la API');
            }
        } catch (error) {
            console.error('Error:', error);
            window.Alert.error('Error al cargar opciones', {
                autoHide: 0,
                dismissible: true
            });
        }
    }
    
    populateSelects() {
        const selects = document.querySelectorAll(`.${this.config.selectClass}`);
        
        selects.forEach(select => {
            // Limpiar opciones existentes excepto la primera
            select.innerHTML = '<option value="">Seleccionar...</option>';
            
            // Agregar opciones
            this.config.options.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option.value;
                optionElement.textContent = option.text;
                select.appendChild(optionElement);
            });
        });
    }
    
    async updateValue(selectElement, value) {
        try {
            const registroId = selectElement.dataset.registroId;
            console.log('DEBUG: updateValue called');
            console.log('DEBUG: selectElement:', selectElement);
            console.log('DEBUG: registroId from dataset:', registroId);
            console.log('DEBUG: dataset completo:', selectElement.dataset);
            console.log('DEBUG: apiUrl template:', this.config.apiUrl);
            
            if (!registroId) {
                console.error('DEBUG: No se encontró registroId en el dataset');
                window.Alert.error('Error: No se pudo identificar el registro', {
                    autoHide: 0,
                    dismissible: true
                });
                return;
            }
            
            const finalUrl = this.config.apiUrl.replace('{registro_id}', registroId);
            console.log('DEBUG: URL final:', finalUrl);
            
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            console.log('DEBUG: CSRF Token encontrado:', !!csrfToken);
            
            const requestBody = {
                [this.config.fieldName]: value
            };
            console.log('DEBUG: Request body:', requestBody);
            
            const response = await fetch(finalUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify(requestBody)
            });
            
            console.log('DEBUG: Response status:', response.status);
            console.log('DEBUG: Response ok:', response.ok);
            
            if (response.ok) {
                const result = await response.json();
                console.log('DEBUG: Response data:', result);
                
                // Actualizar el texto mostrado
                const container = selectElement.closest(`.${this.config.containerClass}`);
                const textSpan = container.querySelector(`.${this.config.textClass}`);
                const selectedOption = selectElement.options[selectElement.selectedIndex];
                
                // Actualizar con badge si hay mapeo
                if (this.config.badgeMapping && this.config.badgeMapping[value]) {
                    const badgeClass = this.config.badgeMapping[value];
                    textSpan.innerHTML = `<span class="${badgeClass}">${selectedOption.textContent}</span>`;
                } else {
                    textSpan.innerHTML = `${selectedOption.textContent}`;
                }
                
                window.Alert.success('Campo actualizado exitosamente', {
                    autoHide: 3000,
                    dismissible: true
                });
            } else {
                const errorData = await response.json();
                console.log('DEBUG: Error response:', errorData);
                let errorMessage = 'Error al actualizar el campo.';
                
                if (errorData.message) {
                    errorMessage = errorData.message;
                }
                
                window.Alert.error(errorMessage, {
                    autoHide: 0,
                    dismissible: true
                });
                
                // Resetear el select
                selectElement.value = '';
            }
        } catch (error) {
            console.error('DEBUG: Error en updateValue:', error);
            window.Alert.error('Error al actualizar el campo. Por favor, inténtalo de nuevo.', {
                autoHide: 0,
                dismissible: true
            });
            
            // Resetear el select
            selectElement.value = '';
        }
    }
}

// Función para inicializar todos los cambios de estado
async function initializeAllChangeStatus() {
    
    // Configuración para ITO
    if (document.querySelectorAll('.ito-text').length > 0) {
        await new ChangeStatus({
            textClass: 'ito-text',
            selectClass: 'ito-select',
            containerClass: 'ito-cell-container',
            apiUrl: '/reg_construccion/api/v1/registros/{registro_id}/update_ito/',
            fieldName: 'user_id',
            responseField: 'user_name',
            options: [], // Se poblará dinámicamente desde la API
            loadOptionsFromAPI: '/reg_construccion/api/v1/users_ito/',
            optionFormatter: (item) => ({
                value: item.id,
                text: `${item.username}${item.first_name ? ` (${item.first_name} ${item.last_name || ''})` : ''}`
            })
        });
    }
    
    // Configuración para Constructor
    if (document.querySelectorAll('.constructor-text').length > 0) {
        await new ChangeStatus({
            textClass: 'constructor-text',
            selectClass: 'constructor-select',
            containerClass: 'constructor-cell-container',
            apiUrl: '/reg_construccion/api/v1/registros/{registro_id}/update_constructor/',
            fieldName: 'contractor_id',
            responseField: 'contratista_name',
            options: [], // Se poblará dinámicamente desde la API
            loadOptionsFromAPI: '/reg_construccion/api/v1/contractors/',
            optionFormatter: (item) => ({
                value: item.id,
                text: `${item.name} (${item.code})`
            })
        });
    }
    
    // Configuración para Estado
    if (document.querySelectorAll('.estado-text').length > 0) {
        await new ChangeStatus({
            textClass: 'estado-text',
            selectClass: 'estado-select',
            containerClass: 'estado-cell-container',
            apiUrl: '/reg_construccion/api/v1/registros/{registro_id}/update_estado/',
            fieldName: 'estado',
            responseField: 'estado_name',
            options: [
                { value: 'construccion', text: 'Construcción' },
                { value: 'paralizado', text: 'Paralizado' },
                { value: 'cancelado', text: 'Cancelado' },
                { value: 'concluido', text: 'Concluido' }
            ],
            badgeMapping: {
                // Mapeo inverso por texto también
                'Construcción': 'badge badge-success',
                'Paralizado': 'badge badge-warning',
                'Cancelado': 'badge badge-error',
                'Concluido': 'badge badge-info'
            }
        });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", function () {
    if (!window.changeStatusInitialized) {
        window.changeStatusInitialized = true;
        initializeAllChangeStatus().catch(console.error);
    }
});

// También ejecutar cuando la página esté completamente cargada
window.addEventListener("load", function () {
    setTimeout(function() {
        if (!window.changeStatusInitialized) {
            window.changeStatusInitialized = true;
            initializeAllChangeStatus().catch(console.error);
        }
    }, 1000);
});

// Ejecutar cada segundo hasta que se encuentren los elementos
let checkIntervalChangeStatus = setInterval(function() {
    const hasElements = document.querySelectorAll('.ito-text, .constructor-text, .estado-text').length > 0;
    if (hasElements) {
        clearInterval(checkIntervalChangeStatus);
        if (!window.changeStatusInitialized) {
            window.changeStatusInitialized = true;
            initializeAllChangeStatus().catch(console.error);
        }
    }
}, 1000);
