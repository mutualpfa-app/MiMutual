from django.apps import AppConfig


class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news'
    verbose_name = 'Gestión de Novedades'
    
    def ready(self):
        """Importar signals si los usamos en el futuro"""
        pass
