from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('usuarios/', views.UsersListView.as_view(), name='list'),
    path('api/v1/users/', views.UserApiView.as_view(), name='api'),
    path('api/v1/users/<int:user_id>/', views.UserApiView.as_view(), name='api_detail'),
    path('api/v1/users/create-modal/', views.UserEditModalView.as_view(), name='create_modal'),
    path('api/v1/users/<int:user_id>/edit-modal/', views.UserEditModalView.as_view(), name='edit_modal'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='users/password_reset.html',
        email_template_name='users/password_reset_email.html',
        subject_template_name='users/password_reset_subject.txt',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html',
    ), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
    ), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html',
    ), name='password_reset_complete'),
]
