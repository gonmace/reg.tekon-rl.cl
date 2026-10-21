"""
Registro de modelos de registro (RegTxtss, RegConstruccion, ...) por namespace de URLs.

Cada app llama a `register_registro_model('<namespace>', Model)` en `AppConfig.ready()`.
El namespace coincide con el prefijo de URL de la app (/reg_txtss/, /reg_construccion/).
Permite a `photos` y a las vistas genéricas resolver el modelo sin acoplarse a uno concreto.
"""

_MODELS = {}
DEFAULT_NAMESPACE = 'reg_txtss'


def register_registro_model(namespace, model):
    _MODELS[namespace] = model


def get_registro_model(namespace):
    return _MODELS.get(namespace)


def all_registro_models():
    return list(_MODELS.values())


def namespace_from_request(request):
    """Namespace registrado al que pertenece la request (por resolver_match o por path)."""
    match = getattr(request, 'resolver_match', None)
    if match:
        for ns in match.namespaces:
            if ns in _MODELS:
                return ns
    first = (request.path.strip('/').split('/') or [''])[0]
    return first if first in _MODELS else None


def model_from_request(request):
    """Modelo de registro de la request; sin pista, el de TX/TSS (compatibilidad)."""
    ns = namespace_from_request(request) if request is not None else None
    return _MODELS.get(ns or DEFAULT_NAMESPACE)
