"""
Comando para crear una nueva aplicación de registros completa.

Este comando genera aplicaciones que usan el sistema genérico de registros,
incluyendo:
- Templates genéricos (main_generic.html, steps_generic.html)
- URLs consistentes con paso_nombre
- Vistas genéricas con header_title mejorado
- Configuración declarativa completa
- Sistema de breadcrumbs dinámico
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings
import os
import re
from pathlib import Path

class Command(BaseCommand):
    help = 'Crea una nueva aplicación de registros completa usando el sistema genérico (templates genéricos, URLs consistentes, vistas mejoradas)'

    def add_arguments(self, parser):
        parser.add_argument(
            'app_name',
            type=str,
            help='Nombre de la aplicación (ej: reg_instalacion, reg_mantenimiento)'
        )
        parser.add_argument(
            '--title',
            type=str,
            help='Título de la aplicación (ej: "Instalación", "Mantenimiento")'
        )
        parser.add_argument(
            '--description',
            type=str,
            help='Descripción de la aplicación'
        )
        parser.add_argument(
            '--pasos',
            nargs='+',
            default=['paso1', 'paso2', 'paso3'],
            help='Lista de pasos para el registro (ej: sitio acceso empalme)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la creación aunque la aplicación ya exista'
        )
        parser.add_argument(
            '--allow-multiple-per-site',
            action='store_true',
            default=False,
            help='Permitir múltiples registros por sitio (uno por día)'
        )

    def handle(self, *args, **options):
        app_name = options['app_name']
        title = options['title'] or app_name.replace('reg_', '').title()
        description = options['description'] or f'Aplicación para registros de {title.lower()}'
        pasos = options['pasos']
        force = options['force']
        allow_multiple_per_site = options['allow_multiple_per_site']

        # Validar nombre de aplicación
        if not re.match(r'^[a-z][a-z0-9_]*$', app_name):
            raise CommandError('El nombre de la aplicación debe ser en minúsculas y solo puede contener letras, números y guiones bajos')

        # Verificar si la aplicación ya existe
        app_path = Path(settings.BASE_DIR) / app_name
        if app_path.exists() and not force:
            raise CommandError(f'La aplicación "{app_name}" ya existe. Usa --force para sobrescribir.')

        self.stdout.write(f'Creando aplicación "{app_name}"...')

        # Crear la aplicación Django manualmente
        if app_path.exists() and not force:
            raise CommandError(f'La aplicación "{app_name}" ya existe. Usa --force para sobrescribir.')
        
        if app_path.exists() and force:
            import shutil
            shutil.rmtree(app_path)
        
        # Crear estructura de directorios
        app_path.mkdir(exist_ok=True)
        (app_path / 'migrations').mkdir(exist_ok=True)
        (app_path / 'templates').mkdir(exist_ok=True)
        (app_path / 'templates' / app_name).mkdir(exist_ok=True)
        (app_path / 'templates' / app_name / 'partials').mkdir(exist_ok=True)
        
        # Crear archivos __init__.py
        (app_path / '__init__.py').touch()
        (app_path / 'migrations' / '__init__.py').touch()

        # Crear estructura de archivos
        self._create_app_structure(app_name, title, description, pasos)
        
        # Crear templates
        self._create_templates(app_name, title, pasos)
        
        # Crear archivos de configuración
        self._create_config_files(app_name, title, pasos, allow_multiple_per_site)
        
        # Crear archivos de vistas
        self._create_views(app_name, title, pasos)
        
        # Crear archivos de formularios
        self._create_forms(app_name, pasos)
        
        # Crear archivos de modelos
        self._create_models(app_name, title, pasos)
        
        # Crear archivos de admin
        self._create_admin(app_name, pasos)
        
        # Crear archivos de URLs
        self._create_urls(app_name, title)
        
                # Crear archivos de apps.py
        self._create_apps_py(app_name, title, description)
        
        # Crear archivo de configuración de ejemplo
        self._create_setup_example(app_name, title)
        
        # Crear configuración de PDF
        self._create_pdf_configuration(app_name, title, pasos)
        
        # Crear vistas de PDF específicas
        self._create_pdf_views(app_name, title, pasos)

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Aplicación "{app_name}" creada exitosamente!\n'
                f'✓ Título: {title}\n'
                f'✓ Pasos: {", ".join(pasos)}\n'
                f'✓ No olvides completar la configuración manual:'
            )
        )
        
        # Mostrar pasos de configuración manual
        self.stdout.write(
            self.style.WARNING(
                '\n📋 PASOS DE CONFIGURACIÓN MANUAL:\n'
                '1. Agregar "{app_name}" a INSTALLED_APPS en config/base.py\n'
                '2. Agregar URL en config/urls.py: path("{app_name}/", include("{app_name}.urls"))\n'
                '3. Agregar al menú en core/menu/menu_builder.py\n'
                '4. Ejecutar: python manage.py makemigrations {app_name}\n'
                '5. Ejecutar: python manage.py migrate\n'
                '6. Crear superusuario si no existe: python manage.py createsuperuser\n'
                '7. ✅ PDF automático: Templates y vistas generados automáticamente\n'
            )
        )

    def _create_app_structure(self, app_name, title, description, pasos):
        """Crear estructura de directorios y archivos base"""
        app_path = Path(settings.BASE_DIR) / app_name
        
        # Crear directorios adicionales
        (app_path / 'templates' / app_name).mkdir(parents=True, exist_ok=True)
        (app_path / 'templates' / app_name / 'partials').mkdir(parents=True, exist_ok=True)

    def _create_templates(self, app_name, title, pasos):
        """Crear templates HTML"""
        app_path = Path(settings.BASE_DIR) / app_name
        templates_path = app_path / 'templates' / app_name

        # Template principal de listado
        list_template = f'''{{% extends "base.html" %}}
{{% load static %}}

{{% block title %}}{title}{{% endblock %}}

{{% block content %}}
<div class="container mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold text-gray-900">{title}</h1>
        <a href="{{% url '{app_name}:activar' %}}" class="btn btn-primary">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            Nuevo Registro
        </a>
    </div>

    <div class="bg-white shadow-md rounded-lg overflow-hidden">
        <div class="p-6">
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                ID
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Título
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Sitio
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Usuario
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Fecha
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Acciones
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        {{% for registro in registros %}}
                        <tr>
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {{ registro.id }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {{ registro.title }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {{ registro.sitio.name|default:"Sin sitio" }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {{ registro.user.username|default:"Sin usuario" }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {{ registro.created_at|date:"d/m/Y" }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                <a href="{{% url '{app_name}:steps' registro.id %}}" class="text-indigo-600 hover:text-indigo-900">
                                    Ver Pasos
                                </a>
                            </td>
                        </tr>
                        {{% endfor %}}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{{% endblock %}}'''

        with open(templates_path / 'list.html', 'w', encoding='utf-8') as f:
            f.write(list_template)

        # Template de pasos
        steps_template = f'''{{% extends "base.html" %}}
{{% load static %}}

{{% block title %}}{title} - Pasos{{% endblock %}}

{{% block content %}}
<div class="container mx-auto px-4 py-8">
    <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">{title}</h1>
        <p class="text-gray-600">Registro #{{ registro.id }}</p>
    </div>

    <div class="bg-white shadow-md rounded-lg overflow-hidden">
        <div class="border-b border-gray-200">
            <nav class="-mb-px flex space-x-8 px-6">
                {{% for paso in pasos %}}
                <a href="?paso={{ paso.nombre }}" 
                   class="py-4 px-1 border-b-2 font-medium text-sm {{% if paso.activo %}}border-indigo-500 text-indigo-600{{% else %}}border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300{{% endif %}}">
                    {{ paso.titulo }}
                </a>
                {{% endfor %}}
            </nav>
        </div>

        <div class="p-6">
            {{% block paso_content %}}
            <p class="text-gray-500">Selecciona un paso para comenzar.</p>
            {{% endblock %}}
        </div>
    </div>
</div>
{{% endblock %}}'''

        with open(templates_path / 'steps.html', 'w', encoding='utf-8') as f:
            f.write(steps_template)

    def _create_config_files(self, app_name, title, pasos, allow_multiple_per_site=False):
        """Crear archivos de configuración"""
        app_path = Path(settings.BASE_DIR) / app_name

        # Configuración principal
        config_content = f'''"""
