from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View


@login_required
def debug_form_view(request):
    return render(request, 'debug_form.html')


@method_decorator(login_required, name='dispatch')
class DebugFormView(View):
    def post(self, request):
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'message': 'Forbidden'}, status=403)
        form_data = request.POST.dict()
        return JsonResponse({
            'success': True,
            'message': 'Formulario recibido correctamente',
            'data': form_data,
            'files_count': len(request.FILES),
        })

    def get(self, request):
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'message': 'Forbidden'}, status=403)
        return JsonResponse({'success': True, 'message': 'Debug endpoint funcionando', 'method': 'GET'})
