import json

from django import forms


class JSONListField(forms.CharField):
    """Campo oculto cuyo valor es una lista JSON (la arma el JS del widget)."""

    widget = forms.HiddenInput

    def __init__(self, *args, max_items=200, **kwargs):
        kwargs.setdefault('required', False)
        self.max_items = max_items
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value in (None, ''):
            return []
        if isinstance(value, list):
            data = value
        else:
            try:
                data = json.loads(value)
            except (TypeError, ValueError):
                raise forms.ValidationError('Formato inválido.')
        if not isinstance(data, list):
            raise forms.ValidationError('Se esperaba una lista.')
        if len(data) > self.max_items:
            raise forms.ValidationError(f'Máximo {self.max_items} elementos.')
        return self.clean_items(data)

    def clean_items(self, data):
        return data

    def prepare_value(self, value):
        if isinstance(value, list):
            return json.dumps(value, ensure_ascii=False)
        return value

    def has_changed(self, initial, data):
        return True


class TextListField(JSONListField):
    """Lista de textos: recorta, descarta vacíos y limita la longitud."""

    def clean_items(self, data):
        items = []
        for item in data:
            if not isinstance(item, str):
                raise forms.ValidationError('Cada elemento debe ser texto.')
            item = item.strip()
            if item:
                if len(item) > 1000:
                    raise forms.ValidationError('Un elemento supera los 1000 caracteres.')
                items.append(item)
        return items
