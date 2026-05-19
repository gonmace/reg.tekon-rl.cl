import DataTable from 'datatables.net-dt';
import "./ubicarMap.js"
import "./convertCoords.js"

// Importar el componente Alert desde el script global
const Alert = window.Alert;

DataTable.ext.classes.container = "dt-container table table-sm !table-zebra w-full";
DataTable.ext.classes.thead = {
    row: "bg-accent text-white uppercase",
};

// Configuración genérica para cualquier aplicación de registros
const CONFIG = {
    // URLs de la API - se pueden configurar desde el template
    apiBaseUrl: window.API_BASE_URL || '/txtss/api/v1/',
    registrosUrl: window.REGISTROS_URL || '/txtss/api/v1/registros/',
    usuariosUrl: window.USUARIOS_URL || '/txtss/api/v1/usuarios/usuarios_ito/',
    activarUrl: window.ACTIVAR_URL || '/txtss/activar/',
    
    // Configuración de la tabla
    tableId: window.TABLE_ID || '#registros-table',
    pageLength: window.PAGE_LENGTH || 10,
    
    // Configuración de permisos
    isSuperuser: window.isSuperuser || false,
    
    // Configuración de columnas
    columns: window.TABLE_COLUMNS || [
        { data: 'sitio.pti_cell_id', className: '!text-center', title: 'PTI ID' },
        { data: 'sitio.operator_id', className: '!text-center', title: 'Operador ID' },
        { data: 'sitio.name', className: 'w-fit max-w-40', title: 'Nombre Sitio' },
        { 
            data: 'user.username', 
            className: '!text-center',
            width: '150px',
            title: 'ITO',
            editable: true
        }
    ],
    
    // Configuración de acciones
    showActions: window.SHOW_ACTIONS !== false,
    actionsUrl: window.ACTIONS_URL || '/txtss/registros/',
    
    // Configuración de idioma
    language: {
        search: "_INPUT_",
        searchPlaceholder: "Buscar...",
        lengthMenu: "_MENU_ Registros",
        info: "_START_ al _END_ de _TOTAL_ ",
        infoEmpty: "0 al 0 de 0",
        infoFiltered: "(filtrado de _MAX_ registros)",
    }
};

class GenericRegistrosTable {
    constructor(config = {}) {
        this.config = { ...CONFIG, ...config };
        this.usuariosIto = [];
        this.tabla = null;
        this.init();
    }
    
    async init() {
        try {
            await this.cargarUsuariosIto();
            this.inicializarTabla();
            this.configurarEventos();
        } catch (error) {
            console.error('Error inicializando tabla:', error);
            // Inicializar tabla incluso si falla la carga de usuarios ITO
            this.inicializarTabla();
            this.configurarEventos();
        }
    }
    
