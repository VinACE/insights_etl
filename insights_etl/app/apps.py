import django.apps


class AppConfig (django.apps.AppConfig):
    name = 'app'

    def ready(self):

        import app.models as models




