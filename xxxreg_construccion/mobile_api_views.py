"""
Vistas específicas de la API para la aplicación móvil.
"""

from rest_framework import status, settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from datetime import date, datetime
from django.contrib.auth import authenticate

from core.models.registros import Registro
from users.models import User
from rest_framework_simplejwt.tokens import RefreshToken

from .models import RegConstruccion, AvanceComponente, AvanceComponenteComentarios, Objetivo, EjecucionPorcentajes
from .serializers import (
    RegConstruccionSerializer,
    AvanceComponenteSerializer, AvanceComponenteComentariosSerializer, ObjetivoSerializer, ComponenteSerializer
)
from core.models.sites import Site
from proyectos.models import Componente
from photos.models import Photos


def get_tokens_for_user(user):
    """Genera tokens JWT para un usuario"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sitios_activos_por_usuario(request):
    """
    1. API para listar los sitios que están activos en reg_construccion filtrados por usuario.

    GET /api/v1/mobile/sitios-activos/?user_id=<id>
    """
    user_id = request.query_params.get('user_id')

    if not user_id:
        return Response(
            {'error': 'El parámetro user_id es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user_id = int(user_id)
    except ValueError:
        return Response(
            {'error': 'user_id debe ser un número entero'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Obtener sitios únicos que tienen registros activos del usuario
    sitios_activos = Site.objects.filter(
        reg_construccion__user_id=user_id,
        reg_construccion__is_active=True
    ).distinct().values('id', 'name', 'pti_cell_id', 'operator_id')

    return Response({
        'sitios': list(sitios_activos),
        'total': sitios_activos.count()
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fechas_por_usuario(request):
    """
    2. API para mostrar la lista de las fechas que tiene el usuario

    GET /api/v1/mobile/fechas-por-usuario/?user_id=<id>
    """
    user_id = request.query_params.get('user_id')
    sitio_id = request.query_params.get('sitio_id')

    if not user_id or not sitio_id:
        return Response(
            {'error': 'El parámetro user_id y sitio_id son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        user_id = int(user_id)
        sitio_id = int(sitio_id)
    except ValueError:
        return Response(
            {'error': 'user_id debe ser un número entero'},
            status=status.HTTP_400_BAD_REQUEST
        )
    fechas = RegConstruccion.objects.filter(
        sitio_id=sitio_id, user_id=user_id, is_active=True).values('id', 'fecha')

    return Response({
        'fechas': list(fechas),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_nueva_fecha(request):
    """
    2. API para crear una nueva fecha (nuevo registro de construcción).

    POST /api/v1/mobile/crear-fecha/
    """
    try:
        # Validar datos requeridos
        required_fields = ['sitio_id', 'title', 'fecha']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'error': f'El campo {field} es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Verificar que el sitio existe
        sitio = get_object_or_404(Site, id=request.data['sitio_id'])
        ultimo_registro = RegConstruccion.objects.filter(sitio=sitio, is_active=True).order_by("-fecha").first()

        if not ultimo_registro:
            return Response(
                {'error': 'El sitio no tiene registros activos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que no existe un registro para la misma fecha, sitio y usuario
        fecha = request.data['fecha']
        registro_existente = RegConstruccion.objects.filter(
            sitio=sitio,
            user=request.user,
            fecha=fecha,
            is_active=True,
        ).first()

        if registro_existente:
            return Response(
                {'error': f'Ya existe un registro para la fecha {fecha} en este sitio'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crear el nuevo registro
        registro_data = {
            'sitio': sitio,
            'user': request.user,
            'title': request.data['title'],
            'description': request.data.get('description', ''),
            'fecha': fecha,
            'estado': request.data.get('estado', 'construccion'),
            'estructura': ultimo_registro.estructura,
        }
        registro = RegConstruccion.objects.create(**registro_data)
        serializer_data = RegConstruccionSerializer(registro).data
        print("Creamos un nuevo registro para esta fecha!!", registro)
        # aqui vamos a crear un nuevo avance por cada componente con los valores anteriores
        for componente in registro.estructura.componentes.all():
            last_avance_componente = AvanceComponente.objects.filter(
                registro=ultimo_registro,
                componente=componente.componente,
                is_deleted=False,
            ).order_by('-created_at').first()

            print("Ultimo avance del componente: ", last_avance_componente)
            if last_avance_componente:
                AvanceComponente.objects.create(
                    registro=registro,
                    componente=componente.componente,
                    porcentaje_actual=0,
                    porcentaje_acumulado=last_avance_componente.porcentaje_acumulado,
                    porcentaje_anterior=last_avance_componente.porcentaje_acumulado,
                )

        return Response(serializer_data, status=status.HTTP_200_OK)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Error al crear el registro: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def llenar_objetivo(request):
    """
    3. API para llenar el campo objetivo.

    POST /api/v1/mobile/llenar-objetivo/
    """
    try:
        # Validar datos requeridos
        if 'registro_id' not in request.data or 'objetivo' not in request.data:
            return Response(
                {'error': 'Los campos registro_id y objetivo son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        registro_id = request.data['registro_id']
        objetivo_texto = request.data['objetivo']

        # Verificar que el registro existe y pertenece al usuario
        try:
            registro = RegConstruccion.objects.get(
                id=registro_id,
                user=request.user,
                is_active=True
            )
        except RegConstruccion.DoesNotExist:
            return Response(
                {'error': 'Registro no encontrado o no tienes permisos'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Crear o actualizar el objetivo
        objetivo, created = Objetivo.objects.get_or_create(
            registro=registro,
            is_deleted=False,
            defaults={'objetivo': objetivo_texto}
        )

        if not created:
            objetivo.objetivo = objetivo_texto
            objetivo.save()

        serializer = ObjetivoSerializer(objetivo)
        return Response({
            'message': 'Objetivo guardado exitosamente',
            'objetivo': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error al guardar el objetivo: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def llenar_avance(request):
    """
    4. API para llenar el campo avance.

    POST /api/v1/mobile/llenar-avance/
    """
    try:
        print("Entrando a llenar avance", request.data)
        # Validar datos requeridos
        required_fields = ['registro_id', 'componente_id', 'porcentaje_actual']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'error': f'El campo {field} es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        registro_id = request.data['registro_id']
        componente_id = request.data['componente_id']
        porcentaje_actual = request.data['porcentaje_actual']
        comentarios = request.data.get('comentarios', '')
        fecha_avance = request.data.get('fecha', date.today())

        # Verificar que el registro existe y pertenece al usuario
        try:
            print("Obteniendo el resistro actual")
            registro = RegConstruccion.objects.get(
                id=registro_id,
                user=request.user,
                is_active=True
            )
            fecha_avance = registro.fecha
        except Exception as e:
            print("Registro no encontrado o no tienes permisos", registro_id, request.user,)
            return Response(
                {'error': 'Registro no encontrado o no tienes permisos'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar que el componente existe
        try:
            print("Obteniendo el componente actual")
            componente = Componente.objects.get(id=componente_id)
        except Componente.DoesNotExist:
            print("Componente no encontrado", componente_id)
            return Response(
                {'error': 'Componente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # vamos a calcular en base al porcentaje actual, cuanto sería el porcentaje acumulado
        # el porcentaje acumulado será el porcentaje anterior + porcentaje actual
        print("Obteniendo el avance")
        avance = AvanceComponente.objects.filter(
            registro=registro,
            componente=componente,
            is_deleted=False,
        ).order_by('-created_at').first()

        if avance:
            ultimo_avance = AvanceComponente.objects.filter(
                registro__sitio=registro.sitio,
                componente=componente,
                is_deleted=False,
            ).order_by('-created_at').first()
            avance.porcentaje_actual = porcentaje_actual
            avance.porcentaje_acumulado = ultimo_avance.porcentaje_acumulado + porcentaje_actual
            avance.porcentaje_anterior = ultimo_avance.porcentaje_acumulado
            avance.comentarios = comentarios
            avance.save()

            return Response(data=AvanceComponenteSerializer(avance).data, status=status.HTTP_200_OK)

        return Response(
            {'error': 'Avance no encontrado para este registro y este componente'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print("Error al guardar el avance:")
        return Response(
            {'error': f'Error al guardar el avance: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def llenar_tabla(request):
    """
    5. API para llenar la tabla (comentarios de avance por componente).

    POST /api/v1/mobile/llenar-tabla/
    """
    try:
        # Validar datos requeridos
        if 'registro_id' not in request.data or 'comentarios' not in request.data:
            return Response(
                {'error': 'Los campos registro_id y comentarios son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        registro_id = request.data['registro_id']
        comentarios_texto = request.data['comentarios']

        # Verificar que el registro existe y pertenece al usuario
        try:
            registro = RegConstruccion.objects.get(
                id=registro_id,
                user=request.user,
                is_active=True
            )
        except RegConstruccion.DoesNotExist:
            return Response(
                {'error': 'Registro no encontrado o no tienes permisos'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Crear o actualizar los comentarios
        comentarios_obj, created = AvanceComponenteComentarios.objects.get_or_create(
            registro=registro,
            is_deleted=False,
            defaults={'comentarios': comentarios_texto}
        )

        if not created:
            comentarios_obj.comentarios = comentarios_texto
            comentarios_obj.save()

        serializer = AvanceComponenteComentariosSerializer(comentarios_obj)
        return Response({
            'message': 'Comentarios guardados exitosamente',
            'comentarios': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error al guardar los comentarios: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subir_imagenes(request):
    """
    6. API para subir imágenes.

    POST /api/v1/mobile/subir-imagenes/
    """
    try:
        # Validar datos requeridos
        if 'registro_id' not in request.data:
            return Response(
                {'error': 'El campo registro_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        registro_id = request.data['registro_id']

        # Verificar que el registro existe y pertenece al usuario
        try:
            registro = RegConstruccion.objects.get(
                id=registro_id,
                user=request.user,
                is_active=True
            )
        except RegConstruccion.DoesNotExist:
            return Response(
                {'error': 'Registro no encontrado o no tienes permisos'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Procesar las imágenes
        imagenes_subidas = []
        files = request.FILES.getlist('imagenes')
        captions = request.data.getlist('captions')

        if not files:
            return Response(
                {'error': 'No se encontraron imágenes para subir'},
                status=status.HTTP_400_BAD_REQUEST
            )

        for imagen in files:
            # Crear el objeto Photos
            photo = Photos.objects.create(
                content_type=ContentType.objects.get_for_model(registro),
                object_id=registro.id,
                app='reg_construccion',
                etapa='imagenes',
                imagen=imagen,
                descripcion=captions.pop(0) if captions else ''
            )
            base_image_url = request.build_absolute_uri('/')[:-1]
            final_image_url = base_image_url + photo.imagen.url
            imagenes_subidas.append({
                'id': photo.id,
                'image_url': final_image_url,
                'caption': photo.descripcion,
                'uploaded_at': photo.created_at.isoformat()
            })

        print("registro: ", registro)
        print("Imagenes subidas:", imagenes_subidas)
        return Response({
            'message': f'{len(imagenes_subidas)} imágenes subidas exitosamente',
            'imagenes': imagenes_subidas
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error al subir las imágenes: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["PUT"])
def editar_imagen(request, imagen_id):
    """
    API para editar una imagen.
    """
    try:
        # Verificar que la imagen existe
        imagen = get_object_or_404(Photos, id=imagen_id)

        # Verificar que el usuario tiene permiso para editar la imagen
        registro = RegConstruccion.objects.get(
            id=imagen.object_id,
            user=request.user,
            is_active=True
        )
        # Actualizar la descripción si se proporciona
        if 'description' in request.data:
            imagen.descripcion = request.data['description']
            imagen.save()

        return Response({
            'message': 'Imagen actualizada exitosamente',
            'imagen': {
                'id': imagen.id,
                'image_url': request.build_absolute_uri(imagen.imagen.url),
                'caption': imagen.descripcion,
                'uploaded_at': imagen.created_at.isoformat()
            }
        }, status=status.HTTP_200_OK)

    except RegConstruccion.DoesNotExist:
        return Response(
            {'error': 'No tienes permisos para editar esta imagen'},
            status=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        return Response(
            {'error': f'Error al editar la imagen: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# api para obtener las imagenes
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def obtener_imagenes(request, registro_id):
    """
    Api para mostrar las imagenes de un registro.
    """
    try:
        registro = RegConstruccion.objects.get(id=registro_id)
        imagenes = Photos.objects.filter(
            content_type=ContentType.objects.get_for_model(registro),
            object_id=registro.id,
            app='reg_construccion',
            etapa='imagenes'
        ).order_by('-created_at')
        imagenes_list = []
        for imagen in imagenes:
            base_image_url = request.build_absolute_uri('/')[:-1]
            final_image_url = base_image_url + imagen.imagen.url
            imagenes_list.append({
                'id': imagen.id,
                'image_url': final_image_url,
                'caption': imagen.descripcion,
                'uploaded_at': imagen.created_at.isoformat()
            })
            print(imagenes_list)
        return Response(imagenes_list, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': f'Error al obtener las imagenes: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# hacer la api para eliminar la imagen
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def eliminar_imagen(request, imagen_id):
    try:
        imagen = get_object_or_404(Photos, id=imagen_id)
        imagen.delete()

        return Response({
            'message': 'Imagen eliminada exitosamente'
        }, status=status.HTTP_200_OK)
    except RegConstruccion.DoesNotExist:
        return Response(
            {'error': 'No tienes permisos para eliminar esta imagen'},
            status=status.HTTP_403_FORBIDDEN
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_registro_completo(request, registro_id):
    """
    API adicional para obtener un registro completo con todos sus datos.

    GET /api/v1/mobile/registro-completo/{registro_id}/
    """
    try:
        # Verificar que el registro existe y pertenece al usuario
        try:
            registro = RegConstruccion.objects.select_related(
                'sitio', 'user', 'contratista', 'estructura'
            ).prefetch_related(
                'objetivo_set', 'avancecomponente_set', 'avancecomponentecomentarios_set', 'ejecucionporcentajes_set'
            ).get(
                id=registro_id,
                user=request.user,
                is_active=True
            )
        except RegConstruccion.DoesNotExist:
            return Response(
                {'error': 'Registro no encontrado o no tienes permisos'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = RegConstruccionSerializer(registro)
        return Response(serializer.data)

    except Exception as e:
        return Response(
            {'error': f'Error al obtener el registro: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    7. API para loguearse.

    POST /api/v1/mobile/login/
    """
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    if not username:
        return Response({'error': 'El campo username es requerido'}, status=status.HTTP_400_BAD_REQUEST)
    if not password:
        return Response({'error': 'El campo password es requerido'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)
    if user is None:
        return Response({'error': 'Usuario o contraseña incorrectos'}, status=status.HTTP_401_UNAUTHORIZED)

    tokens = get_tokens_for_user(user)
    return Response({
        'message': 'Login exitoso',
        'user': user.id,
        'username': user.username,
        'tokens': tokens,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def obtener_objetivo(request, registro_id):
    """
    API para obtener el objetivo asociado a un registro específico.

    GET /api/v1/mobile/obtener-objetivo/{registro_id}/
    """
    try:
        # Verificar que el registro existe y pertenece al usuario
        try:
            registro = RegConstruccion.objects.get(
                id=registro_id,
                user=request.user,
                is_active=True
            )
        except RegConstruccion.DoesNotExist:
            return Response(
                {'error': 'Registro no encontrado o no tienes permisos'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener el objetivo asociado al registro
        try:
            print("registro: ", registro)
            objetivo, _ = Objetivo.objects.get_or_create(
                registro=registro,
                is_deleted=False
            )

            print("objetivo: ", objetivo)
            serializer = ObjetivoSerializer(objetivo)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Objetivo.DoesNotExist:
            return Response(
                {'error': 'No se encontró un objetivo para este registro'},
                status=status.HTTP_404_NOT_FOUND
            )

    except Exception as e:
        return Response(
            {'error': f'Error al obtener el objetivo: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# obtener_avance
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def obtener_avance(request, registro_id):
    """
    API para obtener el avance asociado a un registro específico.

    GET /api/v1/mobile/obtener-avance/{registro_id}/
    """
    try:
        # Verificar que el registro existe y pertenece al usuario
        try:
            registro = RegConstruccion.objects.get(
                id=registro_id,
                user=request.user,
                is_active=True
            )
        except RegConstruccion.DoesNotExist:
            return Response(
                {'error': 'Registro no encontrado o no tienes permisos'},
                status=status.HTTP_404_NOT_FOUND
            )

        print("Registro: ", registro)
        # Obtener los avances asociados al registro
        avances = AvanceComponente.objects.filter(
            registro=registro,
            is_deleted=False,
        ).order_by('-fecha')

        print("Avances: ", avances)

        if avances.exists():
            serializer = AvanceComponenteSerializer(avances, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        print("No existen avances, inferir un progreso nuevo", registro.sitio)
        # aqui vamos a cargar todos los componentes asociados a la estructura del registro con su ultimos avances
        last_registro = RegConstruccion.objects.exclude(
            id=registro.id,
        ).filter(
            sitio=registro.sitio,
            is_active=True
        ).order_by('-created_at').first()

        if not last_registro:
            # si no hay ningun registro anterior, retornamos una lista de los componentes de la estructura con valores porcentuales en 0
            componentes = registro.estructura.componentes.all()
            avances = []
            for component in componentes:
                avance = AvanceComponente(
                    registro=registro,
                    fecha=registro.fecha,
                    componente=component.componente,
                    porcentaje_actual=0,
                    porcentaje_anterior=0,
                    porcentaje_acumulado=0,
                    comentarios='',
                )
                avance.save()
                serializer = AvanceComponenteSerializer(avance)
                avances.append(serializer.data)
            print("Avances inferidos: ", avances)
            return Response(avances, status=status.HTTP_200_OK)

        print("Ultimo registro: ", last_registro)
        avances = []
        for component in last_registro.estructura.componentes.all():
            last_component_avance = AvanceComponente.objects.filter(
                registro=last_registro,
                componente=component.componente,
                is_deleted=False
            ).order_by('-fecha').first()
            print("Ultimo avance del componente: ", last_component_avance)
            if last_component_avance:
                avance = AvanceComponente(
                    registro=registro,
                    fecha=registro.fecha,
                    componente=component.componente,
                    porcentaje_actual=0,
                    porcentaje_anterior=last_component_avance.porcentaje_actual,
                    porcentaje_acumulado=last_component_avance.porcentaje_acumulado,
                    comentarios=last_component_avance.comentarios,
                )
                avance.save()
                serializer = AvanceComponenteSerializer(avance)
                avances.append(serializer.data)

        print("Avances inferidos: ", avances)
        return Response(avances, status=status.HTTP_200_OK)
    except Exception as e:
        from traceback import print_exc
        print_exc()
        return Response(
            {'error': f'Error al obtener los avances: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# obtener_tabla
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def obtener_tabla(request, registro_id):
    """
    API para obtener los comentarios asociados a un registro específico.

    GET /api/v1/mobile/obtener-tabla/{registro_id}/
    """
    try:
        # Verificar que el registro existe y pertenece al usuario
        try:
            registro = RegConstruccion.objects.get(
                id=registro_id,
                user=request.user,
                is_active=True
            )
        except RegConstruccion.DoesNotExist:
            return Response(
                {'error': 'Registro no encontrado o no tienes permisos'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener los comentarios asociados al registro
        try:
            comentarios = AvanceComponenteComentarios.objects.get(
                registro=registro,
                is_deleted=False
            )
            serializer = AvanceComponenteComentariosSerializer(comentarios)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except AvanceComponenteComentarios.DoesNotExist:
            return Response(
                {'error': 'No se encontraron comentarios para este registro'},
                status=status.HTTP_404_NOT_FOUND
            )

    except Exception as e:
        return Response(
            {'error': f'Error al obtener los comentarios: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