Configuración declarativa para registros {title}.
"""

from registros.config import (
    create_simple_config, 
    create_registro_config,
    create_1_point_map_config,
    create_2_point_map_config,
    create_3_point_map_config,
    create_photos_config,
    create_custom_config,
    create_sub_element_only_config
)
from .models import {app_name.title().replace('_', '')}, {', '.join([paso.title() for paso in pasos])}
from .forms import {', '.join([f'{paso.title()}Form' for paso in pasos])}
from core.models.sites import Site

# Configuración de pasos
PASOS_CONFIG = {{'''

        for i, paso in enumerate(pasos):
            config_content += f'''
    '{paso}': create_custom_config(
        model_class={paso.title()},
        form_class={paso.title()}Form,
        title='{paso.title()}',
        description='Información sobre {paso.lower()}.',
        template_form='components/elemento_form.html'
    ),'''

        config_content += f'''
}}

# Configuración completa del registro
REGISTRO_CONFIG = create_registro_config(
    registro_model={app_name.title().replace('_', '')},
    pasos_config=PASOS_CONFIG,
    title='{title}',
    app_namespace='{app_name}',
    list_template='pages/main_generic.html',
    steps_template='pages/steps_generic.html',
    allow_multiple_per_site={str(allow_multiple_per_site).lower()}
)'''

        with open(app_path / 'config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)

    def _create_views(self, app_name, title, pasos):
        """Crear archivos de vistas"""
        app_path = Path(settings.BASE_DIR) / app_name

        # Importaciones para las vistas
        views_imports = f'''"""
