from django.apps import AppConfig


class TravelsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "travels"

    def ready(self):
        # Import com efeito colateral: registra os receivers do post_save.
        from . import signals  # noqa: F401
