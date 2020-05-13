from django.apps import AppConfig

class ApiConfig(AppConfig):
    name = 'api'
    verbose_name="QTeams-Backend"

    def ready(self):
        import api.signals
