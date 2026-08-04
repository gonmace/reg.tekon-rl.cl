from django.contrib import admin
from django.utils.html import format_html

from .models import ImagenEjemplo


@admin.register(ImagenEjemplo)
class ImagenEjemploAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug', 'preview')
    prepopulated_fields = {'slug': ('nombre',)}
    search_fields = ('nombre', 'slug')

    def preview(self, obj):
        if not obj.imagen:
            return ''
        return format_html('<img src="{}" style="height:60px;border-radius:6px;">', obj.imagen.url)
    preview.short_description = 'Vista previa'
