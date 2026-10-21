import logging

from django.dispatch import receiver
from hijack.signals import hijack_ended, hijack_started

logger = logging.getLogger('users.hijack')


@receiver(hijack_started)
def log_hijack_started(sender, hijacker, hijacked, request, **kwargs):
    logger.info('HIJACK start: %s (id=%s) -> %s (id=%s)',
                hijacker.username, hijacker.pk, hijacked.username, hijacked.pk)


@receiver(hijack_ended)
def log_hijack_ended(sender, hijacker, hijacked, request, **kwargs):
    logger.info('HIJACK end: %s (id=%s) <- %s (id=%s)',
                hijacker.username, hijacker.pk, hijacked.username, hijacked.pk)
