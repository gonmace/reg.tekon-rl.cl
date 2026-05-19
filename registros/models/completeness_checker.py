"""
Funciones para verificar la completitud de modelos.
"""

from django.db import models
from typing import Dict, Any


def check_model_completeness(model_class, instance_id: int) -> Dict[str, Any]:
    """
    Verifica la completitud de un modelo basado en TODOS sus campos (obligatorios y opcionales).
    - paso-verde:   todos los campos tienen valor
    - paso-amarillo: algunos campos tienen valor (parcial)
    - paso-rojo:    ningún campo tiene valor, o no existe la instancia
    """
    try:
        instance = model_class.objects.get(id=instance_id)
    except model_class.DoesNotExist:
        return {
            'color': 'paso-rojo',
            'is_complete': False,
            'missing_fields': [],
            'total_fields': 0,
            'filled_fields': 0,
            'percentage': 0
        }

    field_names = [
        field.name
        for field in model_class._meta.get_fields()
        if (
            isinstance(field, models.Field)
            and not field.auto_created
            and not field.is_relation
            and field.name not in ['id', 'created_at', 'updated_at', 'is_deleted']
        )
    ]

    total_fields = len(field_names)
    filled_fields = 0
    missing_fields = []

    for field_name in field_names:
        value = getattr(instance, field_name, None)
        if value is not None and value != '':
            filled_fields += 1
        else:
            missing_fields.append(field_name)

    percentage = (filled_fields / total_fields * 100) if total_fields > 0 else 0
    is_complete = total_fields > 0 and filled_fields == total_fields

    if is_complete:
        color = 'paso-verde'
    elif filled_fields > 0:
        color = 'paso-amarillo'
    else:
        color = 'paso-rojo'

    return {
        'color': color,
        'is_complete': is_complete,
        'missing_fields': missing_fields,
        'total_fields': total_fields,
        'filled_fields': filled_fields,
        'percentage': round(percentage, 1)
    }
