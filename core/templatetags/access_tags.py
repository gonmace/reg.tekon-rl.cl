from django import template

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


class _RoleNode(template.Node):
    def __init__(self, nodelist, roles):
        self.nodelist, self.roles = nodelist, roles

    def render(self, context):
        user = _get_user(context)
        if user and user.is_authenticated and (user.is_supermanager or user.user_type in self.roles):
            return self.nodelist.render(context)
        return ''


@register.tag('for_role')
def do_for_role(parser, token):
    """Visible para los roles indicados (y siempre para superusuario).
    Uso: {% for_role 'COORD' 'ADMINISTRADOR' %}...{% endfor_role %}"""
    bits = token.split_contents()
    roles = [r.strip("'\"") for r in bits[1:]]
    nodelist = parser.parse(('endfor_role',))
    parser.delete_first_token()
    return _RoleNode(nodelist, roles)


@register.simple_tag(takes_context=True)
def btn_access(context):
    """Devuelve 'allowed', 'disabled' o 'hidden' según el rol del usuario.
    Uso: {% btn_access as access %} o data-access="{% btn_access %}"
    - VISITA           → hidden   (botón oculto)
    - Registro concluido (`bloqueado` en el contexto) → disabled para todos
    - COORD / ADMINISTRADOR → disabled (visible pero inactivo), salvo que la vista indique
      `puede_escribir` en el contexto (Construcción: la vista decide quién guarda)
    - ITO / SEARCHER / Supermanager → allowed
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
    if u.is_coord or u.is_administrador:
        return 'disabled'
    return 'allowed'
