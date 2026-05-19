"""
Componente combinado para manejar formularios y tablas editables en un solo elemento.
"""

from typing import Dict, Any, Optional, List
from django.shortcuts import render
from django.http import JsonResponse
from registros.components.base import ElementoRegistro
from registros.components.form_element import FormElement
from registros.components.table_element import TableElement
from registros.components.registro_config import ElementoConfig


class CombinedElement(ElementoRegistro):
    """
    Elemento que combina formularios y tablas editables.
    Mantiene la separación de responsabilidades entre ambos tipos de elementos.
    """
    
    def __init__(self, registro, elemento_config: ElementoConfig, instance=None):
        self.elemento_config = elemento_config
        self.registro = registro
        self.instance = instance
        
        # Crear elementos especializados
        self.form_element = None
        self.table_elements = []
        
        # Inicializar formulario si hay modelo o form_class
        if elemento_config.model or elemento_config.form_class:
            self.form_element = FormElement(registro, elemento_config, instance)
        
        # Inicializar tablas editables si hay sub_elementos de tipo editable_table
        for sub_elemento in elemento_config.sub_elementos:
            if sub_elemento.tipo == 'editable_table':
                table_element = TableElement(registro, sub_elemento.config)
                self.table_elements.append(table_element)
    
    def get_form(self, data=None, files=None):
        """Obtiene el formulario del elemento de formulario."""
        if self.form_element:
            return self.form_element.get_form(data, files)
        return None
    
    def save(self, form):
        """Guarda el formulario usando el elemento de formulario."""
        if self.form_element:
            return self.form_element.save(form)
        return None
    
    def get_or_create(self):
        """Obtiene o crea la instancia usando el elemento de formulario."""
        if self.form_element:
            return self.form_element.get_or_create()
        return None
    
    def get_completeness_info(self):
        """Obtiene información de completitud combinada."""
        completeness_info = {
            'color': 'gray',
            'is_complete': False,
            'total_components': 0,
            'complete_components': 0,
            'components': {}
        }
        
        total_components = 0
        complete_components = 0
        
        # Verificar completitud del formulario
        if self.form_element:
            total_components += 1
            form_completeness = self.form_element.get_completeness_info()
            completeness_info['components']['form'] = form_completeness
            
            if form_completeness['is_complete']:
                complete_components += 1
        
        # Verificar completitud de las tablas
        for i, table_element in enumerate(self.table_elements):
            total_components += 1
            table_completeness = table_element.get_completeness_info()
            completeness_info['components'][f'table_{i}'] = table_completeness
            
            if table_completeness['is_complete']:
                complete_components += 1
        
        # Calcular completitud general
        completeness_info['total_components'] = total_components
        completeness_info['complete_components'] = complete_components
        completeness_info['is_complete'] = complete_components == total_components and total_components > 0
        
        # Determinar color general
        if total_components == 0:
            completeness_info['color'] = 'gray'
        elif complete_components == 0:
            completeness_info['color'] = 'error'
        elif complete_components < total_components:
            completeness_info['color'] = 'warning'
        else:
            completeness_info['color'] = 'success'
        
        return completeness_info
    
    def get_context_data(self):
        """Obtiene el contexto combinado para renderizar."""
        context = {
            'title': self.elemento_config.title,
            'description': self.elemento_config.description,
            'success_message': self.elemento_config.success_message,
            'error_message': self.elemento_config.error_message,
            'sub_elementos': self.elemento_config.sub_elementos,
        }
        
        # Agregar contexto del formulario
        if self.form_element:
            form_context = self.form_element.get_context_data()
            context.update({
                'form': form_context['form'],
                'instance': form_context['instance'],
                'form_completeness': form_context['completeness'],
            })
        
        # Agregar contexto de las tablas
        if self.table_elements:
            context['table_elements'] = []
            for table_element in self.table_elements:
                table_context = table_element.get_context_data()
                table_context['completeness'] = table_element.get_completeness_info()
                context['table_elements'].append(table_context)
        
        # Agregar completitud general
        context['completeness'] = self.get_completeness_info()
        
        return context
    
    def render(self, request):
        """Renderiza el elemento combinado."""
        context = self.get_context_data()
        
        # Determinar el template apropiado
        template_name = self.elemento_config.template_name
        
        # Si es solo tabla editable, usar template específico
        if not self.form_element and self.table_elements:
            template_name = 'components/table_only.html'
        
        return render(request, template_name, context)
    
    def handle_form_submission(self, request):
        """Maneja el envío del formulario."""
        if not self.form_element:
            return {'success': False, 'error': 'No hay formulario configurado'}
        
        return self.form_element.handle_form_submission(request)
    
    def get_table_data(self, request, table_index=0):
        """Obtiene los datos de una tabla específica."""
        if table_index < len(self.table_elements):
            return self.table_elements[table_index].get_data(request)
        return JsonResponse({'error': 'Tabla no encontrada'}, status=404)
    
    def create_table_record(self, request, table_index=0):
        """Crea un registro en una tabla específica."""
        if table_index < len(self.table_elements):
            return self.table_elements[table_index].create_record(request)
        return JsonResponse({'error': 'Tabla no encontrada'}, status=404)
    
    def update_table_record(self, request, pk, table_index=0):
        """Actualiza un registro en una tabla específica."""
        if table_index < len(self.table_elements):
            return self.table_elements[table_index].update_record(request, pk)
        return JsonResponse({'error': 'Tabla no encontrada'}, status=404)
    
    def delete_table_record(self, request, pk, table_index=0):
        """Elimina un registro en una tabla específica."""
        if table_index < len(self.table_elements):
            return self.table_elements[table_index].delete_record(request, pk)
        return JsonResponse({'error': 'Tabla no encontrada'}, status=404)
    
    def has_form(self):
        """Verifica si el elemento tiene formulario."""
        return self.form_element is not None
    
    def has_tables(self):
        """Verifica si el elemento tiene tablas editables."""
        return len(self.table_elements) > 0
    
    def is_form_only(self):
        """Verifica si el elemento es solo formulario."""
        return self.has_form() and not self.has_tables()
    
    def is_table_only(self):
        """Verifica si el elemento es solo tabla editable."""
        return not self.has_form() and self.has_tables()
    
    def is_combined(self):
        """Verifica si el elemento combina formulario y tablas."""
        return self.has_form() and self.has_tables() 