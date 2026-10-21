def can_hijack(*, hijacker, hijacked):
    """Solo is_superuser de Django puede impersonar, y nunca a otro superuser."""
    return bool(
        hijacker.is_superuser
        and not hijacked.is_superuser
        and hijacked.is_active
        and not hijacked.is_deleted
    )
