import json
import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.db.models import Q
from django.forms import modelform_factory
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django_tables2 import SingleTableView
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.permissions import UsuariosAccessMixin
from core.tables import UserTable
from core.utils.breadcrumbs import BreadcrumbsMixin
from .models import User
from .permissions import puede_editar_usuario
from .serializers import UserSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(user_type__in=User.ITO_LIKE_ROLES)
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def usuarios_ito(self, request):
        usuarios = self.queryset
        serializer = self.get_serializer(usuarios, many=True)
        return Response(serializer.data)


class UsersListView(UsuariosAccessMixin, LoginRequiredMixin, BreadcrumbsMixin, SingleTableView):
    model = User
    table_class = UserTable
    template_name = 'users/users_list.html'
    paginate_by = 20

    def get_queryset(self):
        qs = User.objects.filter(is_deleted=False).exclude(user_type='').select_related('contractor').order_by('user_type', 'first_name', 'last_name')
        if self.request.user.is_coord:
            qs = qs.filter(contractor_id=self.request.user.contractor_id)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(username__icontains=q)
            )
        return qs

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['partials/table_swap.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Count
        counts = (
            User.objects.filter(is_deleted=False)
            .values('user_type')
            .annotate(total=Count('id'))
        )
        context['user_role_counts'] = {item['user_type']: item['total'] for item in counts}
        return context

    def get_breadcrumbs(self):
        return [{'label': 'Usuarios'}]


def _validar_password(password, user=None):
    """Devuelve el mensaje de error de los validadores de Django, o None si es válida."""
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError
    try:
        validate_password(password, user)
    except ValidationError as e:
        return ' '.join(e.messages)
    return None


class UserApiView(UsuariosAccessMixin, View):
    """CRUD de usuarios vía JSON."""

    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('username', '').strip().lower()
        password = data.get('password', '').strip()
        if not email:
            return JsonResponse({'success': False, 'message': 'El correo electrónico es obligatorio'}, status=400)
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return JsonResponse({'success': False, 'message': 'Ingrese un correo electrónico válido'}, status=400)
        invitar = bool(data.get('invitar'))
        if not password and not invitar:
            return JsonResponse({'success': False, 'message': 'La contraseña es obligatoria'}, status=400)
        if User.objects.filter(username=email).exists():
            return JsonResponse({'success': False, 'message': 'Ya existe un usuario con ese correo'}, status=400)
        from core.models.contractors import Contractor
        contractor_id = data.get('contractor')
        contractor = Contractor.objects.filter(pk=contractor_id, is_active=True, is_deleted=False).first() if contractor_id else None
        user_type = data.get('user_type', User.ITO)
        if request.user.is_administrador and user_type != User.COORD:
            return JsonResponse({'success': False, 'message': 'ADMINISTRADOR solo puede crear usuarios de tipo Coordinador'}, status=403)
        if request.user.is_coord and user_type not in User.ITO_LIKE_ROLES:
            return JsonResponse({'success': False, 'message': 'COORD solo puede crear usuarios ITO o Buscador'}, status=403)
        if request.user.is_coord:
            if contractor and contractor != request.user.contractor:
                return JsonResponse({'success': False, 'message': 'COORD solo puede crear usuarios de su empresa'}, status=403)
            contractor = request.user.contractor
        if password:
            error = _validar_password(password)
            if error:
                return JsonResponse({'success': False, 'message': error}, status=400)
        user = User(
            username=email,
            email=email,
            first_name=data.get('first_name', '').strip() if not invitar else '',  # el invitado lo completa al activar
            last_name=data.get('last_name', '').strip() if not invitar else '',
            user_type=user_type,
            contractor=contractor,
            report_access=data.get('report_access', []),
        )
        if invitar:
            user.set_unusable_password()  # la crea el propio usuario desde el enlace de la invitación
        else:
            user.set_password(password)
        user.save()
        if invitar:
            return _responder_invitacion(user, request.user, creado=True)
        return JsonResponse({'success': True, 'message': 'Usuario creado correctamente'})

    def put(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, is_deleted=False)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Usuario no encontrado'}, status=404)
        if not puede_editar_usuario(request.user, user):
            return JsonResponse({'success': False, 'message': 'No tienes permisos para modificar a este usuario'}, status=403)
        try:
            data = json.loads(request.body.decode('utf-8'))
            user.first_name = data.get('first_name', user.first_name).strip()
            user.last_name = data.get('last_name', user.last_name).strip()
            new_type = data.get('user_type', user.user_type)
            if request.user.is_administrador and new_type != User.COORD:
                return JsonResponse({'success': False, 'message': 'ADMINISTRADOR solo puede asignar tipo Coordinador'}, status=403)
            if request.user.is_coord and new_type not in User.ITO_LIKE_ROLES:
                return JsonResponse({'success': False, 'message': 'COORD solo puede asignar tipo ITO o Buscador'}, status=403)
            user.user_type = new_type
            if 'is_active' in data:
                user.is_active = bool(data['is_active'])
            contractor_id = data.get('contractor')
            if contractor_id:
                from core.models.contractors import Contractor
                new_contractor = Contractor.objects.filter(pk=contractor_id, is_active=True, is_deleted=False).first()
                if request.user.is_coord and new_contractor != request.user.contractor:
                    return JsonResponse({'success': False, 'message': 'COORD solo puede asignar usuarios a su empresa'}, status=403)
                user.contractor = new_contractor
            elif 'contractor' in data:
                user.contractor = None
            if 'report_access' in data:
                user.report_access = data['report_access'] if isinstance(data['report_access'], list) else []
            password = data.get('password', '').strip()
            if password:
                error = _validar_password(password, user)
                if error:
                    return JsonResponse({'success': False, 'message': error}, status=400)
                user.set_password(password)
            user.save()
            return JsonResponse({'success': True, 'message': 'Usuario actualizado correctamente'})
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception('Error actualizando usuario %s', user_id)
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, is_deleted=False)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Usuario no encontrado'}, status=404)
        if not puede_editar_usuario(request.user, user) or user.pk == request.user.pk:
            return JsonResponse({'success': False, 'message': 'No tienes permisos para eliminar a este usuario'}, status=403)
        user.is_deleted = True
        user.is_active = False
        user.save()
        return JsonResponse({'success': True, 'message': 'Usuario eliminado correctamente'})


