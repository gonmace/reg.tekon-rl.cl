"""
Vistas de PDF para registros de Construcción.
"""

from django_weasyprint.views import WeasyTemplateView
from datetime import datetime
from reg_construccion.models import RegConstruccion
from django.conf import settings
from pathlib import Path
from django.shortcuts import render
from core.models.google_maps import GoogleMapsImage
from django.contrib.contenttypes.models import ContentType
from reg_construccion.config import PASOS_CONFIG

def convert_lat_to_dms(lat):
    if lat is None:
        return 'N/A'
    direction = 'N' if lat >= 0 else 'S'
    deg_abs = abs(lat)
    degrees = int(deg_abs)
    minutes_full = (deg_abs - degrees) * 60
    minutes = int(minutes_full)
    seconds = round((minutes_full - minutes) * 60, 2)
    return f"{direction} {degrees}° {minutes}' {seconds}''"

def convert_lon_to_dms(lon):
    if lon is None:
        return 'N/A'
    direction = 'E' if lon >= 0 else 'W'
    deg_abs = abs(lon)
    degrees = int(deg_abs)
    minutes_full = (deg_abs - degrees) * 60
    minutes = int(minutes_full)
    seconds = round((minutes_full - minutes) * 60, 2)
    return f"{direction} {degrees}° {minutes}' {seconds}''"

