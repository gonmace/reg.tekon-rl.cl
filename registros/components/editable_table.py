"""
Componente para manejar tablas editables.
"""

from typing import Dict, Any, List
from django.shortcuts import render
from django.http import JsonResponse
from registros.components.base import ElementoRegistro


class EditableTableElemento(ElementoRegistro):
    """
    Elemento para manejar tablas editables con AJAX.
    """
    
    def __init__(self, registro, table_config: Dict[str, Any]):
        self.table_config = table_config
        self.model_class = table_config.get('model_class')
        self.columns = table_config.get('columns', [])
        self.api_url = table_config.get('api_url', '')
        self.allow_create = table_config.get('allow_create', True)
        self.allow_edit = table_config.get('allow_edit', True)
        self.allow_delete = table_config.get('allow_delete', True)
        self.page_length = table_config.get('page_length', 10)
        self.title = table_config.get('title', 'Tabla Editable')
        self.description = table_config.get('description', '')
        self.template_name = table_config.get('template_name', 'components/editable_table.html')
        
        super().__init__(registro)
    
    def get_context_data(self):
        """Obtiene el contexto para renderizar la tabla."""
        return {
            'title': self.title,
            'description': self.description,
            'columns': self.columns,
            'api_url': self.api_url,
            'allow_create': self.allow_create,
            'allow_edit': self.allow_edit,
            'allow_delete': self.allow_delete,
            'page_length': self.page_length,
        }
    
    def render(self, request):
        """Renderiza la tabla editable."""
        context = self.get_context_data()
        return render(request, self.template_name, context)
    
    def get_data(self, request):
        """Obtiene los datos de la tabla."""
        if not self.model_class:
            return JsonResponse({'error': 'Modelo no configurado'}, status=400)
        
        try:
            # Obtener datos del modelo
            queryset = self.model_class.objects.filter(is_deleted=False)
            
            # Filtrar por usuario si no es superusuario ni ITO/Buscador/Visita
            if not request.user.is_superuser and not request.user.is_visita:
                if hasattr(self.model_class, 'user'):
                    queryset = queryset.filter(user=request.user)
                elif hasattr(self.model_class, 'registro'):
                    queryset = queryset.filter(registro__user=request.user)
            
            # Serializar datos
            data = []
            for obj in queryset:
                row_data = {'id': obj.id}
                for column in self.columns:
                    key = column['key']
                    if hasattr(obj, key):
                        value = getattr(obj, key)
                        # Manejar relaciones
                        if hasattr(value, 'id'):
                            row_data[key] = value.id
                        elif hasattr(value, '__call__'):
                            row_data[key] = value()
                        else:
                            row_data[key] = value
                    else:
                        row_data[key] = None
                data.append(row_data)
            
            return JsonResponse(data, safe=False)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def create_record(self, request):
        """Crea un nuevo registro."""
        if not self.model_class:
            return JsonResponse({'error': 'Modelo no configurado'}, status=400)
        
        try:
            import json
            data = json.loads(request.body.decode('utf-8'))
            
            # Preparar datos para crear objeto
            obj_data = {}
            for column in self.columns:
                key = column['key']
                if key in data and data[key] is not None and data[key] != '':
                    obj_data[key] = data[key]
            
            # Agregar usuario si el modelo lo requiere
            if hasattr(self.model_class, 'user'):
                obj_data['user'] = request.user
            
            # Crear objeto
            obj = self.model_class.objects.create(**obj_data)
            
            # Serializar respuesta
            response_data = {'id': obj.id}
            for column in self.columns:
                key = column['key']
                if hasattr(obj, key):
                    value = getattr(obj, key)
                    if hasattr(value, '__call__'):
                        response_data[key] = value()
                    else:
                        response_data[key] = value
                else:
                    response_data[key] = None
            
            return JsonResponse(response_data, status=201)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    def update_record(self, request, pk):
        """Actualiza un registro."""
        if not self.model_class:
            return JsonResponse({'error': 'Modelo no configurado'}, status=400)
        
        try:
            from django.shortcuts import get_object_or_404
            import json
            
            # Obtener objeto
            obj = get_object_or_404(self.model_class, id=pk)
            
            # Verificar permisos
            if not request.user.is_superuser:
                if hasattr(obj, 'user') and obj.user != request.user:
                    return JsonResponse({'error': 'No tiene permisos'}, status=403)
                elif hasattr(obj, 'registro') and obj.registro.user != request.user:
                    return JsonResponse({'error': 'No tiene permisos'}, status=403)
            
            # Parsear datos JSON
            data = json.loads(request.body.decode('utf-8'))
            
            # Actualizar campos
            for column in self.columns:
                key = column['key']
                if key in data:
                    setattr(obj, key, data[key])
            
            obj.save()
            
            # Serializar respuesta
            response_data = {'id': obj.id}
            for column in self.columns:
                key = column['key']
                if hasattr(obj, key):
                    value = getattr(obj, key)
                    if hasattr(value, '__call__'):
                        response_data[key] = value()
                    else:
                        response_data[key] = value
                else:
                    response_data[key] = None
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    def delete_record(self, request, pk):
        """Elimina un registro."""
        if not self.model_class:
            return JsonResponse({'error': 'Modelo no configurado'}, status=400)
        
        try:
            from django.shortcuts import get_object_or_404
            
            # Obtener objeto
            obj = get_object_or_404(self.model_class, id=pk)
            
            # Verificar permisos
            if not request.user.is_superuser:
                if hasattr(obj, 'user') and obj.user != request.user:
                    return JsonResponse({'error': 'No tiene permisos'}, status=403)
                elif hasattr(obj, 'registro') and obj.registro.user != request.user:
                    return JsonResponse({'error': 'No tiene permisos'}, status=403)
            
            # Soft delete si el modelo lo soporta
            if hasattr(obj, 'is_deleted'):
                obj.is_deleted = True
                obj.save()
            else:
                obj.delete()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400) 