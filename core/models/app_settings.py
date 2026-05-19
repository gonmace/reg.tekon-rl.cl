from django.db import models

from core.models.core_models import BaseModel


class AppSettings(BaseModel):
    app_name = models.CharField(
        max_length=255, verbose_name="Nombre de la Aplicación", null=True, blank=True
    )
    google_maps_api_key = models.CharField(
        max_length=255, verbose_name="Google Maps API Key", null=True, blank=True
    )
    logo = models.FileField(
        "logo",
        null=True,
        blank=True,
        upload_to="app_settings/logo/",
    )
    recipients_email = models.TextField(
        "Correo de destinatarios",
        null=True,
        blank=True,
    )
    app_apk = models.FileField(
        "APK de la Aplicación",
        null=True,
        blank=True,
        upload_to="app_settings/apk/",
    )
    last_apk_version = models.CharField(
        "Última versión del APK",
        max_length=20,
        null=True,
        blank=True,
    )
    class Meta:
        verbose_name = "Configuración"
        verbose_name_plural = "Configuraciones"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # que en cada subida, se genere una nueva versión del APK
        if self.app_apk and not self.last_apk_version:
            # If the APK is being set for the first time, set the version
            self.last_apk_version = "1.0.0"
        elif self.app_apk:
            # If the APK is being updated, increment the version
            current_version = self.last_apk_version.split('.')
            if len(current_version) == 3:
                current_version[-1] = str(int(current_version[-1]) + 1)
                self.last_apk_version = '.'.join(current_version)
            else:
                self.last_apk_version = "1.0.0"
        super().save(*args, **kwargs)

    @staticmethod
    def get_actives():
        return AppSettings.objects.last()

    @staticmethod
    def get_table():
        pass
