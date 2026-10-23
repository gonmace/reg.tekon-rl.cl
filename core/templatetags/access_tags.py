from django import template

from core.permissions import puede_editar_sitios_empresas, tiene_permiso

register = template.Library()


def _get_user(context):
    req = context.get('request')
    return req.user if req and hasattr(req, 'user') else None


class _ConditionalNode(template.Node):
    def __init__(self, nodelist, check):
        self.nodelist, self.check = nodelist, check

    def render(self, context):
        user = _get_user(context)
        if user and user.is_authenticated and self.check(user):
            return self.nodelist.render(context)
        return ''


@register.tag('editable')
def do_editable(parser, token):
    """Visible para todos excepto VISITA. Ver ROLES.md.
    Uso: {% editable %}...{% endeditable %}"""
    nodelist = parser.parse(('endeditable',))
    parser.delete_first_token()
    return _ConditionalNode(nodelist, lambda u: not u.is_visita)


@register.tag('supermanager_only')
def do_supermanager_only(parser, token):
    """Visible solo para el superusuario (sin empresa). Ver ROLES.md.
    Uso: {% supermanager_only %}...{% endsupermanager_only %}"""
    nodelist = parser.parse(('endsupermanager_only',))
    parser.delete_first_token()
    return _ConditionalNode(nodelist, lambda u: u.is_supermanager)


class _PermisoNode(template.Node):
    def __init__(self, nodelist, accion):
        self.nodelist, self.accion = nodelist, accion

    def render(self, context):
        if tiene_permiso(_get_user(context), self.accion):
            return self.nodelist.render(context)
        return ''


@register.tag('con_permiso')
def do_con_permiso(parser, token):
    """Visible para quien tiene el permiso `accion` (ver core/permisos_catalogo.py).
    Uso: {% con_permiso 'activar_registro' %}...{% endcon_permiso %}"""
    bits = token.split_contents()
    if len(bits) != 2:
        raise template.TemplateSyntaxError("con_permiso requiere el nombre de la acción")
    nodelist = parser.parse(('endcon_permiso',))
    parser.delete_first_token()
    return _PermisoNode(nodelist, bits[1].strip("'\""))


@register.tag('editor_sitios')
def do_editor_sitios(parser, token):
    """Visible para quien puede editar Sitios y Empresas (superusuario y administrador global).
    Uso: {% editor_sitios %}...{% endeditor_sitios %}"""
    nodelist = parser.parse(('endeditor_sitios',))
    parser.delete_first_token()
    return _ConditionalNode(nodelist, puede_editar_sitios_empresas)


@register.simple_tag(takes_context=True)
def permiso(context, accion):
    """True si el usuario tiene el permiso. Uso: {% permiso 'concluir' as puede %}"""
    return tiene_permiso(_get_user(context), accion)


@register.simple_tag(takes_context=True)
def btn_access(context):
    """Devuelve 'allowed', 'disabled' o 'hidden' según el usuario.
    Uso: {% btn_access as access %} o data-access="{% btn_access %}"
    - VISITA           → hidden   (botón oculto)
    - Registro concluido (`bloqueado` en el contexto) → disabled para todos
    - Si la vista indica `puede_escribir` en el contexto, esa decisión manda
    - Si no: permiso `cargar_datos` → allowed; sin él → disabled
    Ver ROLES.md."""
    u = _get_user(context)
    if not u or not u.is_authenticated:
        return 'hidden'
    if u.is_visita:
        return 'hidden'
    if context.get('bloqueado'):
        return 'disabled'
    puede_escribir = context.get('puede_escribir')
    if puede_escribir is not None:
        return 'allowed' if puede_escribir else 'disabled'
    return 'allowed' if tiene_permiso(u, 'cargar_datos') else 'disabled'
