"""
Genera datos de prueba (junk data) marcados con prefijo TEST_ para revisar el aspecto visual.

Uso:
    python manage.py seed_test_data
    python manage.py seed_test_data --sites 30 --regs 80
"""

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models.sites import Site
from core.models.contractors import Contractor
from users.models import User


REGIONES = ['Antofagasta', 'Atacama', 'Coquimbo', 'Valparaíso', 'Metropolitana',
            'O\'Higgins', 'Maule', 'Biobío', 'Araucanía', 'Los Lagos']
COMUNAS = ['Calama', 'Copiapó', 'La Serena', 'Viña del Mar', 'Santiago',
           'Rancagua', 'Talca', 'Concepción', 'Temuco', 'Puerto Montt']
NOMBRES = ['Andrés', 'María', 'Juan', 'Sofía', 'Diego', 'Camila', 'Pedro',
           'Valentina', 'Felipe', 'Antonia', 'Matías', 'Florencia']
APELLIDOS = ['González', 'Rojas', 'Muñoz', 'Pérez', 'Soto', 'Contreras',
             'Silva', 'Reyes', 'Castro', 'Vargas']


class Command(BaseCommand):
    help = 'Genera datos de prueba marcados con prefijo TEST_'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=8)
        parser.add_argument('--contractors', type=int, default=6)
        parser.add_argument('--sites', type=int, default=20)
        parser.add_argument('--regs', type=int, default=40)

    @transaction.atomic
    def handle(self, *args, **opts):
        users = self._seed_users(opts['users'])
        contractors = self._seed_contractors(opts['contractors'])
        sites = self._seed_sites(opts['sites'])

        self.stdout.write(self.style.SUCCESS(
            f"\nListo: {len(users)} usuarios, {len(contractors)} contratistas, "
            f"{len(sites)} sitios."
        ))

    def _seed_users(self, n):
        users = []
        for i in range(n):
            nombre = random.choice(NOMBRES)
            apellido = random.choice(APELLIDOS)
            username = f'test_user_{i+1:03d}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@test.local',
                    'first_name': nombre,
                    'last_name': apellido,
                    'user_type': random.choice(['GERENCIA', 'COORD', 'ITO', 'SEARCHER', 'VISITA']),
                    'phone': f'+56 9 {random.randint(1000, 9999)} {random.randint(1000, 9999)}',
                    'is_active': True,
                },
            )
            if created:
                user.set_password('test1234')
                user.save()
            users.append(user)
        self.stdout.write(f"  Usuarios: {len(users)}")
        return users

    def _seed_contractors(self, n):
        contractors = []
        nombres_empresa = ['Constructora Andes', 'Ingeniería Pacífico', 'Obras del Sur',
                           'Estructuras Norte', 'TecnoCivil', 'IngeMontaje',
                           'Construcciones Bío', 'Infra Atacama']
        for i in range(n):
            code = f'TEST{i+1:03d}'
            contractor, _ = Contractor.objects.get_or_create(
                code=code,
                defaults={
                    'name': f'TEST_{nombres_empresa[i % len(nombres_empresa)]} {i+1}',
                    'is_active': random.choice([True, True, True, False]),
                },
            )
            contractors.append(contractor)
        self.stdout.write(f"  Contratistas: {len(contractors)}")
        return contractors

    def _seed_sites(self, n):
        sites = []
        for i in range(n):
            name = f'TEST_Sitio_{i+1:03d}'
            # Solo coords de Mandato (las de Ingeniería/Construcción se cargan luego)
            base_lat = -33.0 - (i * 0.01) - random.random() * 0.001
            base_lon = -70.0 - (i * 0.01) - random.random() * 0.001
            site, _ = Site.objects.get_or_create(
                name=name,
                defaults={
                    'pti_cell_id': f'TEST_PTI_{i+1:04d}',
                    'operator_id': f'TEST_OP_{i+1:04d}',
                    'lat_man': base_lat,
                    'lon_man': base_lon,
                    'alt': random.randint(0, 4500),
                    'region': random.choice(REGIONES),
                    'comuna': random.choice(COMUNAS),
                    'is_deleted': False,
                },
            )
            sites.append(site)
        self.stdout.write(f"  Sitios: {len(sites)}")
        return sites

