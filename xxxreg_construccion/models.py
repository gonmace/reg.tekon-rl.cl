"""
Modelos para registros Reporte de construcción.
"""

from registros.models.base import RegistroBase
from registros.models.paso import PasoBase
from django.db import models
from registros.models.validators import validar_latitud, validar_longitud
from registros.models.completeness_checker import check_model_completeness
from core.models.sites import Site
from core.models.contractors import Contractor
from users.models import User
from proyectos.models import GrupoComponentes, Componente
from simple_history.models import HistoricalRecords
from datetime import date

class RegConstruccion(RegistroBase):
    """
    Modelo para registros Reporte de construcción.
    """
    # Choices para el estado del proyecto
    ESTADO_CHOICES = [
        ('construccion', 'Construcción'),
        ('paralizado', 'Paralizado'),
        ('cancelado', 'Cancelado'),
        ('concluido', 'Concluido'),
    ]
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='construccion',
        verbose_name='Estado del Proyecto',
        help_text='Estado actual del proyecto de construcción'
    )
    """
    Modelo para registros Reporte de construcción.
    """
    sitio = models.ForeignKey(Site, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Sitio', related_name='reg_construccion')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Usuario', related_name='reg_construccion')
    contratista = models.ForeignKey(Contractor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Contratista', related_name='reg_construccion')
    estructura = models.ForeignKey(GrupoComponentes, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Estructura', related_name='reg_construccion')
    title = models.CharField(max_length=100, verbose_name='Título')
    description = models.TextField(blank=True, null=True, verbose_name='Descripción')
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"RegConstruccion {self.id}"
    
    def clean(self):
        """Custom validation method"""
        super().clean()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs) 
        
    def get_reg_app_name(self):
        return "reg_construccion"

class Objetivo(PasoBase):
    """
    Modelo para el paso principal de objetivo.
    """
    registro = models.ForeignKey(RegConstruccion, on_delete=models.CASCADE, verbose_name='Registro')
    objetivo = models.TextField(blank=True, null=True, verbose_name='Objetivo')
    
    class Meta:
        verbose_name = 'Objetivo'
        verbose_name_plural = 'Objetivos'
    
    @staticmethod
    def get_etapa():
        return 'objetivo'
    
    @staticmethod
    def check_completeness(objetivo_id):
        return check_model_completeness(Objetivo, objetivo_id)

class AvanceComponenteComentarios(PasoBase):
    """
    Modelo simple para el paso principal de avance por componente.
    Solo contiene comentarios generales del paso.
    """
    registro = models.ForeignKey(RegConstruccion, on_delete=models.CASCADE, verbose_name='Registro')
    comentarios = models.TextField(blank=True, null=True, verbose_name='Comentarios')
    
    class Meta:
        verbose_name = 'Comentarios Avance por Componente'
        verbose_name_plural = 'Comentarios Avances por Componente'
    
    @staticmethod
    def get_etapa():
        return 'avance_componente'
    
    @staticmethod
    def get_actives():
        return AvanceComponenteComentarios.objects.filter(is_deleted=False)

    @staticmethod
    def check_completeness(avance_componente_comentarios_id):
        return check_model_completeness(AvanceComponenteComentarios, avance_componente_comentarios_id)


class AvanceComponente(PasoBase):
    """
    Avance específico por componente de la estructura del proyecto.
    Permite registrar el progreso actual y acumulado de cada componente.
    """
    registro = models.ForeignKey(RegConstruccion, on_delete=models.CASCADE, verbose_name='Registro')
    fecha = models.DateField(verbose_name='Fecha del avance', default=date.today)
    componente = models.ForeignKey(
        Componente, 
        on_delete=models.CASCADE, 
        verbose_name='Componente',
        related_name='avances_componente'
    )
    porcentaje_anterior = models.IntegerField(
        verbose_name='Porcentaje anterior', 
        default=0,
        help_text='Porcentaje de avance anterior del componente (0-100)'
    )
    porcentaje_actual = models.IntegerField(
        verbose_name='Porcentaje actual', 
        default=0,
        help_text='Porcentaje de avance actual del componente (0-100)'
    )
    porcentaje_acumulado = models.IntegerField(
        verbose_name='Porcentaje acumulado', 
        default=0,
        help_text='Porcentaje de avance acumulado del componente (0-100)'
    )
    comentarios = models.TextField(blank=True, null=True, verbose_name='Comentarios')
    
    class Meta:
        verbose_name = 'Avance por Componente'
        verbose_name_plural = 'Avances por Componente'
        ordering = ['-fecha', '-created_at']
        unique_together = ['registro', 'componente', 'fecha']
    
    @staticmethod
    def get_etapa():
        return 'avance_componente'
    
    @staticmethod
    def get_actives():
        return AvanceComponente.objects.filter(is_deleted=False)

    @staticmethod
    def check_completeness(avance_componente_id):
        return check_model_completeness(AvanceComponente, avance_componente_id)
    
    def clean(self):
        """Validación personalizada para los porcentajes"""
        super().clean()
        if self.porcentaje_actual < 0 or self.porcentaje_actual > 100:
            from django.core.exceptions import ValidationError
            raise ValidationError('El porcentaje actual debe estar entre 0 y 100')
        
        if self.porcentaje_acumulado < 0 or self.porcentaje_acumulado > 100:
            from django.core.exceptions import ValidationError
            raise ValidationError('El porcentaje acumulado debe estar entre 0 y 100')
        
        if self.porcentaje_acumulado < self.porcentaje_actual:
            from django.core.exceptions import ValidationError
            raise ValidationError('El porcentaje acumulado no puede ser menor al porcentaje actual')
    
    def save(self, *args, **kwargs):
        print("Entrando al Save de AvanceComponente...", self.porcentaje_acumulado)
        """Sobrescribir save para calcular automáticamente el porcentaje acumulado si no se especifica"""
        if not self.porcentaje_acumulado:
            # Obtener el último avance acumulado para este componente
            ultimo_avance = AvanceComponente.objects.filter(
                registro=self.registro,
                componente=self.componente
            ).exclude(id=self.id).order_by('-fecha', '-created_at').first()

            print("Ultimo avance acumulado para este componente: ", ultimo_avance)
            if ultimo_avance:
                self.porcentaje_acumulado = max(ultimo_avance.porcentaje_acumulado, self.porcentaje_actual)
            else:
                self.porcentaje_acumulado = self.porcentaje_actual
        
        super().save(*args, **kwargs)


class EjecucionPorcentajes(models.Model):
    """
    Modelo para almacenar los porcentajes de ejecución actual y anterior
    calculados para cada componente de un registro de construcción.
    """
    registro = models.ForeignKey(RegConstruccion, on_delete=models.CASCADE, verbose_name='Registro')
    componente = models.ForeignKey(
        Componente, 
        on_delete=models.CASCADE, 
        verbose_name='Componente',
        related_name='ejecucion_porcentajes'
    )
    porcentaje_ejec_actual = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name='Porcentaje Ejecución Actual',
        help_text='Porcentaje de ejecución actual del componente'
    )
    porcentaje_ejec_anterior = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name='Porcentaje Ejecución Anterior',
        help_text='Porcentaje de ejecución anterior del componente'
    )
    fecha_calculo = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Cálculo'
    )
    
    class Meta:
        verbose_name = 'Ejecución Porcentajes'
        verbose_name_plural = 'Ejecuciones Porcentajes'
        ordering = ['-fecha_calculo']
        unique_together = ['registro', 'componente']
    
    def __str__(self):
        return f"{self.registro} - {self.componente} - Actual: {self.porcentaje_ejec_actual}%, Anterior: {self.porcentaje_ejec_anterior}%"
    
    def clean(self):
        """Validación personalizada para los porcentajes"""
        super().clean()
        if self.porcentaje_ejec_actual < 0 or self.porcentaje_ejec_actual > 100:
            from django.core.exceptions import ValidationError
            raise ValidationError('El porcentaje de ejecución actual debe estar entre 0 y 100')
        
        if self.porcentaje_ejec_anterior < 0 or self.porcentaje_ejec_anterior > 100:
            from django.core.exceptions import ValidationError
            raise ValidationError('El porcentaje de ejecución anterior debe estar entre 0 y 100')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


