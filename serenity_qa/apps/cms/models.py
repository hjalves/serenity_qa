from django.db import models


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
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT
    )
    content = models.TextField(blank=True)
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
