"""
Formularios para registros TX/TSS.
"""

from django import forms

from .models import ALTERNATIVA_CHOICES


class RegTxtssAdminEditForm(forms.Form):
    """Validación del formulario de edición (superusuario): responsable y
    alternativa de un registro. Antes se parseaba `request.POST` a mano y se
    aceptaba cualquier `user_id`; aquí se valida que el usuario sea ITO/Buscador
    activo y que la alternativa sea una opción válida."""

    user = forms.ModelChoiceField(queryset=None, required=False)
    alternativa = forms.ChoiceField(
        choices=[('', '---------')] + list(ALTERNATIVA_CHOICES),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from users.models import User
        self.fields['user'].queryset = User.objects.filter(
            user_type__in=User.ITO_LIKE_ROLES, is_active=True, is_deleted=False
        ).order_by('first_name', 'last_name', 'username')
