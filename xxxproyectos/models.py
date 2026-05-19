"""
Modelos para el manejo de componentes y grupos de componentes.
"""

from django.db import models


# 1. Componente base (reutilizable)
class Componente(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre


# 2. Grupo de componentes (estructura reutilizable)
class GrupoComponentes(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre


# 3. Componentes dentro de un grupo con incidencia
class ComponenteGrupo(models.Model):
    grupo = models.ForeignKey(GrupoComponentes, on_delete=models.CASCADE, related_name="componentes")
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE)
    incidencia = models.DecimalField(max_digits=5, decimal_places=2, help_text="En porcentaje, debe sumar 100% entre todos los componentes del grupo.")
    orden = models.PositiveIntegerField(default=0, blank=False, null=False, verbose_name="Orden")

    class Meta:
        unique_together = ('grupo', 'componente')
        ordering = ['orden', 'id']

    def __str__(self):
        return f"{self.componente.nombre} ({self.incidencia}%)"
