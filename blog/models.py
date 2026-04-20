from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    author = models.ForeignKey("auth.User", on_delete=models.CASCADE)

    # Ghost-style Rich Text
    content = CKEditor5Field("Content", config_name="extends")

    # SEO Fields
    excerpt = models.TextField(
        max_length=300, help_text="Used for social media snippets"
    )
    featured_image = models.ImageField(upload_to="blog/images/", blank=True, null=True)
    meta_title = models.CharField(max_length=70, blank=True, null=True)
    meta_description = models.TextField(max_length=160, blank=True, null=True)

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # if not self.slug:
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        ordering = ["-published_at", "-created_at"]

        verbose_name = "Post"
        verbose_name_plural = "Posts"
