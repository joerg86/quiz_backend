from django.apps import AppConfig

class ApiConfig(AppConfig):
    name = 'api'
    verbose_name="Q-Teams-Backend"

    def ready(self):
        import api.signals