class RegConstruccionPDFView(WeasyTemplateView):
    template_name = 'reportes_reg_construccion/reg_construccion.html'
    pdf_options = {
        'default-font-family': 'Arial',
        'default-font-size': 12,
        'enable-local-file-access': True,
    }
    pdf_stylesheets = [str(Path(settings.BASE_DIR) / 'static/css/weasyprint.css')]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registro_id = self.kwargs.get('registro_id')

        try:
            registro = RegConstruccion.objects.select_related('sitio', 'user').get(id=registro_id)
            
            # Datos generales
            context.update({
                'registro': registro,
                'datos_generales': {
                    f'Código {registro.sitio._meta.get_field("pti_cell_id").verbose_name}:': registro.sitio.pti_cell_id,
                    f'Código {registro.sitio._meta.get_field("operator_id").verbose_name}:': registro.sitio.operator_id,
                    f'{registro.sitio._meta.get_field("name").verbose_name}:': registro.sitio.name,
                    'Latitud Mandato:': registro.sitio.lat_man,
                    'Longitud Mandato:': registro.sitio.lon_man,
                    'Latitud Ingeniería:': registro.sitio.lat_ing,
                    'Longitud Ingeniería:': registro.sitio.lon_ing,
                    'Latitud Construcción:': registro.sitio.lat_con,
                    'Longitud Construcción:': registro.sitio.lon_con,
                    f'{registro.sitio._meta.get_field("region").verbose_name}:': registro.sitio.region,
                    f'{registro.sitio._meta.get_field("comuna").verbose_name}:': registro.sitio.comuna,
                    'Empresa Contratista:': registro.contratista.name if registro.contratista else 'N/A',
                },
                'inspeccion_sitio': {
                    'Responsable ITO:': registro.user.first_name + ' ' + registro.user.last_name,
                    'Fecha de Inspección:': registro.created_at.strftime('%d/%m/%Y'),
                },
            })
            
            # Agregar datos de cada paso
            self._add_paso_data(context, registro, 'objetivo')
            self._add_paso_data(context, registro, 'avance_componente')
            self._add_paso_data(context, registro, 'imagenes')
            
        except Exception as e:
            print(f"Error en get_context_data: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return context

    def _add_paso_data(self, context, registro, paso):
        """Agrega los datos de un paso específico al contexto."""
        # Obtener el objeto del paso
        paso_obj = None
        if paso == 'objetivo':
            paso_obj = registro.objetivo_set.first()
        elif paso == 'avance_componente':
            paso_obj = registro.avancecomponentecomentarios_set.first()
            # Agregar datos de la tabla de avance por componente
            self._add_avance_componente_table_data(context, registro)
        elif paso == 'imagenes':
            # Para imágenes, no hay un modelo específico, solo fotos
            self._add_imagenes_data(context, registro)
            return
        
        if not paso_obj:
            return
        
        # Datos del paso
        paso_data = {}
        for field in paso_obj._meta.fields:
            if field.name not in ['id', 'created_at', 'updated_at', 'registro', 'is_deleted']:
                value = getattr(paso_obj, field.name)
                if value is not None and value != '':
                    paso_data[f'{field.verbose_name}:'] = str(value)
        
        context[f'registro_{paso}'] = paso_data
        
        # Mapa del paso
        registro_content_type = ContentType.objects.get_for_model(registro)
        mapa_paso = GoogleMapsImage.objects.filter(
            content_type=registro_content_type,
            object_id=registro.id,
            etapa=paso
        ).first()
        
        if mapa_paso:
            context[f'google_{paso}_image'] = {
                'src': mapa_paso.imagen.url,
                'alt': f'Mapa de {paso}',
                'caption': f'Distancia: {mapa_paso.distancia_total_metros:.0f} m' if mapa_paso.distancia_total_metros else '',
                'icon1_color': '#FF4040',
                'name1': paso.capitalize(),
            }
        else:
            context[f'google_{paso}_image'] = {'src': None}
        
        # Fotos del paso
        context[f'registro_{paso}_fotos'] = {
            'fotos': self._get_photos(registro, paso)
        }

    def _add_imagenes_data(self, context, registro):
        """Agrega los datos de imágenes al contexto."""
        context['registro_imagenes_fotos'] = {
            'fotos': self._get_photos(registro, 'imagenes')
        }

    def _add_avance_componente_table_data(self, context, registro):
        """Agrega los datos de la tabla de avance por componente al contexto."""
        from reg_construccion.models import AvanceComponente
        from proyectos.models import Componente, ComponenteGrupo
        
        # Obtener los componentes de la estructura seleccionada
        if registro.estructura:
            # Obtener todos los componentes activos de la estructura con su incidencia
            componentes_estructura = ComponenteGrupo.objects.filter(
                grupo=registro.estructura
            ).select_related('componente').order_by('orden', 'id')
            
            # Obtener avances existentes para esta estructura
            avances_existentes = AvanceComponente.objects.filter(
                registro=registro,
                componente__in=[gc.componente for gc in componentes_estructura]
            ).order_by('componente__nombre', '-fecha', '-created_at')
            
            # Crear un diccionario de avances por componente
            avances_por_componente = {}
            for avance in avances_existentes:
                if avance.componente_id not in avances_por_componente:
                    avances_por_componente[avance.componente_id] = []
                avances_por_componente[avance.componente_id].append(avance)
            
            # Generar datos de tabla
            table_data = []
            total_ejec_anterior = 0
            total_ejec_actual = 0
            total_ejec_acumulada = 0
            total_ejecucion_total = 0
            
            for gc in componentes_estructura:
                componente = gc.componente
                avances_componente = avances_por_componente.get(componente.id, [])
                
                # Calcular porcentajes de ejecución
                ejec_anterior = 0
                ejec_actual = 0
                
                if avances_componente:
                    # Obtener el avance más reciente
                    ultimo_avance = avances_componente[0]
                    ejec_actual = ultimo_avance.porcentaje_actual
                    
                    # Cada fecha es independiente - ejec_anterior es el valor guardado en esta fecha
                    ejec_anterior = ultimo_avance.porcentaje_acumulado - ultimo_avance.porcentaje_actual
                    
                    # Asegurar que no sea negativo
                    if ejec_anterior < 0:
                        ejec_anterior = 0
                else:
                    # Sin avances, todos los valores son 0
                    ejec_anterior = 0
                    ejec_actual = 0
                
                # Calcular ejecución acumulada
                ejec_acumulada = ejec_anterior + ejec_actual
                
                # Calcular ejecución total (incidencia × ejecución acumulada)
                incidencia = float(gc.incidencia)
                ejecucion_total = (incidencia / 100) * ejec_acumulada
                
                # Acumular totales
                total_ejec_anterior += ejec_anterior
                total_ejec_actual += ejec_actual
                total_ejec_acumulada += ejec_acumulada
                total_ejecucion_total += ejecucion_total
                
                row_data = {
                    'componente': componente.nombre,
                    'incidencia': f"{incidencia:.1f}%",
                    'ejec_anterior': f"{ejec_anterior}%",
                    'ejec_actual': f"{ejec_actual}%",
                    'ejec_acumulada': f"{ejec_acumulada}%",
                    'ejecucion_total': f"{ejecucion_total:.1f}%"
                }
                
                table_data.append(row_data)
            
            # Agregar totales
            context['avance_componente_table'] = {
                'table_data': table_data,
                'total_ejec_anterior': f"{total_ejec_anterior:.1f}%",
                'total_ejec_actual': f"{total_ejec_actual:.1f}%",
                'total_ejec_acumulada': f"{total_ejec_acumulada:.1f}%",
                'total_ejecucion_total': f"{total_ejecucion_total:.1f}%"
            }
            
            # Agregar datos para gráfico
            context['avance_componente_chart'] = {
                'componentes': [row['componente'] for row in table_data],
                'ejecucion_total': [float(row['ejecucion_total'].replace('%', '')) for row in table_data],
                'ejec_actual': [float(row['ejec_actual'].replace('%', '')) for row in table_data],
                'ejec_anterior': [float(row['ejec_anterior'].replace('%', '')) for row in table_data]
            }
        else:
            # Si no hay estructura seleccionada, mostrar todos los avances
            avances_componente = AvanceComponente.objects.filter(
                registro=registro
            ).order_by('componente__nombre', '-fecha', '-created_at')
            
            # Convertir a formato de tabla
            table_data = []
            for avance in avances_componente:
                row_data = {
                    'componente': avance.componente.nombre,
                    'incidencia': 'N/A',
                    'ejec_anterior': f"{avance.porcentaje_actual}%",
                    'ejec_actual': f"{avance.porcentaje_actual}%",
                    'ejec_acumulada': f"{avance.porcentaje_acumulado}%",
                    'ejecucion_total': 'N/A'
                }
                table_data.append(row_data)
            
            context['avance_componente_table'] = {
                'table_data': table_data,
                'total_ejec_anterior': 'N/A',
                'total_ejec_actual': 'N/A',
                'total_ejec_acumulada': 'N/A',
                'total_ejecucion_total': 'N/A'
            }

    def _get_photos(self, registro, etapa):
        """
        Obtiene todas las fotos relacionadas con una etapa específica.
        Para las etapas, las fotos se asocian al registro principal (RegConstruccion).
        """
        from photos.models import Photos
        from django.contrib.contenttypes.models import ContentType
        
        # Obtener el ContentType del modelo del registro principal
        registro_content_type = ContentType.objects.get_for_model(registro)
        
        # Obtener todas las fotos para este registro, etapa específica y app 'reg_construccion'
        fotos = Photos.objects.filter(
            content_type=registro_content_type,
            object_id=registro.id,
            etapa=etapa,
            app='reg_construccion'
        ).order_by('orden', '-created_at')
        
        # Convertir a formato para el template
        fotos_list = []
        for foto in fotos:
            fotos_list.append({
                'src': foto.imagen.url,
                'alt': foto.descripcion or f'Foto de {etapa} {registro.sitio.pti_cell_id}',
                'descripcion': foto.descripcion,
                'orden': foto.orden
            })
        
        return fotos_list

def preview_reg_construccion_individual(request, registro_id):
    """Vista para previsualizar el PDF de un registro de construcción."""
    view = RegConstruccionPDFView()
    view.kwargs = {'registro_id': registro_id}
    context = view.get_context_data()
    return render(request, 'reportes_reg_construccion/reg_construccion.html', context)