Vistas para registros {title}.
"""

from registros.views.steps_views import (
    GenericRegistroStepsView,
    GenericElementoView,
    GenericRegistroTableListView
)
from registros.views.activation_views import GenericActivarRegistroView
from registros.config import RegistroConfig
from .config import REGISTRO_CONFIG
from django.shortcuts import get_object_or_404


class ListRegistrosView(GenericRegistroTableListView):
    """Vista para listar registros {title} usando tabla genérica."""
    
    def get_registro_config(self):
        return REGISTRO_CONFIG
    
    def get_breadcrumbs(self):
        """Genera breadcrumbs para la página de listado."""
        return [
            {{'label': 'Inicio', 'url': reverse('dashboard:dashboard')}},
            {{'label': '{title}'}}  # Página actual sin URL
        ]


class StepsRegistroView(GenericRegistroStepsView):
    """Vista para mostrar los pasos de un registro {title}."""
    
    def get_registro_config(self):
        return REGISTRO_CONFIG
    
    def get_context_data(self, **kwargs):
        """Obtiene el contexto y establece el registro."""
        registro_id = self.kwargs.get('registro_id')
        self.registro = get_object_or_404(self.registro_config.registro_model, id=registro_id)
        context = super().get_context_data(**kwargs)
        return context
    
    def get_header_title(self):
        """Obtiene el título del header basado en PTI ID o Operador ID."""
        if hasattr(self, 'registro') and self.registro:
            # Intentar obtener PTI ID primero
            pti_id = getattr(getattr(self.registro, 'sitio', None), 'pti_cell_id', None)
            if pti_id:
                return pti_id
            
            # Si no hay PTI ID, intentar Operador ID
            operador_id = getattr(getattr(self.registro, 'sitio', None), 'operator_id', None)
            if operador_id:
                return operador_id
        
        return super().get_header_title()
    
    def get_pdf_url(self, registro_id):
        """Obtiene la URL para generar el PDF del registro."""
        from django.urls import reverse
        return reverse('{app_name}:pdf', kwargs={{'registro_id': registro_id}})


class ElementoRegistroView(GenericElementoView):
    """Vista para manejar elementos de registro {title}."""
    
    def get_registro_config(self):
        return REGISTRO_CONFIG
    
    def get(self, request, registro_id, paso_nombre):
        """Establece el registro antes de procesar la petición."""
        self.registro = self.registro_config.registro_model.objects.get(id=registro_id)
        return super().get(request, registro_id, paso_nombre)
    
    def get_header_title(self):
        """Obtiene el título del header basado en el nombre del sitio."""
        if hasattr(self, 'registro') and self.registro:
            name = getattr(getattr(self.registro, 'sitio', None), 'name', 'Sin PTI')
            return name
        return super().get_header_title()


class ActivarRegistroView(GenericActivarRegistroView):
    """Vista para activar registros {title}."""
    
    def get_registro_config(self):
        return REGISTRO_CONFIG'''

        with open(app_path / 'views.py', 'w', encoding='utf-8') as f:
            f.write(views_imports)

    def _create_forms(self, app_name, pasos):
        """Crear archivos de formularios"""
        app_path = Path(settings.BASE_DIR) / app_name

        forms_content = f'''"""
Formularios para registros {app_name}.
"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Div
from .models import {app_name.title().replace('_', '')}, {', '.join([paso.title() for paso in pasos])}
from registros.forms.utils import get_form_field_css_class

'''

        for paso in pasos:
            forms_content += f'''
