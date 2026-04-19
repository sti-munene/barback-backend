from rest_framework import serializers

from blog.models import Post


class PostSerializer(serializers.ModelSerializer):
    # Ensure the rich text is sent as clean HTML or JSON
    # content_html = serializers.ReadOnlyField(source="content.html")

    class Meta:
        model = Post
        fields = [
            "title",
            "slug",
            # "content_html",
            "content",
            "excerpt",
            "featured_image",
            "meta_title",
            "meta_description",
            "published_at",
            "author",
        ]
