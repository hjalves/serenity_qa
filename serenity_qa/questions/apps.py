from django.apps import AppConfig


class QuestionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "serenity_qa.questions"

    def ready(self):
        from . import signals  # NOQA
