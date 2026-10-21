from django import forms

from users.models import User

from .models import RegConstruccion


def _etiqueta_usuario(u):
    return f'{u.get_full_name} ({u.username})' if u.first_name else u.username


class RegConstruccionEditForm(forms.ModelForm):
    """Datos de cabecera de la visita.

    `cambiar_ito` (superusuario y ADMINISTRADOR) agrega el campo `user` para
    reasignar la visita; el ADMINISTRADOR solo ve ese campo (no gestiona la cabecera).
    """

    class Meta:
        model = RegConstruccion
        fields = ['fecha', 'revision', 'estado_obra']
        widgets = {'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}

    def __init__(self, *args, cambiar_ito=False, solo_ito=False, **kwargs):
        super().__init__(*args, **kwargs)
        if solo_ito:
            for name in list(self.fields):
                del self.fields[name]
        if cambiar_ito:
            self.fields['user'] = forms.ModelChoiceField(
                label='ITO / Buscador', required=False, empty_label='Sin asignar',
                queryset=User.objects.filter(
                    user_type__in=User.ITO_LIKE_ROLES, is_active=True, is_deleted=False,
                ).order_by('first_name', 'last_name', 'username'),
                initial=self.instance.user_id,
            )
            self.fields['user'].label_from_instance = _etiqueta_usuario
            self.order_fields(['user'])
        for field in self.fields.values():
            css = 'select select-bordered w-full' if isinstance(field.widget, forms.Select) \
                else 'input input-bordered w-full'
            field.widget.attrs.setdefault('class', css)

    def _post_clean(self):
        # `user` no es un campo del Meta: se asigna a mano antes de validar el modelo.
        if 'user' in self.fields and 'user' in self.cleaned_data:
            self.instance.user = self.cleaned_data['user']
        super()._post_clean()

