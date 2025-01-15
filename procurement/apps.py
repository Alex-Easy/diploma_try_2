from django.apps import AppConfig


class ProcurementConfig(AppConfig):
    """
    Configuration class for the 'procurement' application.

    Attributes:
        default_auto_field (str): Specifies the type of primary key to use for models.
        name (str): The full Python path to the application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'procurement'

