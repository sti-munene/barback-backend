from django.contrib import admin

from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "published_on", "created_on")

    # Sidebar with filters
    # list_filter = ("status", "created_on", "author")

    # Search bar for titles and content
    search_fields = ("title", "content")

    # AUTO-GENERATE SLUG: This is the magic for SEO.
    # It fills the slug field as you type the title.
    prepopulated_fields = {"slug": ("title",)}

    # Nice UI touches
    date_hierarchy = "published_on"  # Adds a date navigation bar at the top
    raw_id_fields = ("author",)  # Better if you end up with thousands of users
    ordering = ("-created_on",)  # Show newest first

    # Grouping fields into sections (Fieldsets)
    fieldsets = (
        (None, {"fields": ("title", "slug", "status")}),
        (
            "Content",
            {
                "fields": ("content", "excerpt", "featured_image"),
            },
        ),
        (
            "SEO Metadata",
            {
                "classes": ("collapse",),  # Hides this section by default
                "fields": ("meta_title", "meta_description"),
            },
        ),
        (
            "Important Dates",
            {
                "fields": ("published_on",),
            },
        ),
    )