    async cargarUsuariosIto() {
        try {
            const response = await fetch(this.config.usuariosUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.usuariosIto = await response.json();
        } catch (error) {
            console.error('Error cargando usuarios ITO:', error);
            this.usuariosIto = [];
        }
    }
    
    inicializarTabla() {
        const columns = this.config.columns.map(col => {
            if (col.data === 'user.username' && this.config.isSuperuser) {
                return {
                    ...col,
                    render: (data, type, row) => this.renderItoCell(data, type, row)
                };
            }
            return col;
        });
        
        // Agregar columna de acciones si está habilitada
        if (this.config.showActions && this.config.isSuperuser) {
            columns.push({
                data: null,
                orderable: false,
                className: 'text-center',
                render: (data, type, row) => this.renderActionsCell(data, type, row)
            });
        }
        
        this.tabla = new DataTable(this.config.tableId, {
            ajax: {
                url: this.config.registrosUrl,
                dataSrc: '',
            },
            columns: columns,
            responsive: true,
            pageLength: this.config.pageLength,
            order: [[1, 'asc']],
            dom: 'rt<"flex justify-between items-center"<"info"i><"length"l><"pagination"p>>',
            language: this.config.language,
            autoWidth: false,
            bStateSave: true
        });
        
        // Configurar buscador personalizado
        this.configurarBuscador();
    }
    
    renderItoCell(data, type, row) {
        if (type === 'display') {
            if (this.config.isSuperuser) {
                let selectHtml = '<div class="ito-cell-container">';
                selectHtml += '<span class="ito-text" style="cursor: pointer;" data-registro-id="' + row.id + '">';
                selectHtml += (data || 'Sin asignar') + ' <i class="fa-solid fa-pen-to-square text-xs text-warning ml-1"></i></span>';
                selectHtml += '<select class="ito-select select select-warning select-sm select-bordered w-full max-w-full" style="display: none;" data-registro-id="' + row.id + '">';
                selectHtml += '<option value="">Seleccionar ITO</option>';
                
                this.usuariosIto.forEach(usuario => {
                    const selected = (row.user && row.user.id === usuario.id) ? 'selected' : '';
                    selectHtml += '<option value="' + usuario.id + '" ' + selected + '>' + usuario.username + '</option>';
                });
                
                selectHtml += '</select></div>';
                return selectHtml;
            } else {
                return data || 'Sin asignar';
            }
        }
        return data || 'Sin asignar';
    }
    
    renderActionsCell(data, type, row) {
        return `
            <a 
                type="button"
                href="${this.config.actionsUrl}${row.id}/"
                class="btn btn-lg btn-success btn-circle text-lg sombra"
                data-id="${row.id}" 
                title="${row.sitio.name}"
            >
                <i class="fa-regular fa-pen-to-square"></i>
            </a>
        `;
    }
    
    configurarBuscador() {
        const buscador = document.getElementById('buscadorPersonalizado');
        if (buscador && this.tabla) {
            buscador.addEventListener('keyup', function () {
                this.tabla.search(this.value).draw();
            }.bind(this));
        }
    }
    
    configurarEventos() {
        if (!this.config.isSuperuser) return;
        
        const registrosTable = document.querySelector(this.config.tableId);
        if (!registrosTable) return;
        
        // Evento para hacer clic en el texto y mostrar el select
        registrosTable.addEventListener('click', (e) => {
            if (e.target.classList.contains('ito-text')) {
                this.mostrarSelect(e.target);
            }
        });
        
        // Evento para cambiar el valor del select
        registrosTable.addEventListener('change', (e) => {
            if (e.target.classList.contains('ito-select')) {
                this.actualizarIto(e.target);
            }
        });
        
        // Evento para perder foco del select
        registrosTable.addEventListener('blur', (e) => {
            if (e.target.classList.contains('ito-select')) {
                this.ocultarSelect(e.target);
            }
        }, true);
    }
    
    mostrarSelect(textSpan) {
        const registroId = textSpan.dataset.registroId;
        const cell = textSpan.closest('td');
        const select = cell.querySelector('.ito-select');
        
        textSpan.style.display = 'none';
        select.style.display = 'block';
        select.focus();
    }
    
    ocultarSelect(select) {
        const cell = select.closest('td');
        const textSpan = cell.querySelector('.ito-text');
        
        setTimeout(() => {
            select.style.display = 'none';
            textSpan.style.display = 'inline';
        }, 200);
    }
    
    async actualizarIto(select) {
        const registroId = select.dataset.registroId;
        const newUserId = select.value;
        const cell = select.closest('td');
        const textSpan = cell.querySelector('.ito-text');
        
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const rowData = this.tabla.row(cell.closest('tr')).data();
            
            const response = await fetch(`${this.config.registrosUrl}${registroId}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({
                    sitio_id: rowData.sitio.id,
                    user_id: newUserId,
                    is_deleted: rowData.is_deleted
                })
            });
            
            if (!response.ok) {
                throw new Error('Error en la actualización');
            }
            
            const data = await response.json();
            
            // Actualizar el texto mostrado
            const selectedUser = this.usuariosIto.find(u => u.id == newUserId);
            textSpan.innerHTML = (selectedUser ? selectedUser.username : 'Sin asignar') + ' <i class="fa-solid fa-pen-to-square text-xs text-gray-400 ml-1"></i>';
            
            // Ocultar select y mostrar texto
            select.style.display = 'none';
            textSpan.style.display = 'inline';
            
            Alert.success('ITO actualizado exitosamente', {
                autoHide: 3000,
                dismissible: true
            });
            
        } catch (error) {
            console.error('Error:', error);
            
            // Restaurar valor original
            const rowData = this.tabla.row(cell.closest('tr')).data();
            const originalUser = this.usuariosIto.find(u => u.id == rowData.user.id);
            textSpan.innerHTML = (originalUser ? originalUser.username : 'Sin asignar') + ' <i class="fa-solid fa-pen-to-square text-xs text-gray-400 ml-1"></i>';
            
            // Ocultar select y mostrar texto
            select.style.display = 'none';
            textSpan.style.display = 'inline';
            
            Alert.error('Error al actualizar ITO. Por favor, inténtalo de nuevo.', {
                autoHide: 0,
                dismissible: true
            });
        }
    }
}

class GenericModalHandler {
    constructor(config = {}) {
        console.log('GenericModalHandler constructor iniciado');
        this.config = {
            modalId: window.MODAL_ID || '#activar-registro-modal',
            activarBtnId: window.ACTIVAR_BTN_ID || '#activar-registro-btn',
            activarUrl: window.ACTIVAR_URL || '/txtss/activar/',
            ...config
        };
        console.log('Configuración del modal:', this.config);
        this.modal = null;
        this.activarBtn = null;
        this.init();
    }
    
    init() {
        console.log('GenericModalHandler init iniciado');
        this.modal = document.getElementById(this.config.modalId.replace('#', ''));
        this.activarBtn = document.getElementById(this.config.activarBtnId.replace('#', ''));
        
        console.log('Modal encontrado:', this.modal);
        console.log('Botón activar encontrado:', this.activarBtn);
        
        if (this.activarBtn && this.modal) {
            console.log('Configurando eventos del modal...');
            this.configurarEventos();
        } else {
            console.error('No se encontraron los elementos del modal');
        }
    }
    
    configurarEventos() {
        console.log('Configurando eventos del modal...');
        
        // Abrir modal
        this.activarBtn.addEventListener("click", () => {
            console.log('Botón activar clickeado');
            this.modal.showModal();
        });
        
        // Cerrar modal
        window.closeModal = () => {
            console.log('Cerrando modal');
            this.modal.close();
        };
        
        // Manejar formulario
        const form = this.modal.querySelector('form');
        console.log('Formulario encontrado:', form);
        if (form) {
            console.log('Agregando event listener al formulario');
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        } else {
            console.error('No se encontró el formulario en el modal');
        }
    }
    
    async handleFormSubmit(e) {
        e.preventDefault();
        
        console.log('Formulario enviado');
        
        const formData = new FormData(e.target);
        
        // Verificar que los campos requeridos estén presentes
        const sitio = formData.get('sitio');
        const user = formData.get('user');
        const title = formData.get('title');
        const description = formData.get('description');
        
        console.log('Datos del formulario:', {
            sitio,
            user,
            title,
            description
        });
        
        if (!sitio || !user) {
            Alert.error('Por favor completa todos los campos requeridos.', {
                autoHide: 3000,
                dismissible: true
            });
            return;
        }
        
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            console.log('CSRF Token:', csrfToken);
            console.log('URL de activación:', this.config.activarUrl);
            
            const response = await fetch(this.config.activarUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData
            });
            
            console.log('Respuesta del servidor:', response.status, response.statusText);
            
            const result = await response.json();
            console.log('Datos de respuesta:', result);
            
            if (response.ok && result.success) {
                this.modal.close();
                
                Alert.success(result.message || 'Registro activado exitosamente', {
                    autoHide: 3000
                });
                
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                // Manejar errores del servidor
                const errorMessage = result.message || 'Error al activar el registro';
                console.error('Error del servidor:', errorMessage);
                Alert.error(errorMessage, {
                    autoHide: 0,
                    dismissible: true
                });
            }
            
        } catch (error) {
            console.error('Error en la petición:', error);
            Alert.error('Error al crear el registro. Por favor, inténtalo de nuevo.', {
                autoHide: 0,
                dismissible: true
            });
        }
    }
}

// Inicialización cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", function () {
    console.log('DOM cargado, inicializando componentes...');
    
    // Inicializar tabla genérica
    console.log('Inicializando GenericRegistrosTable...');
    new GenericRegistrosTable();
    
    // Inicializar manejador de modal genérico
    console.log('Inicializando GenericModalHandler...');
    new GenericModalHandler();
    
    console.log('Componentes inicializados');
});

// Exportar clases para uso en otros módulos
export { GenericRegistrosTable, GenericModalHandler, CONFIG }; 