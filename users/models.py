from django.db import models

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
# from core.permissions import ROLE_PERMISSIONS


class User(AbstractUser):
    COORD = "COORD"
    GERENCIA = "GERENCIA"
    ITO = "ITO"
    SEARCHER = "SEARCHER"
    VISITA = "VISITA"

    # Roles con privilegios equivalentes al ITO
    ITO_LIKE_ROLES = (ITO, SEARCHER)

    # Roles que requieren configuración explícita de acceso a reportes
    RESTRICTED_ROLES = (ITO, SEARCHER, COORD, VISITA)

    TYPE_CHOICES = [
        (GERENCIA, "Gerencia"),
        (COORD, "Coordinador"),
        (ITO, "ITO"),
        (SEARCHER, "Buscador"),
        (VISITA, "Visita"),
    ]

    REPORT_ACCESS_CHOICES = [
        ('txtss_postes',  'TX/TSS Postes'),
        ('txtss_torres',  'TX/TSS Torres'),
        ('construccion',  'Construcción'),
    ]
    user_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default=ITO,
        blank=True,
        verbose_name="Tipo de Usuario",
    )
    contractor = models.ForeignKey(
        'core.Contractor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Empresa',
        related_name='users',
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Registro"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Última Actualización"
    )

    is_deleted = models.BooleanField(default=False)

    report_access = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Acceso a Reportes',
        help_text='Lista de reportes permitidos. Vacío = acceso total.',
    )

    # Add related_name to resolve reverse accessor conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    # Variable para almacenar los campos modificados
    _original_state = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_state = self._get_current_state()

    def _get_current_state(self):
        """Obtiene el estado actual del modelo"""
        state = {}
        for field in self._meta.fields:
            state[field.name] = getattr(self, field.name)
        return state

    def get_dirty_fields(self):
        """Obtiene los campos que han sido modificados"""
        if not self._original_state:
            return {}

        dirty_fields = {}
        for field_name, original_value in self._original_state.items():
            current_value = getattr(self, field_name)
            if original_value != current_value:
                dirty_fields[field_name] = current_value

        return dirty_fields

    def clean(self):
        super().clean()
        if self.user_type and not self.contractor_id:
            raise ValidationError({'contractor': 'Los usuarios con rol asignado deben pertenecer a una empresa.'})

    def save(self, *args, **kwargs):
        """Guarda el modelo y actualiza el estado original"""
        super().save(*args, **kwargs)
        self._original_state = self._get_current_state()

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    @staticmethod
    def get_users():
        return User.objects.filter(is_active=True)

    @staticmethod
    def get_shearchers():
        return User.objects.filter(
            is_active=True, is_deleted=False, user_type=User.SEARCHER
        )

    @staticmethod
    def get_table(user=None):
        return {
            "title": "Información de Usuario",
            "columns": [
                {"type": "text", "label": "Nombre", "key": "get_full_name"},
                {"type": "text", "label": "Correo Electrónico", "key": "username"},
                {"type": "text", "label": "Tipo de Usuario", "key": "user_type"},
                {"type": "text", "label": "Empresa", "key": "company"},
                {
                    "type": "date",
                    "label": "Última Actualización",
                    "key": "updated_at",
                    "format": "d/m/Y H:i A",
                },
            ],
            "create_url": "users:create",
            "create_text": "Crear Usuario",
            "searchable": True,
            "filters": ["username", "email", "user_type__name", "company__name"],
            "order_by": ["created_at", "username"],
            "actions": [
                {"type": "edit", "url_name": "users:update", "url_args": "pk"},
                {"type": "delete", "url_name": "users:delete", "url_args": "pk"},
            ],
        }

    def has_report_access(self, report_code):
        """True si el usuario puede ver el reporte. Vacío = acceso total."""
        if not self.user_type or self.user_type == self.GERENCIA:
            return True
        access = self.report_access or []
        return len(access) == 0 or report_code in access

    def soft_delete(self):
        self.is_active = False
        self.is_deleted = True
        self.save()

    @staticmethod
    def get_active_users():
        return User.objects.filter(is_active=True, is_deleted=False).exclude(user_type='')

    @property
    def is_coord(self):
        return self.user_type == User.COORD

    @property
    def is_gerencia(self):
        return self.user_type == User.GERENCIA

    @property
    def is_manager(self):
        return self.is_gerencia

    @property
    def is_ito(self):
        return self.user_type == User.ITO

    @property
    def is_searcher(self):
        return self.user_type == User.SEARCHER

    @property
    def is_ito_like(self):
        """Roles con privilegios de ITO (ITO + Buscador)."""
        return self.user_type in User.ITO_LIKE_ROLES

    @property
    def is_visita(self):
        return self.user_type == User.VISITA

    @property
    def is_limited(self):
        """ITO, Buscador y Visita: acceso restringido al sistema."""
        return self.user_type in (User.ITO, User.SEARCHER, User.VISITA)

    # Compat: mantener is_admin como sinónimo de is_coord (Coord reemplazó a Admin)
    @property
    def is_admin(self):
        return self.user_type == User.COORD

    @property
    def is_superuser_type(self):
        """Usuario sin rol asignado = superusuario, no visible en listas."""
        return self.user_type == ''

    @property
    def get_user_type(self):
        if not self.user_type:
            return 'Superusuario'
        return dict(User.TYPE_CHOICES).get(self.user_type, self.user_type)

    # def get_role_permissions(self):
    #     """Obtiene los permisos asociados al rol del usuario"""
    #     return ROLE_PERMISSIONS.get(self.user_type, [])

    # def has_role_permission(self, permission):
    #     """Verifica si el usuario tiene un permiso específico de su rol"""
    #     return permission in self.get_role_permissions()


# @receiver(post_save, sender=User)
# def assign_role_permissions(sender, instance, created, **kwargs):
#     """
#     Asigna automáticamente los permisos según el rol del usuario
#     """
#     if created or "user_type" in instance.get_dirty_fields():
#         # Obtener los permisos del rol
#         role_permissions = ROLE_PERMISSIONS.get(instance.user_type, [])

#         # Asignar los permisos al usuario
#         for permission in role_permissions:
#             app_label, codename = permission.split(".")
#             from django.contrib.auth.models import Permission

#             try:
#                 perm = Permission.objects.get(
#                     codename=codename, content_type__app_label=app_label
#                 )
#                 instance.user_permissions.add(perm)
#             except Permission.DoesNotExist:
#                 pass

