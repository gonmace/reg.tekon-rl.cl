"""
Resources de django-import-export para usar tanto en admin como en vistas.
"""

from import_export import fields, resources

from core.models.sites import Site


class SiteResource(resources.ModelResource):
    pti_cell_id = fields.Field(attribute='pti_cell_id', column_name='PTI ID')
    operator_id = fields.Field(attribute='operator_id', column_name='Operador ID')
    nombre_sitio = fields.Field(attribute='name', column_name='Nombre del Sitio')
    tipo_sitio = fields.Field(attribute='tipo_sitio', column_name='Tipo de sitio')
    lat_man = fields.Field(attribute='lat_man', column_name='Latitud Mandato')
    lon_man = fields.Field(attribute='lon_man', column_name='Longitud Mandato')
    lat_ing = fields.Field(attribute='lat_ing', column_name='Latitud Ingeniería')
    lon_ing = fields.Field(attribute='lon_ing', column_name='Longitud Ingeniería')
    lat_con = fields.Field(attribute='lat_con', column_name='Latitud Construcción')
    lon_con = fields.Field(attribute='lon_con', column_name='Longitud Construcción')
    alt = fields.Field(attribute='alt', column_name='Altura (m)')
    region = fields.Field(attribute='region', column_name='Region / Provincia')
    comuna = fields.Field(attribute='comuna', column_name='Comuna / Municipio')
    empresa_energia = fields.Field(attribute='empresa_energia', column_name='Empresa de Energía')

    class Meta:
        model = Site
        fields = (
            'pti_cell_id', 'operator_id', 'nombre_sitio', 'tipo_sitio',
            'lat_man', 'lon_man', 'lat_ing', 'lon_ing', 'lat_con', 'lon_con',
            'alt', 'region', 'comuna', 'empresa_energia',
        )
        export_order = (
            'pti_cell_id', 'operator_id', 'nombre_sitio', 'tipo_sitio',
            'lat_man', 'lon_man', 'lat_ing', 'lon_ing', 'lat_con', 'lon_con',
            'alt', 'region', 'comuna', 'empresa_energia',
        )
        import_id_fields = ('pti_cell_id',)
