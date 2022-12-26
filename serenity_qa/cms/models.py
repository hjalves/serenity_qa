from django.contrib.contenttypes.models import ContentType
from django.db import models

from serenity_qa.questions.models import Question


class PageManager(models.Manager):
    def published(self):
        return self.filter(status=Page.STATUS_PUBLISHED)


class Page(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CHOICES = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
    )

    objects = PageManager()

    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    content = models.TextField(blank=True)
    footer = models.TextField(blank=True)
    root_page = models.BooleanField(default=False)
    show_in_nav = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "page"
        verbose_name_plural = "pages"
        ordering = ["-root_page", "created_on"]

    def __str__(self):
        return self.title

    def enabled_sections(self):
        return self.sections.filter(enabled=True)


class Section(models.Model):
    COMPONENT_CHOICES = [
        ("question", "Question"),
        ("progress", "Project progress"),
    ]
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="sections")
    component = models.CharField(max_length=100, choices=COMPONENT_CHOICES)
    arguments = models.JSONField(default=dict, blank=True, null=True)
    ordering = models.IntegerField(null=True, blank=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = "section"
        verbose_name_plural = "sections"
        ordering = ("page", "ordering", "id")

    def __str__(self):
        return f"{self.component} ({self.get_arguments_str()})"

    def get_arguments_str(self):
        if arguments := self.arguments or {}:
            return ", ".join(f"{k}={v!r}" for k, v in arguments.items())
        return ""