class {paso.title()}Form(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.registro_id = kwargs.pop('registro_id', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.form_class = 'p-0 md:p-2'
        self.helper.label_class = 'text-sm text-base-content'
        self.helper.field_class = 'mb-2'
        
        # Configurar el campo registro automáticamente
        self.fields['registro'].queryset = {app_name.title().replace('_', '')}.objects.all()
        
        try:
            if self.registro_id:
                registro_obj = {app_name.title().replace('_', '')}.objects.get(id=self.registro_id)
                self.fields['registro'].widget = forms.HiddenInput()
                self.initial['registro'] = registro_obj.id
                self.fields['registro'].initial = registro_obj.id
            elif self.instance.pk:
                self.fields['registro'].widget = forms.HiddenInput()
            else:
                self.fields['registro'].widget = forms.HiddenInput()
        except {app_name.title().replace('_', '')}.DoesNotExist:
            self.fields['registro'].widget = forms.HiddenInput()

        self.helper.layout = Layout(
            Field('registro'),
            Field('comentarios', css_class=f"{{get_form_field_css_class(self, 'comentarios')}} w-full"),
            Div(
                Submit('submit', 'Guardar Registro', css_class='btn btn-success w-full mt-4 sombra'),
                css_class='text-center'
            ),
        )
    
    class Meta:
        model = {paso.title()}
        fields = ['registro', 'comentarios']
        labels = {{
            'comentarios': 'Comentarios',
        }}
        widgets = {{
            'comentarios': forms.Textarea(attrs={{'rows': 4, 'placeholder': 'Ingrese comentarios...'}}),
        }}

'''

        with open(app_path / 'forms.py', 'w', encoding='utf-8') as f:
            f.write(forms_content)

    def _create_models(self, app_name, title, pasos):
        """Crear archivos de modelos"""
        app_path = Path(settings.BASE_DIR) / app_name

        models_content = f'''"""
Modelos para registros {title}.
"""

from registros.models.base import RegistroBase
from registros.models.paso import PasoBase
from django.db import models
from registros.models.validators import validar_latitud, validar_longitud
from registros.models.completeness_checker import check_model_completeness
from core.models.sites import Site
from users.models import User
from simple_history.models import HistoricalRecords

class {app_name.title().replace('_', '')}(RegistroBase):
    """
    Modelo para registros {title}.
    """
    sitio = models.ForeignKey(Site, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Sitio', related_name='{app_name}')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Usuario', related_name='{app_name}')
    title = models.CharField(max_length=100, verbose_name='Título')
    description = models.TextField(blank=True, null=True, verbose_name='Descripción')
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{app_name.title().replace('_', '')} {{self.id}}"
    
    def clean(self):
        """Custom validation method"""
        super().clean()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs) 

'''

        for paso in pasos:
            models_content += f'''
class {paso.title()}(PasoBase):
    """Paso {paso.title()} para registros {title}."""
    registro = models.ForeignKey({app_name.title().replace('_', '')}, on_delete=models.CASCADE, verbose_name='Registro')
    comentarios = models.TextField(blank=True, null=True, verbose_name='Comentarios')
    
    class Meta:
        verbose_name = 'Registro {paso.title()}'
        verbose_name_plural = 'Registros {paso.title()}'
    
    @staticmethod
    def get_etapa():
        return '{paso}'
    
    @staticmethod
    def get_actives():
        return {paso.title()}.objects.filter(is_deleted=False)

    @staticmethod
    def check_completeness({paso}_id):
        return check_model_completeness({paso.title()}, {paso}_id)

'''

        with open(app_path / 'models.py', 'w', encoding='utf-8') as f:
            f.write(models_content)

    def _create_admin(self, app_name, pasos):
        """Crear archivos de admin"""
        app_path = Path(settings.BASE_DIR) / app_name

        admin_content = f'''"""
Admin para registros {app_name}.
"""

from django.contrib import admin
from .models import {app_name.title().replace('_', '')}, {', '.join([paso.title() for paso in pasos])}

@admin.register({app_name.title().replace('_', '')})
class {app_name.title().replace('_', '')}Admin(admin.ModelAdmin):
    list_display = ['id', 'title', 'sitio', 'user', 'created_at']
    list_filter = ['created_at', 'sitio']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']

'''

        for paso in pasos:
            admin_content += f'''
@admin.register({paso.title()})
class {paso.title()}Admin(admin.ModelAdmin):
    list_display = ['id', 'registro', 'created_at']
    list_filter = ['created_at']
    search_fields = ['comentarios']
    readonly_fields = ['created_at', 'updated_at']

'''

        with open(app_path / 'admin.py', 'w', encoding='utf-8') as f:
            f.write(admin_content)

    def _create_urls(self, app_name, title):
        """Crear archivos de URLs"""
        app_path = Path(settings.BASE_DIR) / app_name

        urls_content = f'''"""
URLs para registros {title}.
"""

from django.urls import path
from .views import ListRegistrosView, StepsRegistroView, ElementoRegistroView, ActivarRegistroView
from .pdf_views import {app_name.title().replace('_', '')}PDFView, preview_{app_name}_individual

app_name = '{app_name}'

urlpatterns = [
    path('', ListRegistrosView.as_view(), name='list'),
    path('activar/', ActivarRegistroView.as_view(), name='activar'),
    path('<int:registro_id>/', StepsRegistroView.as_view(), name='steps'),
    path('<int:registro_id>/<str:paso_nombre>/', ElementoRegistroView.as_view(), name='elemento'),
    path('pdf/<int:registro_id>/', {app_name.title().replace('_', '')}PDFView.as_view(), name='pdf'),
    path('preview/<int:registro_id>/', preview_{app_name}_individual, name='preview'),
]'''

        with open(app_path / 'urls.py', 'w', encoding='utf-8') as f:
            f.write(urls_content)

    def _generate_pdf_step_data_code(self, pasos, app_name):
        """Generar código para los datos de cada paso en PDF"""
        code = ""
        for paso in pasos:
            code += f'''
        # Datos del paso {paso}
        paso_{paso} = registro.{paso}_set.first()
        if paso_{paso}:
            registro_{paso}_data = {{}}
            for field in paso_{paso}._meta.fields:
                if field.name not in ['id', 'created_at', 'updated_at', 'registro']:
                    value = getattr(paso_{paso}, field.name)
                    if value is not None and value != '':
                        registro_{paso}_data[f'{{field.verbose_name}}:'] = str(value)
            
            context['registro_{paso}'] = registro_{paso}_data
            
            # Mapa del {paso}
            registro_content_type = ContentType.objects.get_for_model(registro)
            mapa_{paso} = GoogleMapsImage.objects.filter(
                content_type=registro_content_type,
                object_id=registro.id,
                etapa='{paso}'
            ).first()
            
            if mapa_{paso}:
                context['google_{paso}_image'] = {{
                    'src': mapa_{paso}.imagen.url,
                    'alt': f'Mapa de {{paso}}',
                    'caption': f'Distancia: {{mapa_{paso}.distancia_total_metros:.0f}} m' if mapa_{paso} and mapa_{paso}.distancia_total_metros else 'Mapa no disponible',
                    'icon1_color': '#FF4040',
                    'name1': '{paso.title()}',
                }}
            else:
                context['google_{paso}_image'] = {{'src': None}}
            
            # Fotos del {paso}
            context['registro_{paso}_fotos'] = {{
                'fotos': self._get_photos(registro, '{paso}')
            }}
        else:
            context['registro_{paso}'] = {{}}
            context['google_{paso}_image'] = {{'src': None}}
            context['registro_{paso}_fotos'] = {{'fotos': []}}'''
        return code

    def _create_apps_py(self, app_name, title, description):
        """Crear archivo apps.py"""
        app_path = Path(settings.BASE_DIR) / app_name

        apps_content = f'''"""
Configuración de la aplicación {title}.
"""

from django.apps import AppConfig


class {app_name.title().replace('_', '')}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{app_name}'
    verbose_name = '{title}'
    description = '{description}'
'''

        with open(app_path / 'apps.py', 'w', encoding='utf-8') as f:
            f.write(apps_content)

    def _create_setup_example(self, app_name, title):
        """Crear archivo de ejemplo de configuración"""
        app_path = Path(settings.BASE_DIR) / app_name
        
        setup_content = f'''# Configuración Manual para {title}
# Este archivo muestra los pasos necesarios para completar la configuración

## 1. Agregar a INSTALLED_APPS (config/base.py)
```python
INSTALLED_APPS = [
    # ... otras apps
    '{app_name}',
]
```

## 2. Agregar URL (config/urls.py)
```python
urlpatterns = [
    # ... otras URLs
    path('{app_name}/', include('{app_name}.urls')),
]
```

## 3. Agregar al Menú (core/menu/menu_builder.py)
```python
menu = [
    # ... otros items
    MenuItem('{title}', '{app_name}:list', 'fas fa-file-alt', module='registros'),
]
```

## 4. Crear Migraciones
```bash
python manage.py makemigrations {app_name}
python manage.py migrate
```

## 5. Crear Superusuario (si no existe)
```bash
python manage.py createsuperuser
```

## 6. Verificar Funcionamiento
- Ir a http://localhost:8000/{app_name}/
- Verificar que aparezca en el menú lateral
- Probar crear un nuevo registro

## 7. Generar PDF (Opcional)
- Ir a http://localhost:8000/{app_name}/pdf/1/ para generar PDF
- Ir a http://localhost:8000/{app_name}/preview/1/ para previsualizar

## Notas
- La aplicación usa el sistema genérico de registros
- Los templates están en {app_name}/templates/{app_name}/
- La configuración está en {app_name}/config.py
- Los modelos heredan de RegistroBase y PasoBase
- **PDF automático**: Se generan templates y vistas de PDF automáticamente
- **Templates PDF**: En pdf_reports/templates/reportes_{app_name}/
- **Vista PDF**: {app_name}/pdf_views.py
'''
        
        with open(app_path / 'SETUP.md', 'w', encoding='utf-8') as f:
            f.write(setup_content)

    def _create_pdf_configuration(self, app_name, title, pasos):
        """Crear configuración de PDF para la aplicación"""
        app_path = Path(settings.BASE_DIR) / app_name
        
        # Crear directorio de templates PDF
        pdf_templates_path = Path(settings.BASE_DIR) / 'pdf_reports' / 'templates' / f'reportes_{app_name}'
        pdf_templates_path.mkdir(parents=True, exist_ok=True)
        (pdf_templates_path / 'partials').mkdir(exist_ok=True)
        
        # Template principal de PDF
        pdf_template = f'''{{% load static %}}
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Informe {title}</title>
  <link rel="stylesheet" href="{{% static 'css/weasyprint.css' %}}">
</head>
<body>

<!-- ENCABEZADO -->
<div id="page-header">
  <table class="header-table">
    <tr>
      <td class="header-logo left">
        {{% include "svgs/phoenix_tower_logo_horizontal.svg" %}}
      </td>
      <td class="header-title">
        <h1>{title} <br>
        {{{{ registro.sitio.pti_cell_id|default:registro.sitio.operator_id }}}}</h1>
      </td>
      <td class="header-logo right">
        {{% include "svgs/tekon_logo.svg" %}}
      </td>
    </tr>
  </table>  
</div>

<!-- PIE DE PÁGINA -->
<div id="page-footer">
  <span class="page-number"></span>
</div>

<!-- CONTENIDO DEL INFORME -->
<article id="datos-generales">
  <h2>Datos Generales.</h2>
  <section class="datos">
    <dl>
      {{% for key, value in datos_generales.items %}}
        <dt>{{{{ key }}}}</dt>
        <dd>{{{{ value }}}}</dd>
      {{% endfor %}}
    </dl>
  </section>

  <h2>INSPECCIÓN DE SITIO.</h2>
  <section class="datos">
    <dl>
      {{% for key, value in inspeccion_sitio.items %}}
        <dt>{{{{ key }}}}</dt>
        <dd>{{{{ value }}}}</dd>
      {{% endfor %}}
    </dl>
  </section>
</article>'''

        # Agregar secciones para cada paso
        for paso in pasos:
            pdf_template += f'''

<!-- {paso.title()} -->
<article id="registro-{paso}">
  <h2>{{{{ "{paso.title()}" }}}}</h2>
  <section class="content-registro">
    {{% for key, value in registro_{paso}.items %}}
    {{% if value != '' %}}
      <p><strong>{{{{ key }}}}</strong> {{{{ value }}}}</p>
    {{% endif %}}
    {{% endfor %}}
  </section>
</article>

<!-- Mapa del {paso} -->
{{% if google_{paso}_image.src %}}
<table class="mapa-table">
  <tr>
    <td class="mapa-img-cell">
      <img src="{{{{ google_{paso}_image.src }}}}" alt="{{{{ google_{paso}_image.alt }}}}">
      <p class="mapa-leyenda-caption">{{{{ google_{paso}_image.caption|default:"" }}}}</p>
    </td>
    <td class="mapa-leyenda-cell">
      {{% include "reportes_{app_name}/partials/leyenda.html" with icon_color=google_{paso}_image.icon1_color name=google_{paso}_image.name1 %}}
      {{% if google_{paso}_image.icon2_color %}}
        {{% include "reportes_{app_name}/partials/leyenda.html" with icon_color=google_{paso}_image.icon2_color name=google_{paso}_image.name2 %}}
      {{% endif %}}
      {{% if google_{paso}_image.icon3_color %}}
        {{% include "reportes_{app_name}/partials/leyenda.html" with icon_color=google_{paso}_image.icon3_color name=google_{paso}_image.name3 %}}
      {{% endif %}}
    </td>
  </tr>
</table>
{{% endif %}}

<!-- Fotos del {paso.title()} -->
{{% if registro_{paso}_fotos.fotos %}}
  <section class="imagenes">
    <div class="foto-titulo">
      <p><strong>Registro Fotográfico del {{%{{ "{paso.title()}" %}}%}}:</strong></p>
    </div>
    {{% for foto in registro_{paso}_fotos.fotos %}}
      <div>
        <img src="{{%{{ foto.src %}}%}}" alt="{{%{{ foto.alt %}}%}}">
        <p style="">{{%{{ foto.descripcion %}}%}}</p>
      </div>
    {{% endfor %}}
  </section>
{{% endif %}}'''

        pdf_template += '''

</body>
</html>'''

        # Guardar template principal
        with open(pdf_templates_path / f'{app_name}.html', 'w', encoding='utf-8') as f:
            f.write(pdf_template)
        
        # Template de leyenda
        leyenda_template = '''{% if icon_color and name %}
<div class="leyenda-item">
  <svg width="12" height="12" viewBox="0 0 12 12" xmlns="http://www.w3.org/2000/svg">
    <circle cx="6" cy="6" r="6" fill="{{ icon_color }}"/>
  </svg>
  <span>{{ name }}</span>
</div>
{% endif %}'''
        
        with open(pdf_templates_path / 'partials' / 'leyenda.html', 'w', encoding='utf-8') as f:
            f.write(leyenda_template)
        
        # Template de tabla
        tabla_template = '''{% if tabla.headers and tabla.rows %}
<table class="table table-centered">
  <thead>
    <tr>
      {% for header in tabla.headers %}
        <th>{{ header }}</th>
      {% endfor %}
    </tr>
  </thead>
  <tbody>
    {% for row in tabla.rows %}
      <tr>
        {% for cell in row %}
          <td>{{ cell }}</td>
        {% endfor %}
      </tr>
    {% endfor %}
  </tbody>
</table>
{% endif %}'''
        
        with open(pdf_templates_path / 'partials' / 'tabla.html', 'w', encoding='utf-8') as f:
            f.write(tabla_template)
        
        # Crear vista de PDF
        pdf_view_content = f'''from django_weasyprint.views import WeasyTemplateView
from datetime import datetime
from {app_name}.models import {app_name.title().replace('_', '')}
from django.conf import settings
from pathlib import Path
from django.shortcuts import render
from core.models.google_maps import GoogleMapsImage
from django.contrib.contenttypes.models import ContentType
from {app_name}.config import PASOS_CONFIG

def convert_lat_to_dms(lat):
    if lat is None:
        return 'N/A'
    direction = 'N' if lat >= 0 else 'S'
    deg_abs = abs(lat)
    degrees = int(deg_abs)
    minutes_full = (deg_abs - degrees) * 60
    minutes = int(minutes_full)
    seconds = round((minutes_full - minutes) * 60, 2)
    return f"{{direction}} {{degrees}}° {{minutes}}' {{seconds}}''"

def convert_lon_to_dms(lon):
    if lon is None:
        return 'N/A'
    direction = 'E' if lon >= 0 else 'W'
    deg_abs = abs(lon)
    degrees = int(deg_abs)
    minutes_full = (deg_abs - degrees) * 60
    minutes = int(minutes_full)
    seconds = round((minutes_full - minutes) * 60, 2)
    return f"{{direction}} {{degrees}}° {{minutes}}' {{seconds}}''"

class {app_name.title().replace('_', '')}PDFView(WeasyTemplateView):
    template_name = 'reportes_{app_name}/{app_name}.html'
    pdf_options = {{
        'default-font-family': 'Arial',
        'default-font-size': 12,
        'enable-local-file-access': True,
    }}
    pdf_stylesheets = [str(Path(settings.BASE_DIR) / 'static/css/weasyprint.css')]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registro_id = self.kwargs.get('registro_id')

        registro = {app_name.title().replace('_', '')}.objects.select_related('sitio', 'user')\\
            .prefetch_related({', '.join([f"'{paso}_set'" for paso in pasos])})\\
            .get(id=registro_id)
        
        # Datos generales
        context.update({{
            'registro': registro,
            'datos_generales': {{
                f'Código {{registro.sitio._meta.get_field("pti_cell_id").verbose_name}}:': registro.sitio.pti_cell_id,
                f'Código {{registro.sitio._meta.get_field("operator_id").verbose_name}}:': registro.sitio.operator_id,
                f'{{registro.sitio._meta.get_field("name").verbose_name}}:': registro.sitio.name,
                f'{{registro.sitio._meta.get_field("lat_base").verbose_name}}:': registro.sitio.lat_base,
                f'{{registro.sitio._meta.get_field("lon_base").verbose_name}}:': registro.sitio.lon_base, 
                f'{{registro.sitio._meta.get_field("region").verbose_name}}:': registro.sitio.region,
                f'{{registro.sitio._meta.get_field("comuna").verbose_name}}:': registro.sitio.comuna,
            }},
            'inspeccion_sitio': {{
                'Responsable Técnico:': registro.user.first_name + ' ' + registro.user.last_name,
                'Fecha de Inspección:': registro.created_at.strftime('%d/%m/%Y'),
            }},
        }})
        
        # Agregar datos de cada paso
        {self._generate_pdf_step_data_code(pasos, app_name)}
        
        return context

    def _get_photos(self, registro, etapa):
        """Obtiene todas las fotos relacionadas con el registro para una etapa específica."""
        from photos.models import Photos
        from django.contrib.contenttypes.models import ContentType
        
        registro_content_type = ContentType.objects.get_for_model(registro)
        
        fotos = Photos.objects.filter(
            content_type=registro_content_type,
            object_id=registro.id,
            etapa=etapa,
            app='{app_name}'
        ).order_by('orden', '-created_at')
        
        fotos_list = []
        for foto in fotos:
            fotos_list.append({{
                'src': foto.imagen.url,
                'alt': foto.descripcion or f'Foto de {{etapa}} {{registro.sitio.pti_cell_id}}',
                'descripcion': foto.descripcion,
                'orden': foto.orden
            }})
        
        return fotos_list

def preview_{app_name}_individual(request, registro_id):
    view = {app_name.title().replace('_', '')}PDFView()
    view.kwargs = {{'registro_id': registro_id}}
    context = view.get_context_data()
    return render(request, 'reportes_{app_name}/{app_name}.html', context)
'''
        
        with open(app_path / 'pdf_views.py', 'w', encoding='utf-8') as f:
            f.write(pdf_view_content)
        
        # Actualizar URLs para incluir PDF
        urls_content = f'''from django.urls import path
from .views import (
    ListRegistrosView,
    StepsRegistroView,
    ElementoRegistroView,
    ActivarRegistroView
)
from .pdf_views import {app_name.title().replace('_', '')}PDFView, preview_{app_name}_individual

app_name = '{app_name}'

urlpatterns = [
    path('', ListRegistrosView.as_view(), name='list'),
    path('activar/', ActivarRegistroView.as_view(), name='activar'),
    path('<int:registro_id>/', StepsRegistroView.as_view(), name='steps'),
    path('<int:registro_id>/<str:paso>/', ElementoRegistroView.as_view(), name='elemento'),
    path('pdf/<int:registro_id>/', {app_name.title().replace('_', '')}PDFView.as_view(), name='pdf'),
    path('preview/<int:registro_id>/', preview_{app_name}_individual, name='preview'),
]'''
        
        with open(app_path / 'urls.py', 'w', encoding='utf-8') as f:
            f.write(urls_content)

    def _create_pdf_views(self, app_name, title, pasos):
        """Crear vistas de PDF específicas para la aplicación"""
        app_path = Path(settings.BASE_DIR) / app_name
        
        pdf_view_content = f'''"""
Vistas de PDF para registros {title}.
"""
from pdf_reports.views import RegistroPDFView, preview_registro_individual
from django.shortcuts import render

class {app_name.title().replace('_', '')}PDFView(RegistroPDFView):
    """Vista para generar PDF de registros {title}."""
    pass

def preview_{app_name}_individual(request, registro_id):
    """Vista para previsualizar el PDF de un registro {title}."""
    view = {app_name.title().replace('_', '')}PDFView()
    view.kwargs = {{'registro_id': registro_id}}
    context = view.get_context_data()
    return render(request, 'reportes_{app_name}/{app_name}.html', context)
'''
        
        with open(app_path / 'pdf_views.py', 'w', encoding='utf-8') as f:
            f.write(pdf_view_content) 