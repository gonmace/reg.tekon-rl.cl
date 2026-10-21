import re

from django import forms
from django.contrib.auth.forms import SetPasswordForm


class PerfilContrasenaForm(SetPasswordForm):
    """Pantalla del enlace de contraseña.

    Un usuario invitado aún no tiene contraseña (`has_usable_password()` es False): además de
    elegirla debe completar su nombre, apellido y teléfono. Quien ya tiene contraseña (olvidó la
    suya) solo la cambia.
    """
    first_name = forms.CharField(label='Nombre', max_length=150)
    last_name = forms.CharField(label='Apellido', max_length=150)
    phone = forms.CharField(label='Teléfono', max_length=20)

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.pide_perfil = not user.has_usable_password()
        if self.pide_perfil:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['phone'].initial = user.phone or ''
            self.order_fields(['first_name', 'last_name', 'phone', 'new_password1', 'new_password2'])
        else:
            for campo in ('first_name', 'last_name', 'phone'):
                del self.fields[campo]

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if len(re.sub(r'\D', '', phone)) < 8 or not re.fullmatch(r'[+\d][\d\s().-]*', phone):
            raise forms.ValidationError('Ingresa un teléfono válido (ej: +56 9 1234 5678).')
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.pide_perfil:
            user.first_name = self.cleaned_data['first_name'].strip()
            user.last_name = self.cleaned_data['last_name'].strip()
            user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
        return user
