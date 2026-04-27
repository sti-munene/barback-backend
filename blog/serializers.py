from django.contrib.auth.models import User
from rest_framework import serializers

from blog.models import Post


class AuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
        ]


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Post
        fields = [
            "title",
            "slug",
            "content",
            "excerpt",
            "featured_image",
            "meta_title",
            "meta_description",
            "author",
            "published_on",
        ]
