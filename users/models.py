from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    ADMINISTRADOR = "ADMINISTRADOR"
    ITO = "ITO"
    SEARCHER = "SEARCHER"
    VISITA = "VISITA"

    # Roles con privilegios equivalentes al ITO
    ITO_LIKE_ROLES = (ITO, SEARCHER)

    # Roles que requieren configuración explícita de acceso a reportes
    RESTRICTED_ROLES = (ADMINISTRADOR, ITO, SEARCHER, VISITA)

    TYPE_CHOICES = [
        (ADMINISTRADOR, "Administrador"),
        (ITO, "ITO"),
        (SEARCHER, "Buscador"),
        (VISITA, "Visita"),
    ]

    REPORT_ACCESS_CHOICES = [
        ('txtss_postes',  'TX/TSS Postes'),
        ('txtss_torres',  'TX/TSS Ingenieria'),
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
        if not self.user_type and self.contractor_id:
            raise ValidationError({'contractor': 'El superusuario no puede pertenecer a una empresa.'})
        if self.user_type and self.user_type != self.ADMINISTRADOR and not self.contractor_id:
            raise ValidationError({'contractor': 'Este rol debe pertenecer a una empresa.'})

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

    @property
    def display_name(self):
        """Nombre para mostrar en la interfaz: nombre y apellido; si no los tiene, el usuario."""
        return self.get_full_name.strip() or self.username

    @property
    def iniciales(self):
        """Iniciales del avatar: nombre + apellido (o las 2 primeras letras del usuario)."""
        partes = [p for p in (self.first_name, self.last_name) if p and p.strip()]
        return ''.join(p.strip()[0] for p in partes[:2]).upper() or self.username[:2].upper()

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
        if not self.user_type or self.is_admin_global:
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
    def is_administrador(self):
        return self.user_type == User.ADMINISTRADOR

    @property
    def is_admin_global(self):
        """ADMINISTRADOR sin empresa: ve y administra todas las empresas."""
        return self.user_type == User.ADMINISTRADOR and not self.contractor_id

    @property
    def is_admin_empresa(self):
        """ADMINISTRADOR con empresa: limitado a los datos de su empresa."""
        return self.user_type == User.ADMINISTRADOR and bool(self.contractor_id)

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

    @property
    def is_supermanager(self):
        """Sin rol asignado = superusuario."""
        return self.user_type == ''

    @property
    def get_user_type(self):
        if not self.user_type:
            return 'Superusuario'
        return dict(User.TYPE_CHOICES).get(self.user_type, self.user_type)
