from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User



class UserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        (
            "Información Personal",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone",
                )
            },
        ),
        ("Información para Sistema", {"fields": ("is_active", "is_deleted", "user_type", "contractor")}),
        ("Permisos", {"fields": ("is_staff", "is_superuser")}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )



admin.site.register(User, UserAdmin)

