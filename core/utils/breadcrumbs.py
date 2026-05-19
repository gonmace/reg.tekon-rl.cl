from django.urls import reverse, NoReverseMatch
from django.utils.text import capfirst

class BreadcrumbsMixin:
    """
    Mixin simple para manejar breadcrumbs y títulos de página.
    
    Uso básico:
    class MiVistaView(BreadcrumbsMixin, TemplateView):
        template_name = 'mi_template.html'
        
        class Meta:
            title = 'Mi Página'
            header_title = 'Gestión de Mi Página'
            breadcrumbs = [
                {'label': 'Inicio', 'url_name': 'dashboard:dashboard'},
                {'label': 'Mi Página'}
            ]
    """
    
    def get_page_title(self):
        """Obtiene el título de la página desde Meta.title o genera uno automático"""
        meta = getattr(self, 'Meta', None)
        if meta and hasattr(meta, 'title'):
            return meta.title
        
        # Fallback automático basado en el nombre de la clase
        return capfirst(self.__class__.__name__.replace('View', ''))

    def get_header_title(self):
        """Obtiene el título del header desde Meta.header_title o usa el page_title"""
        meta = getattr(self, 'Meta', None)
        if meta and hasattr(meta, 'header_title'):
            return meta.header_title
        
        # Por defecto usa el título de la página
        return self.get_page_title()

    def get_breadcrumbs(self):
        """Obtiene los breadcrumbs desde Meta.breadcrumbs o genera unos básicos"""
        meta = getattr(self, 'Meta', None)
        
        # Si hay breadcrumbs definidos en Meta, usarlos
        if meta and hasattr(meta, 'breadcrumbs'):
            return self._resolve_breadcrumbs(meta.breadcrumbs)
        
        # Si no hay breadcrumbs definidos, generar unos básicos
        return self._generate_default_breadcrumbs()
    
    def _resolve_breadcrumbs(self, breadcrumb_list):
        """Resuelve las URLs de los breadcrumbs definidos en Meta"""
        resolved = []
        for item in breadcrumb_list:
            url = None
            if 'url_name' in item:
                try:
                    # Si hay url_kwargs, usarlos para generar la URL
                    if 'url_kwargs' in item:
                        url = reverse(item['url_name'], kwargs=item['url_kwargs'])
                    else:
                        url = reverse(item['url_name'])
                except NoReverseMatch:
                    url = "#"
            resolved.append({"label": item["label"], "url": url})
        return resolved
    
    def _generate_default_breadcrumbs(self):
        """Genera breadcrumbs básicos: Inicio + Título actual"""
        breadcrumbs = [
            {"label": "Inicio", "url": reverse("dashboard:dashboard")}
        ]
        
        # Agregar el título actual sin URL (página actual)
        breadcrumbs.append({"label": self.get_page_title()})
        
        return breadcrumbs

    def get_context_data(self, **kwargs):
        """Agrega breadcrumbs, page_title y header_title al contexto"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.get_page_title()
        context['header_title'] = self.get_header_title()
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context