def _responder_invitacion(user, invitador, creado=False):
    """Envía la invitación y arma la respuesta JSON (el envío puede fallar aunque el usuario exista)."""
    import logging
    from .invitations import enviar_invitacion
    try:
        enviar_invitacion(user, invitador)
    except Exception:
        logging.getLogger(__name__).exception('No se pudo enviar la invitación a %s', user.pk)
        base = 'Usuario creado, pero no se pudo enviar la invitación' if creado else 'No se pudo enviar la invitación'
        return JsonResponse({'success': creado, 'message': f'{base}. Reintenta desde la lista de usuarios.'},
                            status=200 if creado else 502)
    msg = f'Usuario creado e invitación enviada a {user.email}' if creado else f'Invitación enviada a {user.email}'
    return JsonResponse({'success': True, 'message': msg})


class UserInviteView(UsuariosAccessMixin, View):
    """Envía (o reenvía) la invitación para que el usuario cree su contraseña."""

    def post(self, request, user_id):
        user = User.objects.filter(id=user_id, is_deleted=False).first()
        if not user:
            return JsonResponse({'success': False, 'message': 'Usuario no encontrado'}, status=404)
        if user.is_supermanager or user.is_superuser:
            return JsonResponse({'success': False, 'message': 'No se puede invitar a este usuario'}, status=403)
        if request.user.is_coord and not (
            user.user_type in User.ITO_LIKE_ROLES and user.contractor_id == request.user.contractor_id
        ):
            return JsonResponse({'success': False, 'message': 'COORD solo puede invitar a usuarios ITO o Buscador de su empresa'}, status=403)
        if not user.is_active:
            return JsonResponse({'success': False, 'message': 'El usuario está inactivo'}, status=400)
        return _responder_invitacion(user, request.user)


class UserEditModalView(UsuariosAccessMixin, View):
    """Devuelve el HTML del formulario para el modal."""

    def get(self, request, user_id=None):
        if user_id:
            try:
                user = User.objects.get(id=user_id, is_deleted=False)
                action = 'edit'
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Usuario no encontrado'}, status=404)
            if not puede_editar_usuario(request.user, user):
                return JsonResponse({'success': False, 'message': 'No tienes permisos para modificar a este usuario'}, status=403)
        else:
            user = None
            action = 'create'

        fields = ['first_name', 'last_name', 'contractor', 'user_type', 'is_active'] if action == 'edit' else ['username', 'first_name', 'last_name', 'contractor', 'user_type']
        UserForm = modelform_factory(User, fields=fields)
        form = UserForm(instance=user)

        from core.models.contractors import Contractor
        if request.user.is_coord and request.user.contractor:
            form.fields['contractor'].queryset = Contractor.objects.filter(pk=request.user.contractor.pk)
        else:
            form.fields['contractor'].queryset = Contractor.objects.filter(is_active=True, is_deleted=False).order_by('name')
        form.fields['contractor'].empty_label = 'Seleccionar empresa...'

        if request.user.is_administrador:
            form.fields['user_type'].choices = [(User.COORD, 'Coordinador')]
        elif request.user.is_coord:
            form.fields['user_type'].choices = [
                (User.ITO, 'ITO'),
                (User.SEARCHER, 'Buscador'),
            ]

        input_class = 'input input-bordered w-full'
        select_class = 'select select-bordered w-full'
        for field_name, field in form.fields.items():
            if field_name == 'is_active':
                field.widget.attrs.update({'class': 'toggle toggle-success'})
            elif field_name in ('user_type', 'contractor'):
                field.widget.attrs.update({'class': select_class})
            elif field_name == 'username':
                field.label = 'Correo electrónico'
                field.widget.attrs.update({
                    'class': input_class,
                    'type': 'email',
                    'placeholder': 'usuario@ejemplo.com',
                    'autocomplete': 'email',
                })
            else:
                field.widget.attrs.update({'class': input_class, 'placeholder': f'Ingrese {field.label.lower()}'})

        form_html = render(request, 'users/user_form_modal.html', {
            'form': form,
            'user': user,
            'action': action,
            'report_access_choices': User.REPORT_ACCESS_CHOICES,
            'current_report_access': list(user.report_access) if user else [],
            'restricted_roles': list(User.RESTRICTED_ROLES),
        }).content.decode('utf-8')

        return JsonResponse({'success': True, 'form_html': form_html})


class LoginView(DjangoLoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True


class LogoutView(DjangoLogoutView):
    pass
