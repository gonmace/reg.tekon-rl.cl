from core.menu.menu_builder import MenuBuilder


def menu_context(request):
    return {
        'menu_items': MenuBuilder.get_menu(request.user, request.path, request),
    }
