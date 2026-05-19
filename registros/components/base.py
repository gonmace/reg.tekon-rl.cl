from django.shortcuts import render
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction


class ElementoRegistro:
    """
    Clase base para elementos de registro que se reutilizarán en las aplicaciones.
    Cada elemento es un formulario asociado a un modelo específico y puede tener sub-elementos.
    """
    model = None              # Modelo asociado al elemento
    form_class = None         # Formulario asociado al elemento
    template_name = None      # Template a renderizar
    tipo = 'form'            # Tipo de elemento (por defecto es 'form')
    success_message = "Elemento guardado exitosamente."
    error_message = "Error al guardar el elemento."
    sub_elementos = {}        # Diccionario de sub-elementos (fotos, mapas, etc.)

    def __init__(self, registro, instance=None):
        self.registro = registro
        self.instance = instance
        self.sub_elementos_instancias = {}

    def get_queryset(self):
        """Obtiene el queryset filtrado por registro."""
        if self.model:
            return self.model.objects.filter(registro=self.registro)
        return None

    def get_form(self, data=None, files=None):
        """Obtiene una instancia del formulario con los datos proporcionados."""
        if not self.form_class:
            return None
            
        if self.instance:
            return self.form_class(data=data, files=files, instance=self.instance)
        else:
            return self.form_class(data=data, files=files, registro_id=self.registro.id)

    def save(self, form):
        """Guarda el formulario y asocia el registro."""
        try:
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.registro = self.registro
                obj.save()
                return obj
        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(f"Error al guardar: {str(e)}")

    def delete(self, instance):
        """Elimina una instancia del modelo."""
        try:
            with transaction.atomic():
                instance.delete()
                return True
        except Exception as e:
            raise ValidationError(f"Error al eliminar: {str(e)}")

    def get_or_create(self):
        """Obtiene la instancia existente o crea una nueva."""
        try:
            queryset = self.get_queryset()
            if queryset:
                return queryset.first()
        except Exception:
            pass
        return None

    def get_sub_elemento(self, tipo_sub_elemento):
        """Obtiene un sub-elemento específico."""
        if tipo_sub_elemento not in self.sub_elementos:
            return None
            
        if tipo_sub_elemento not in self.sub_elementos_instancias:
            sub_elemento_class = self.sub_elementos[tipo_sub_elemento]
            self.sub_elementos_instancias[tipo_sub_elemento] = sub_elemento_class(self)
            
        return self.sub_elementos_instancias[tipo_sub_elemento]

    def get_all_sub_elementos(self):
        """Obtiene todos los sub-elementos."""
        sub_elementos = {}
        for tipo in self.sub_elementos.keys():
            sub_elementos[tipo] = self.get_sub_elemento(tipo)
        return sub_elementos

    def render_template(self, request, context=None):
        """Renderiza el template con el contexto proporcionado."""
        if context is None:
            context = {}
        
        context.update({
            'registro': self.registro,
            'tipo': self.tipo,
            'instance': self.instance,
            'elemento': self,
            'sub_elementos': self.get_all_sub_elementos(),
        })
        
        return render(request, self.template_name, context)

    def handle_form_submission(self, request):
        """Maneja el envío del formulario."""
        if request.method == 'POST':
            form = self.get_form(data=request.POST, files=request.FILES)
            if form and form.is_valid():
                try:
                    obj = self.save(form)
                    messages.success(request, self.success_message)
                    return {'success': True, 'object': obj}
                except ValidationError as e:
                    messages.error(request, str(e))
                    return {'success': False, 'errors': e.messages}
            else:
                messages.error(request, self.error_message)
                return {'success': False, 'form': form}
        else:
            form = self.get_form()
            return {'success': None, 'form': form}

    def get_completeness_info(self, instance_id=None):
        """Obtiene información sobre la completitud del elemento."""
        if hasattr(self, 'model') and hasattr(self.model, 'check_completeness'):
            if instance_id:
                return self.model.check_completeness(instance_id)
            elif self.instance:
                return self.model.check_completeness(self.instance.id)
        return None

    def get_tipo(self):
        """Obtiene el tipo del elemento."""
        return self.tipo

    def to_dict(self):
        """Convierte el elemento a diccionario para serialización."""
        return {
            'tipo': self.get_tipo(),
            'model': self.model.__name__ if self.model else None,
            'registro_id': self.registro.id if self.registro else None,
            'instance_id': self.instance.id if self.instance else None,
            'sub_elementos': list(self.sub_elementos.keys()),
        } 