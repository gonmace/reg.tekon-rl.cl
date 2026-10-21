from rest_framework import serializers
from .models import Site

class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = '__all__'

    def _unico_entre_activos(self, campo, valor, mensaje):
        """PTI ID y nombre son únicos solo entre sitios no eliminados (ver Site.Meta.constraints)."""
        if valor in (None, ''):
            return valor
        qs = Site.objects.filter(is_deleted=False, **{campo: valor})
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(mensaje)
        return valor

    def validate_pti_cell_id(self, value):
        return self._unico_entre_activos('pti_cell_id', value, 'Ya existe un sitio activo con este PTI ID.')

    def validate_name(self, value):
        return self._unico_entre_activos('name', value, 'Ya existe un sitio activo con este nombre.')

