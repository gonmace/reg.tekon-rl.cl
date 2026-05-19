"""
Vistas de PDF para registros TX/TSS.
"""

from pdf_reports.views import RegistroPDFView, preview_registro_individual
from django.shortcuts import render


class RegTxtssPDFView(RegistroPDFView):
    """Vista para generar PDF de registros TX/TSS."""
    pass


def preview_reg_txtss_individual(request, registro_id):
    """Vista para previsualizar el PDF de un registro TX/TSS."""
    view = RegTxtssPDFView()
    view.kwargs = {'registro_id': registro_id}
    context = view.get_context_data()
    return render(request, 'reportes_txtss/txtss.html', context) 