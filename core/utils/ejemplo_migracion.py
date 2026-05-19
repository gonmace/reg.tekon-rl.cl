# Ejemplo de Migración al BreadcrumbsMixin Simplificado
# Este archivo muestra cómo migrar vistas existentes al nuevo sistema

from django.views.generic import TemplateView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from core.utils.breadcrumbs import BreadcrumbsMixin

# ============================================================================
# ANTES: Vista compleja con lógica de auto-detección
# ============================================================================

class VistaAntiguaCompleja(LoginRequiredMixin, BreadcrumbsMixin, TemplateView):
    template_name = 'pages/vista_antigua.html'
    
    def get_parent_breadcrumbs(self):
        """Método complejo para generar breadcrumbs padres"""
        return [{"label": "Sección Padre", "url": reverse("app:padre")}]
    
    def get_page_title(self):
        """Lógica compleja para el título"""
        if self.request.user.is_superuser:
            return "Administración"
        return "Vista Normal"

# ============================================================================
# AHORA: Vista simple con configuración clara
# ============================================================================

class VistaNuevaSimple(LoginRequiredMixin, BreadcrumbsMixin, TemplateView):
    template_name = 'pages/vista_nueva.html'
    
    class Meta:
        title = 'Mi Vista'
        header_title = 'Gestión de Mi Vista'
        breadcrumbs = [
            {'label': 'Inicio', 'url_name': 'dashboard:dashboard'},
            {'label': 'Sección Padre', 'url_name': 'app:padre'},
            {'label': 'Mi Vista'}
        ]

# ============================================================================
# EJEMPLOS PRÁCTICOS DE MIGRACIÓN
# ============================================================================

# 1. Vista de Dashboard (ya migrada)
class DashboardView(BreadcrumbsMixin, TemplateView):
    template_name = 'pages/dashboard.html'
    
    class Meta:
        title = 'Dashboard'
        header_title = 'Panel Principal'

# 2. Vista de Lista con breadcrumbs personalizados
class ListaRegistrosView(LoginRequiredMixin, BreadcrumbsMixin, TemplateView):
    template_name = 'pages/lista_registros.html'
    
    class Meta:
        title = 'Registros'
        header_title = 'Gestión de Registros'
        breadcrumbs = [
            {'label': 'Inicio', 'url_name': 'dashboard:dashboard'},
            {'label': 'Registros'}
        ]

# 3. Vista de Detalle con breadcrumbs dinámicos
class DetalleRegistroView(LoginRequiredMixin, BreadcrumbsMixin, DetailView):
    model = Registro
    template_name = 'pages/detalle_registro.html'
    
    class Meta:
        title = 'Detalle del Registro'
        header_title = 'Información del Registro'
        breadcrumbs = [
            {'label': 'Inicio', 'url_name': 'dashboard:dashboard'},
            {'label': 'Registros', 'url_name': 'registros:list'},
            {'label': 'Detalle'}
        ]
    
    def get_page_title(self):
        """Personalizar título con datos del objeto"""
        obj = self.get_object()
        return f"Registro: {obj.nombre}"

# 4. Vista de Formulario con breadcrumbs contextuales
class CrearRegistroView(LoginRequiredMixin, BreadcrumbsMixin, FormView):
    template_name = 'pages/crear_registro.html'
    form_class = RegistroForm
    
    class Meta:
        title = 'Nuevo Registro'
        header_title = 'Crear Registro'
        breadcrumbs = [
            {'label': 'Inicio', 'url_name': 'dashboard:dashboard'},
            {'label': 'Registros', 'url_name': 'registros:list'},
            {'label': 'Nuevo Registro'}
        ]

# 5. Vista con breadcrumbs dinámicos (como la vista genérica)
class VistaConBreadcrumbsDinamicos(LoginRequiredMixin, BreadcrumbsMixin, FormView):
    template_name = 'pages/vista_dinamica.html'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.seccion = kwargs.get('seccion', 'general')
    
    def get_page_title(self):
        """Título dinámico basado en la sección"""
        return f"{self.seccion.title()}"
    
    def get_breadcrumbs(self):
        """Breadcrumbs dinámicos basados en la sección"""
        breadcrumbs = [
            {'label': 'Inicio', 'url_name': 'dashboard:dashboard'},
            {'label': 'Sección', 'url_name': 'app:seccion'}
        ]
        
        if self.seccion != 'general':
            breadcrumbs.append({'label': self.seccion.title()})
        
        return breadcrumbs

# ============================================================================
# VENTAJAS DE LA MIGRACIÓN
# ============================================================================

"""
✅ MÁS SIMPLE:
   - Solo necesitas definir Meta
   - No más métodos complejos
   - Configuración en un solo lugar

✅ MÁS CLARO:
   - Breadcrumbs explícitos
   - Títulos claros
   - Fácil de entender

✅ MÁS FLEXIBLE:
   - Puedes personalizar exactamente lo que necesitas
   - Breadcrumbs dinámicos cuando sea necesario
   - Fallbacks automáticos

✅ MÁS MANTENIBLE:
   - Menos código
   - Menos lógica compleja
   - Fácil de modificar

✅ MIGRACIÓN GRADUAL:
   - Las vistas existentes siguen funcionando
   - Puedes migrar una por una
   - No hay cambios breaking
"""

# ============================================================================
# PASOS PARA MIGRAR UNA VISTA
# ============================================================================

"""
1. Identificar la vista a migrar
2. Agregar BreadcrumbsMixin a la herencia
3. Definir la clase Meta con:
   - title: título de la página
   - header_title: título del header
   - breadcrumbs: lista de breadcrumbs (opcional)
4. Eliminar métodos complejos como get_parent_breadcrumbs()
5. Probar que todo funciona correctamente
""" 