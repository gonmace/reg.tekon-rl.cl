from django import template

from widgets.widget_types.form_dinamico import parse_campos

register = template.Library()


@register.simple_tag
def campos_dinamicos(campos_raw, datos):
    """
    {% campos_dinamicos campos datos as lista %}
    Parsea el DSL 'campos' e inyecta value/checked desde los datos ya guardados,
    más la ImagenEjemplo de cada campo que declare una (campo['img']).
    """
    from widgets.models import ImagenEjemplo

    datos = datos or {}
    campos = parse_campos(campos_raw or '')

    slugs = {c['imagen'] for c in campos if c['imagen']}
    imagenes = {
        img.slug: {'url': img.imagen.url, 'nombre': img.nombre, 'descripcion': img.descripcion}
        for img in ImagenEjemplo.objects.filter(slug__in=slugs)
    } if slugs else {}

    lista = []
    for campo in campos:
        campo = dict(campo)
        # dict plano (no la instancia del modelo) para que 'lista' siga siendo
        # JSON-serializable de punta a punta (se vuelca tal cual con json_script).
        campo['img'] = imagenes.get(campo['imagen'])
        # 'answered' distingue "toggle nunca guardado" de "toggle guardado en False":
        # ambos se ven igual en el DOM (checkbox sin marcar), así que el nivel de
        # completitud necesita saber si la clave llegó a existir en los datos guardados.
        campo['answered'] = campo['nombre'] in datos
        val = datos.get(campo['nombre'])
        if campo['tipo'] == 'toggle':
            campo['checked'] = bool(val)
        elif val in (None, ''):
            campo['value'] = ''
        elif isinstance(val, (int, float)):
            # Evita el formateo regional de Django (es → "4,2"), que rompe
            # <input type="number"> y el parseFloat() del lado JS.
            campo['value'] = str(val)
        else:
            campo['value'] = val
        lista.append(campo)
    return lista
