import DataTable from 'datatables.net-dt';
import "./ubicarMap.js"
import "./convertCoords.js"
// Importar el componente Alert desde el script global
const Alert = window.Alert;

DataTable.ext.classes.container = "dt-container table table-sm !table-zebra w-full";
DataTable.ext.classes.thead = {
    row: "bg-accent text-white uppercase",
};

document.addEventListener("DOMContentLoaded", function () {
    const registrosTable = document.querySelector('#registros-table');

    if (registrosTable) {
        const isSuperuser = window.isSuperuser || false;

        // Cargar usuarios ITO disponibles
        let usuariosIto = [];
        
        // Función para inicializar la tabla después de cargar usuarios ITO
        function initializeTable() {
            const tabla = new DataTable('#registros-table', {
                ajax: {
                    url: '/txtss/api/v1/registros/',
                    dataSrc: '',
                    // dataSrc: function(json) {
                    //     console.log('Data de registros:', json);
                    //     return json;
                    // }
                },
                columns: [
                    { data: 'sitio.pti_cell_id', className: '!text-center' },
                    { data: 'sitio.operator_id', className: '!text-center' },
                    { data: 'sitio.name', className: 'w-fit max-w-40' },
                    { 
                        data: 'user.username', 
                        className: '!text-center',
                        width: '150px',
                        render: function (data, type, row) {
                            if (type === 'display') {
                                if (isSuperuser) {
                                    // Crear el HTML del select editable
                                    let selectHtml = '<div class="ito-cell-container">';
                                    selectHtml += '<span class="ito-text" style="cursor: pointer;" data-registro-id="' + row.id + '">';
                                    selectHtml += (data || 'Sin asignar') + ' <i class="fa-solid fa-pen-to-square text-xs text-warning ml-1"></i></span>';
                                    selectHtml += '<select class="ito-select select select-warning select-sm select-bordered w-full max-w-full" style="display: none;" data-registro-id="' + row.id + '">';
                                    selectHtml += '<option value="">Seleccionar ITO</option>';
                                    
                                    // Agregar opciones de usuarios ITO
                                    usuariosIto.forEach(usuario => {
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
                    },
                    ...(isSuperuser ? [{
                        data: null,
                        orderable: false,
                        className: 'text-center',
                        render: function (data, type, row) {
                            return `
                                <a 
                                    type="button"
                                    href="/txtss/registros/${data.id}/"
                                    class="btn btn-lg btn-success btn-circle text-lg sombra"
                                    data-id="${row.is_deleted.id}" 
                                    title="${row.sitio.name}"
                                >
                                    <i class="fa-regular fa-pen-to-square"></i>
                                </a>
                            `;
                        }
                    }] : [])
                ],
                responsive: true,
                pageLength: 10,
                order: [[1, 'asc']],
                dom: 'rt<"flex justify-between items-center"<"info"i><"length"l><"pagination"p>>',
                language: {
                    search: "_INPUT_",
                    searchPlaceholder: "Buscar...",
                    lengthMenu: "_MENU_ Registros",
                    info: "_START_ al _END_ de _TOTAL_ ",
                    infoEmpty: "0 al 0 de 0",
                    infoFiltered: "(filtrado de _MAX_ registros)",
                },
                autoWidth: false,
                bStateSave: true
            });

            // Buscador personalizado
            const buscador = document.getElementById('buscadorPersonalizado');
            if (buscador) {
                buscador.addEventListener('keyup', function () {
                    tabla.search(this.value).draw();
                });
            }

            // Delegación de eventos para el select editable
            if (isSuperuser) {
                // Evento para hacer clic en el texto y mostrar el select
                registrosTable.addEventListener('click', function(e) {
                    if (e.target.classList.contains('ito-text')) {
                        const registroId = e.target.dataset.registroId;
                        const cell = e.target.closest('td');
                        const textSpan = e.target;
                        const select = cell.querySelector('.ito-select');
                        
                        textSpan.style.display = 'none';
                        select.style.display = 'block';
                        select.focus();
                    }
                });

                // Evento para cambiar el valor del select
                registrosTable.addEventListener('change', function(e) {
                    if (e.target.classList.contains('ito-select')) {
                        const registroId = e.target.dataset.registroId;
                        const newUserId = e.target.value;
                        const cell = e.target.closest('td');
                        const textSpan = cell.querySelector('.ito-text');
                        const select = e.target;
                        
                        // Obtener el token CSRF
                        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                        
                        // Obtener los datos de la fila
                        const rowData = tabla.row(cell.closest('tr')).data();
                        
                        // Actualizar el registro
                        fetch(`/txtss/api/v1/registros/${registroId}/`, {
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
                        })
                        .then(response => {
                            if (response.ok) {
                                return response.json();
                            } else {
                                throw new Error('Error en la actualización');
                            }
                        })
                        .then(data => {
                            // Actualizar el texto mostrado
                            const selectedUser = usuariosIto.find(u => u.id == newUserId);
                            textSpan.innerHTML = (selectedUser ? selectedUser.username : 'Sin asignar') + ' <i class="fa-solid fa-pen-to-square text-xs text-gray-400 ml-1"></i>';
                            
                            // Ocultar select y mostrar texto
                            select.style.display = 'none';
                            textSpan.style.display = 'inline';
                            
                            // Mostrar mensaje de éxito

                                Alert.success('ITO actualizado exitosamente', {
                                    autoHide: 3000,
                                    dismissible: true
                                });

                        })
                        .catch(error => {
                            console.error('Error:', error);
                            
                            // Restaurar valor original
                            const originalUser = usuariosIto.find(u => u.id == rowData.user.id);
                            textSpan.innerHTML = (originalUser ? originalUser.username : 'Sin asignar') + ' <i class="fa-solid fa-pen-to-square text-xs text-gray-400 ml-1"></i>';
                            
                            // Ocultar select y mostrar texto
                            select.style.display = 'none';
                            textSpan.style.display = 'inline';
                            
                            // Mostrar mensaje de error personalizado
                            if (error.response) {
                                error.response.json().then(data => {
                                    if (data.errors && data.errors.non_field_errors) {
                                        Alert.error(data.errors.non_field_errors[0], {
                                            autoHide: 0,
                                            dismissible: true
                                        });
                                    } else if (data.message) {
                                        Alert.error(data.message, {
                                            autoHide: 0,
                                            dismissible: true
                                        });
                                    } else {
                                        Alert.error('Error al actualizar ITO. Por favor, inténtalo de nuevo.', {
                                            autoHide: 0,
                                            dismissible: true
                                        });
                                    }
                                }).catch(() => {
                                    Alert.error('Error al actualizar ITO. Por favor, inténtalo de nuevo.', {
                                        autoHide: 0,
                                        dismissible: true
                                    });
                                });
                            } else {
                                Alert.error('Error al actualizar ITO. Por favor, inténtalo de nuevo.', {
                                    autoHide: 0,
                                    dismissible: true
                                });
                            }
                        });
                    }
                });

                // Evento para perder foco del select
                registrosTable.addEventListener('blur', function(e) {
                    if (e.target.classList.contains('ito-select')) {
                        const cell = e.target.closest('td');
                        const textSpan = cell.querySelector('.ito-text');
                        const select = e.target;
                        
                        setTimeout(() => {
                            select.style.display = 'none';
                            textSpan.style.display = 'inline';
                        }, 200);
                    }
                }, true);
            }
        }

        // Cargar usuarios ITO y luego inicializar la tabla
        fetch('/txtss/api/v1/registros/usuarios_ito/')
            .then(response => response.json())
            .then(data => {
                usuariosIto = data;
                initializeTable();
            })
            .catch(error => {
                console.error('Error cargando usuarios ITO:', error);
                // Inicializar tabla incluso si falla la carga de usuarios ITO
                initializeTable();
            });
    }

    // Activar el modal
    const modal = document.getElementById("activar-registro-modal");
    const activarBtn = document.getElementById("activar-registro-btn");

    if (activarBtn && modal) {
        activarBtn.addEventListener("click", function () {
            console.log("activarBtn");
            
            modal.showModal();
        });
    }

    window.closeModal = function () {
        modal.close();
    };

    const activarRegistroBtn = document.getElementById("activar-registro-btn");
    if (activarRegistroBtn) {
        activarRegistroBtn.addEventListener("click", function () {
            console.log("activarRegistroBtn");
        });
    }

    // Activar el registro
    // Interceptar el submit del formulario
    const form = document.querySelector('#activar-registro-modal form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            
            // Verificar que los campos requeridos estén presentes
            const sitio = formData.get('sitio');
            const user = formData.get('user');
            
            if (!sitio || !user) {
                Alert.error('Por favor completa todos los campos requeridos.', {
                    autoHide: 3000,
                    dismissible: true
                });
                return;
            }

            // Obtener el token CSRF
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            // Hacer la petición POST al formulario
            fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('Error en la petición');
                }
            })
            .then(data => {
                console.log('Respuesta del servidor:', data);
                
                if (data.success) {
                    // Cerrar el modal
                    modal.close();
                    
                    Alert.success(data.message || 'Registro activado exitosamente', {
                        autoHide: 3000
                    });
                    
                    // Recargar la página después de un breve delay para que se vea la alerta
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    throw new Error(data.message || 'Error al activar el registro');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Intentar obtener el mensaje de error del servidor
                if (error.response) {
                    error.response.json().then(data => {
                        if (data.errors && data.errors.non_field_errors) {
                            Alert.error(data.errors.non_field_errors[0], {
                                autoHide: 0,
                                dismissible: true
                            });
                        } else if (data.message) {
                            Alert.error(data.message, {
                                autoHide: 0,
                                dismissible: true
                            });
                        } else {
                            Alert.error('Error al crear el registro. Por favor, inténtalo de nuevo.', {
                                autoHide: 0,
                                dismissible: true
                            });
                        }
                    }).catch(() => {
                        Alert.error('Error al crear el registro. Por favor, inténtalo de nuevo.', {
                            autoHide: 0,
                            dismissible: true
                        });
                    });
                } else {
                    Alert.error('Error al crear el registro. Por favor, inténtalo de nuevo.', {
                        autoHide: 0,
                        dismissible: true
                    });
                }
            });
        });
    }
});
