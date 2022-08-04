from django.apps import AppConfig


class GimmoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gimmo'

    #def ready(self):
    #    from gimmo.jobs import updater
    #    updater.start()
