"""
Comando para hacer backup y restaurar datos importantes del sistema.
Uso:
    python manage.py backup_restore_data --action=backup --output=backup_data.json
    python manage.py backup_restore_data --action=restore --input=backup_data.json
"""

import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from users.models import User
from core.models.sites import Site
from reg_txtss.models import RegTxtss
from photos.models import Photos


class Command(BaseCommand):
    help = 'Backup y restauración de datos importantes del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['backup', 'restore'],
            required=True,
            help='Acción a realizar: backup o restore'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Archivo de salida para backup (ej: backup_data.json)'
        )
        parser.add_argument(
            '--input',
            type=str,
            help='Archivo de entrada para restore (ej: backup_data.json)'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'backup':
            self.backup_data(options['output'])
        elif action == 'restore':
            self.restore_data(options['input'])

    def backup_data(self, output_file):
        """Exporta datos importantes a un archivo JSON"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'backup_data_{timestamp}.json'
        
        self.stdout.write(f'Iniciando backup de datos a {output_file}...')
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'users': [],
            'sites': [],
            'reg_txtss': [],
            'photos': [],
        }
        
        # Backup de usuarios
        self.stdout.write('Exportando usuarios...')
        users = User.objects.all()
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
                'phone': user.phone,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_deleted': user.is_deleted,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None,
                # Importante: No incluimos la contraseña por seguridad
                # Las contraseñas se mantendrán en la base de datos original
            }
            backup_data['users'].append(user_data)
        
        # Backup de sitios
        self.stdout.write('Exportando sitios...')
        sites = Site.objects.all()
        for site in sites:
            site_data = {
                'id': site.id,
                'name': site.name,
                'operator_id': getattr(site, 'operator_id', None),
                'pti_cell_id': getattr(site, 'pti_cell_id', None),
                'latitude': getattr(site, 'latitude', None),
                'longitude': getattr(site, 'longitude', None),
                'coordinates_gms': getattr(site, 'coordinates_gms', None),
                'is_active': getattr(site, 'is_active', True),
                'created_at': site.created_at.isoformat() if hasattr(site, 'created_at') and site.created_at else None,
                'updated_at': site.updated_at.isoformat() if hasattr(site, 'updated_at') and site.updated_at else None,
            }
            backup_data['sites'].append(site_data)
        
        # Backup de registros TXTSS
        self.stdout.write('Exportando registros TXTSS...')
        try:
            reg_txtss = RegTxtss.objects.all()
            for reg in reg_txtss:
                reg_data = {
                    'id': reg.id,
                    'sitio_id': reg.sitio.id if reg.sitio else None,
                    'user_id': reg.user.id if reg.user else None,
                    'fecha': reg.fecha.isoformat() if hasattr(reg, 'fecha') and reg.fecha else None,
                    'is_active': reg.is_active,
                    'is_deleted': reg.is_deleted,
                    'created_at': reg.created_at.isoformat() if reg.created_at else None,
                    'updated_at': reg.updated_at.isoformat() if reg.updated_at else None,
                }
                backup_data['reg_txtss'].append(reg_data)
        except Exception as e:
            self.stdout.write(f'Advertencia: No se pudieron exportar registros TXTSS: {e}')
        
        # Backup de fotos
        self.stdout.write('Exportando fotos...')
        photos = Photos.objects.all()
        for photo in photos:
            photo_data = {
                'id': photo.id,
                'imagen': str(photo.imagen) if photo.imagen else None,
                'descripcion': photo.descripcion,
                'app': photo.app,
                'etapa': photo.etapa,
                'orden': photo.orden,
                'content_type_id': photo.content_type_id,
                'object_id': photo.object_id,
                'created_at': photo.created_at.isoformat() if hasattr(photo, 'created_at') and photo.created_at else None,
            }
            backup_data['photos'].append(photo_data)
        
        # Guardar archivo de backup
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Backup completado exitosamente!\n'
                f'Archivo: {output_file}\n'
                f'Usuarios: {len(backup_data["users"])}\n'
                f'Sitios: {len(backup_data["sites"])}\n'
                f'Registros TXTSS: {len(backup_data["reg_txtss"])}\n'
                f'Fotos: {len(backup_data["photos"])}'
            )
        )

    def restore_data(self, input_file):
        """Restaura datos desde un archivo JSON"""
        if not input_file:
            raise CommandError('Debe especificar un archivo de entrada con --input')
        
        if not os.path.exists(input_file):
            raise CommandError(f'El archivo {input_file} no existe')
        
        self.stdout.write(f'Iniciando restauración desde {input_file}...')
        
        with open(input_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        with transaction.atomic():
            # Restaurar usuarios
            self.stdout.write('Restaurando usuarios...')
            for user_data in backup_data['users']:
                try:
                    user, created = User.objects.get_or_create(
                        id=user_data['id'],
                        defaults={
                            'username': user_data['username'],
                            'email': user_data['email'],
                            'first_name': user_data['first_name'],
                            'last_name': user_data['last_name'],
                            'user_type': user_data.get('user_type', 'ITO'),
                            'phone': user_data.get('phone', ''),
                            'is_active': user_data['is_active'],
                            'is_staff': user_data['is_staff'],
                            'is_superuser': user_data['is_superuser'],
                            'is_deleted': user_data.get('is_deleted', False),
                        }
                    )
                    
                    # Si el usuario ya existe, actualizar campos importantes
                    if not created:
                        user.email = user_data['email']
                        user.first_name = user_data['first_name']
                        user.last_name = user_data['last_name']
                        user.user_type = user_data.get('user_type', 'ITO')
                        user.phone = user_data.get('phone', '')
                        user.is_active = user_data['is_active']
                        user.is_staff = user_data['is_staff']
                        user.is_superuser = user_data['is_superuser']
                        user.is_deleted = user_data.get('is_deleted', False)
                        user.save()
                        self.stdout.write(f'  Usuario actualizado: {user.username}')
                    else:
                        self.stdout.write(f'  Usuario creado: {user.username}')
                        
                except Exception as e:
                    self.stdout.write(f'  Error restaurando usuario {user_data["username"]}: {e}')
            
            # Restaurar sitios
            self.stdout.write('Restaurando sitios...')
            for site_data in backup_data['sites']:
                site, created = Site.objects.get_or_create(
                    id=site_data['id'],
                    defaults={
                        'name': site_data['name'],
                        'operator_id': site_data.get('operator_id'),
                        'pti_cell_id': site_data.get('pti_cell_id'),
                        'latitude': site_data.get('latitude'),
                        'longitude': site_data.get('longitude'),
                        'coordinates_gms': site_data.get('coordinates_gms'),
                        'is_active': site_data.get('is_active', True),
                    }
                )
                if created:
                    self.stdout.write(f'  Sitio creado: {site.name}')
                else:
                    self.stdout.write(f'  Sitio existente: {site.name}')
            
            # Restaurar registros TXTSS
            self.stdout.write('Restaurando registros TXTSS...')
            for reg_data in backup_data['reg_txtss']:
                try:
                    sitio = Site.objects.get(id=reg_data['sitio_id']) if reg_data['sitio_id'] else None
                    user = User.objects.get(id=reg_data['user_id']) if reg_data['user_id'] else None
                    
                    reg, created = RegTxtss.objects.get_or_create(
                        id=reg_data['id'],
                        defaults={
                            'sitio': sitio,
                            'user': user,
                            'fecha': reg_data['fecha'] if reg_data['fecha'] else None,
                            'is_active': reg_data['is_active'],
                            'is_deleted': reg_data['is_deleted'],
                        }
                    )
                    if created:
                        self.stdout.write(f'  Registro TXTSS creado: {reg.id}')
                    else:
                        self.stdout.write(f'  Registro TXTSS existente: {reg.id}')
                except Exception as e:
                    self.stdout.write(f'  Error restaurando registro TXTSS {reg_data["id"]}: {e}')
            
            # Restaurar fotos
            self.stdout.write('Restaurando fotos...')
            for photo_data in backup_data['photos']:
                try:
                    photo, created = Photos.objects.get_or_create(
                        id=photo_data['id'],
                        defaults={
                            'imagen': photo_data['imagen'],
                            'descripcion': photo_data['descripcion'],
                            'app': photo_data['app'],
                            'etapa': photo_data['etapa'],
                            'orden': photo_data['orden'],
                            'content_type_id': photo_data['content_type_id'],
                            'object_id': photo_data['object_id'],
                        }
                    )
                    if created:
                        self.stdout.write(f'  Foto creada: {photo.id}')
                    else:
                        self.stdout.write(f'  Foto existente: {photo.id}')
                except Exception as e:
                    self.stdout.write(f'  Error restaurando foto {photo_data["id"]}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Restauración completada exitosamente!\n'
                f'Archivo: {input_file}\n'
                f'Timestamp original: {backup_data.get("timestamp", "N/A")}'
            )
        ) 