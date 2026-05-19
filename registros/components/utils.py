from django.http import JsonResponse
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect


def handle_elemento_ajax_request(request, elemento, success_url=None):
    """
    Maneja una petición AJAX para un elemento.
    
    Args:
        request: HttpRequest
        elemento: Instancia del elemento
        success_url: URL de redirección en caso de éxito
        
    Returns:
        JsonResponse: Respuesta JSON
    """
    try:
        result = elemento.handle_form_submission(request)
        
        if result['success'] is True:
            response_data = {
                'success': True,
                'message': elemento.success_message,
                'redirect_url': success_url,
                'object_id': result['object'].id if result['object'] else None,
            }
            return JsonResponse(response_data)
        elif result['success'] is False:
            response_data = {
                'success': False,
                'message': elemento.error_message,
                'errors': result.get('errors', []),
            }
            return JsonResponse(response_data, status=400)
        else:
            # GET request
            response_data = {
                'success': None,
                'form_html': render_form_to_html(result['form']),
            }
            return JsonResponse(response_data)
            
    except Exception as e:
        response_data = {
            'success': False,
            'message': f"Error inesperado: {str(e)}",
        }
        return JsonResponse(response_data, status=500)


def handle_elemento_form_request(request, elemento, success_url=None, template_context=None):
    """
    Maneja una petición de formulario normal para un elemento.
    
    Args:
        request: HttpRequest
        elemento: Instancia del elemento
        success_url: URL de redirección en caso de éxito
        template_context: Contexto adicional para el template
        
    Returns:
        HttpResponse: Respuesta HTTP
    """
    try:
        result = elemento.handle_form_submission(request)
        
        if result['success'] is True:
            if success_url:
                return redirect(success_url)
            else:
                messages.success(request, elemento.success_message)
                return redirect(request.path)
        elif result['success'] is False:
            # El formulario tiene errores, se renderiza de nuevo
            context = {
                'form': result['form'],
                'elemento': elemento,
                'registro': elemento.registro,
            }
            if template_context:
                context.update(template_context)
            
            return elemento.render_template(request, context)
        else:
            # GET request
            context = {
                'form': result['form'],
                'elemento': elemento,
                'registro': elemento.registro,
            }
            if template_context:
                context.update(template_context)
            
            return elemento.render_template(request, context)
            
    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")
        return redirect(request.path)


def render_form_to_html(form):
    """
    Renderiza un formulario a HTML.
    
    Args:
        form: Formulario Django
        
    Returns:
        str: HTML del formulario
    """
    try:
        from crispy_forms.utils import render_crispy_form
        return render_crispy_form(form)
    except ImportError:
        # Fallback si crispy_forms no está disponible
        return form.as_p()


def get_elemento_status(elemento):
    """
    Obtiene el estado de completitud de un elemento.
    
    Args:
        elemento: Instancia del elemento
        
    Returns:
        dict: Información del estado
    """
    if not elemento.instance:
        return {
            'status': 'empty',
            'color': 'gray',
            'message': 'Sin datos',
            'completeness': 0,
        }
    
    completeness_info = elemento.get_completeness_info()
    if completeness_info:
        return {
            'status': 'complete' if completeness_info['is_complete'] else 'incomplete',
            'color': completeness_info['color'],
            'message': f"{completeness_info['filled_fields']}/{completeness_info['total_fields']} campos completados",
            'completeness': (completeness_info['filled_fields'] / completeness_info['total_fields']) * 100,
        }
    
    return {
        'status': 'unknown',
        'color': 'gray',
        'message': 'Estado desconocido',
        'completeness': 0,
    }


def validate_elemento_data(data, elemento):
    """
    Valida los datos de un elemento.
    
    Args:
        data: Datos a validar
        elemento: Instancia del elemento
        
    Returns:
        tuple: (is_valid, errors)
    """
    try:
        form = elemento.get_form(data=data)
        if form:
            return form.is_valid(), form.errors
        return True, {}
    except Exception as e:
        return False, {'general': [str(e)]}


def get_elemento_summary(elemento):
    """
    Obtiene un resumen de la información del elemento.
    
    Args:
        elemento: Instancia del elemento
        
    Returns:
        dict: Resumen del elemento
    """
    if not elemento.instance:
        return {
            'has_data': False,
            'summary': 'Sin datos',
            'last_updated': None,
        }
    
    # Obtener información específica según el tipo de elemento
    if hasattr(elemento, 'get_empalme_info'):
        info = elemento.get_empalme_info()
        summary = f"Empalme: {info['proveedor']} - {info['capacidad']}" if info else "Sin datos"
    elif hasattr(elemento, 'get_acceso_info'):
        info = elemento.get_acceso_info()
        summary = f"Acceso: {info['tipo_suelo']}" if info else "Sin datos"
    elif hasattr(elemento, 'get_sitio_info'):
        info = elemento.get_sitio_info()
        summary = f"Sitio: {info['altura']} - {info['dimensiones']}" if info else "Sin datos"
    elif hasattr(elemento, 'get_mapas_info'):
        info = elemento.get_mapas_info()
        summary = f"Mapa: {info['etapa']}" if info else "Sin datos"
    else:
        summary = "Datos disponibles"
    
    return {
        'has_data': True,
        'summary': summary,
        'last_updated': elemento.instance.updated_at if hasattr(elemento.instance, 'updated_at') else None,
    } 