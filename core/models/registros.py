from django.db import models
from core.models.sites import Site
from core.models import BaseModel

class Registro(BaseModel):
    sitio = models.ForeignKey(Site, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = 'Registro'
        verbose_name_plural = 'Registros'
    
    def __str__(self):
        return f"{self.sitio} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"


