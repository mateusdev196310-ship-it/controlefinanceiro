from django.apps import AppConfig


class FinancasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'financas'
    
    def ready(self):
        """
        Importa os signals quando a aplicação estiver pronta.
        Isso garante que os signals sejam registrados automaticamente.
        """
        import financas.signals
