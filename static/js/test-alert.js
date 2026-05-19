/**
 * Script de prueba para el componente Alert
 * Para probar que el botón de cerrar (X) funciona correctamente
 */

// Función para probar las alertas
function testAlerts() {
    console.log('Probando componente Alert...');
    
    // Verificar que el componente esté disponible
    if (!window.Alert) {
        console.error('Alert component not available!');
        return;
    }
    
    // Probar alerta de éxito
    const successId = window.Alert.success('Esta es una alerta de éxito de prueba', {
        autoHide: 0  // No auto-ocultar para poder probar el botón X
    });
    console.log('Success alert created with ID:', successId);
    
    // Probar alerta de error
    const errorId = window.Alert.error('Esta es una alerta de error de prueba', {
        autoHide: 0
    });
    console.log('Error alert created with ID:', errorId);
    
    // Probar alerta de advertencia
    const warningId = window.Alert.warning('Esta es una alerta de advertencia de prueba', {
        autoHide: 0
    });
    console.log('Warning alert created with ID:', warningId);
    
    // Probar alerta informativa
    const infoId = window.Alert.info('Esta es una alerta informativa de prueba', {
        autoHide: 0
    });
    console.log('Info alert created with ID:', infoId);
    
    console.log('Alertas de prueba creadas. Prueba hacer clic en las X para cerrarlas.');
    console.log('Revisa la consola para ver los logs de debugging.');
}

// Función para probar confirmación
function testConfirm() {
    if (!window.Alert) {
        console.error('Alert component not available!');
        return;
    }
    
    window.Alert.confirm(
        '¿Estás seguro de que quieres realizar esta acción?',
        () => {
            console.log('Usuario confirmó la acción');
            window.Alert.success('Acción confirmada');
        },
        () => {
            console.log('Usuario canceló la acción');
            window.Alert.info('Acción cancelada');
        },
        {
            title: 'Confirmar Acción',
            confirmText: 'Sí, continuar',
            cancelText: 'No, cancelar'
        }
    );
}

// Función para probar manualmente el botón de cerrar
function testCloseButton() {
    if (!window.Alert) {
        console.error('Alert component not available!');
        return;
    }
    
    const testId = window.Alert.error('Prueba manual del botón de cerrar', {
        autoHide: 0
    });
    
    console.log('Test alert created with ID:', testId);
    
    // Buscar el botón de cerrar manualmente
    setTimeout(() => {
        const closeBtn = document.querySelector(`[data-alert-id="${testId}"]`);
        if (closeBtn) {
            console.log('Close button found:', closeBtn);
            console.log('Close button HTML:', closeBtn.outerHTML);
            
            // Simular clic programáticamente
            closeBtn.click();
        } else {
            console.error('Close button not found for ID:', testId);
        }
    }, 100);
}

// Función para inspeccionar alertas actuales
function inspectAlerts() {
    const alertsContainer = document.getElementById('alerts-container');
    if (alertsContainer) {
        console.log('Alerts container found:', alertsContainer);
        const alerts = alertsContainer.querySelectorAll('[id^="alert-"]');
        console.log('Current alerts:', alerts.length);
        alerts.forEach((alert, index) => {
            console.log(`Alert ${index + 1}:`, {
                id: alert.id,
                html: alert.outerHTML,
                closeBtn: alert.querySelector('.alert-close-btn')
            });
        });
    } else {
        console.error('Alerts container not found');
    }
}

// Agregar botones de prueba al DOM cuando esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Crear botones de prueba
    const testContainer = document.createElement('div');
    testContainer.style.cssText = 'position: fixed; top: 10px; left: 10px; z-index: 10000; background: white; padding: 10px; border: 1px solid #ccc; border-radius: 5px; max-width: 300px;';
    testContainer.innerHTML = `
        <h4 style="margin: 0 0 10px 0;">Prueba Alert Component</h4>
        <button onclick="testAlerts()" style="margin: 2px; padding: 5px 10px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; width: 100%;">Probar Alertas</button>
        <button onclick="testConfirm()" style="margin: 2px; padding: 5px 10px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer; width: 100%;">Probar Confirmación</button>
        <button onclick="testCloseButton()" style="margin: 2px; padding: 5px 10px; background: #ffc107; color: black; border: none; border-radius: 3px; cursor: pointer; width: 100%;">Probar Botón Cerrar</button>
        <button onclick="inspectAlerts()" style="margin: 2px; padding: 5px 10px; background: #6c757d; color: white; border: none; border-radius: 3px; cursor: pointer; width: 100%;">Inspeccionar Alertas</button>
        <button onclick="window.Alert.hideAll()" style="margin: 2px; padding: 5px 10px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; width: 100%;">Cerrar Todas</button>
    `;
    
    document.body.appendChild(testContainer);
    
    console.log('Botones de prueba agregados. Puedes probar el componente Alert ahora.');
    console.log('Revisa la consola del navegador para ver los logs de debugging.');
});

// Hacer las funciones disponibles globalmente
window.testAlerts = testAlerts;
window.testConfirm = testConfirm;
window.testCloseButton = testCloseButton;
window.inspectAlerts = inspectAlerts;
