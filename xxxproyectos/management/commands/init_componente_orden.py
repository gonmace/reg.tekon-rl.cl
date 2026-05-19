from django.core.management.base import BaseCommand
from proyectos.models import ComponenteGrupo


class Command(BaseCommand):
    help = 'Inicializa el orden de los componentes en grupos existentes'

    def handle(self, *args, **options):
        # Obtener todos los grupos únicos
        grupos = ComponenteGrupo.objects.values_list('grupo', flat=True).distinct()
        
        for grupo_id in grupos:
            # Obtener componentes del grupo ordenados por ID
            componentes = ComponenteGrupo.objects.filter(grupo_id=grupo_id).order_by('id')
            
            # Asignar orden secuencial
            for index, componente in enumerate(componentes):
                componente.orden = index
                componente.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Inicializado orden para grupo {grupo_id}: {componentes.count()} componentes'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS('Orden de componentes inicializado correctamente')
        )
