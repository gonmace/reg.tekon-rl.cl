"""
Vistas de PDF para registros TX/TSS.
"""

from pdf_reports.views import RegistroPDFView, preview_registro_individual
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from core.permissions import can_access_registro


class RegTxtssPDFView(RegistroPDFView):
    """Vista para generar PDF de registros TX/TSS."""
    pass


@login_required
def preview_reg_txtss_individual(request, registro_id):
    """Vista para previsualizar el PDF de un registro TX/TSS."""
    from reg_txtss.models import RegTxtss
    registro = get_object_or_404(
        RegTxtss.objects.select_related('sitio', 'user'), id=registro_id
    )
    if not can_access_registro(request.user, registro):
        raise PermissionDenied('No tienes acceso a este registro.')

    view = RegTxtssPDFView()
    view.kwargs = {'registro_id': registro_id}
    context = view.get_context_data()
    context['es_preview'] = True
    return render(request, 'reportes_txtss/txtss.html', context)