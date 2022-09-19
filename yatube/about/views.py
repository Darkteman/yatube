from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """Загружает шаблон: Об авторе."""
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """Загружает шаблон: Технологии."""
    template_name = 'about/tech.html'
