import json

from import_export import fields, resources

from .models import ConfigPaso


class ConfigPasoResource(resources.ModelResource):
    nombre = fields.Field(attribute='pasodef__nombre', column_name='nombre')
    titulo = fields.Field(attribute='pasodef__titulo', column_name='titulo')
    descripcion = fields.Field(attribute='pasodef__descripcion', column_name='descripcion')
    orden = fields.Field(attribute='orden', column_name='orden')
    widgets_json = fields.Field(column_name='widgets_json')

    class Meta:
        model = ConfigPaso
        fields = ('nombre', 'titulo', 'descripcion', 'orden', 'widgets_json')
        export_order = ('nombre', 'titulo', 'descripcion', 'orden', 'widgets_json')
        import_id_fields = ('nombre',)

    def dehydrate_widgets_json(self, obj):
        widgets = obj.pasodef.paso_widgets.order_by('orden')
        data = [{'slug': pw.widget_slug, 'orden': pw.orden, 'config': pw.config} for pw in widgets]
        return json.dumps(data, ensure_ascii=False)
