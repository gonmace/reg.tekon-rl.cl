"""
Serializers para la API de reg_construccion.
"""

from rest_framework import serializers
from .models import RegConstruccion, Objetivo, AvanceComponente, AvanceComponenteComentarios, EjecucionPorcentajes
from core.models.sites import Site
from core.models.contractors import Contractor
from users.models import User
from proyectos.models import GrupoComponentes, Componente


class SiteSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Site."""
    class Meta:
        model = Site
        fields = ['id', 'name', 'pti_cell_id', 'operator_id']


class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User."""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class ContractorSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Contractor."""
    class Meta:
        model = Contractor
        fields = ['id', 'name', 'code']


class GrupoComponentesSerializer(serializers.ModelSerializer):
    """Serializer para el modelo GrupoComponentes."""
    class Meta:
        model = GrupoComponentes
        fields = ['id', 'nombre']


class ComponenteSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Componente."""
    class Meta:
        model = Componente
        fields = ['id', 'nombre']


class ObjetivoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Objetivo."""
    class Meta:
        model = Objetivo
        fields = ['id', 'objetivo', 'is_deleted', 'created_at', 'updated_at']


class AvanceComponenteComentariosSerializer(serializers.ModelSerializer):
    """Serializer para el modelo AvanceComponenteComentarios."""
    class Meta:
        model = AvanceComponenteComentarios
        fields = ['id', 'comentarios', 'is_deleted', 'created_at', 'updated_at']


class AvanceComponenteSerializer(serializers.ModelSerializer):
    """Serializer para el modelo AvanceComponente."""
    componente = ComponenteSerializer(read_only=True)
    componente_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = AvanceComponente
        fields = [
            'id', 'fecha', 'componente', 'componente_id', "porcentaje_anterior",
            'porcentaje_actual', 'porcentaje_acumulado', 'comentarios',
            'is_deleted', 'created_at', 'updated_at'
        ]


class EjecucionPorcentajesSerializer(serializers.ModelSerializer):
    """Serializer para el modelo EjecucionPorcentajes."""
    componente = ComponenteSerializer(read_only=True)
    
    class Meta:
        model = EjecucionPorcentajes
        fields = [
            'id', 'componente', 'porcentaje_ejec_actual', 
            'porcentaje_ejec_anterior', 'fecha_calculo'
        ]


class RegConstruccionSerializer(serializers.ModelSerializer):
    """Serializer para el modelo RegConstruccion."""
    sitio = SiteSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    contratista = ContractorSerializer(read_only=True)
    estructura = GrupoComponentesSerializer(read_only=True)
    objetivos = ObjetivoSerializer(source='objetivo_set', many=True, read_only=True)
    avances_componente = AvanceComponenteSerializer(source='avancecomponente_set', many=True, read_only=True)
    avance_componente_comentarios = AvanceComponenteComentariosSerializer(source='avancecomponentecomentarios_set', many=True, read_only=True)
    ejecucion_porcentajes = EjecucionPorcentajesSerializer(source='ejecucionporcentajes_set', many=True, read_only=True)
    
    # Campos para escritura
    sitio_id = serializers.IntegerField(write_only=True, required=False)
    user_id = serializers.IntegerField(write_only=True, required=False)
    contratista_id = serializers.IntegerField(write_only=True, required=False)
    estructura_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = RegConstruccion
        fields = [
            'id', 'estado', 'sitio', 'sitio_id', 'user', 'user_id', 
            'contratista', 'contratista_id', 'estructura', 'estructura_id',
            'title', 'description', 'fecha', 'is_active', 'created_at', 'updated_at',
            'objetivos', 'avances_componente', 'avance_componente_comentarios', 
            'ejecucion_porcentajes'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RegConstruccionListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar registros de construcción."""
    sitio = SiteSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    contratista = ContractorSerializer(read_only=True)
    estructura = GrupoComponentesSerializer(read_only=True)
    
    class Meta:
        model = RegConstruccion
        fields = [
            'id', 'estado', 'sitio', 'user', 'contratista', 'estructura',
            'title', 'description', 'fecha', 'is_active', 'created_at', 'updated_at'
        ]
