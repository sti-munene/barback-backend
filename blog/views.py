from rest_framework import permissions, viewsets

from blog.models import Post
from blog.serializers import PostSerializer


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for viewing published blog posts.
    """

    queryset = Post.objects.filter(status="PUBLISHED")  # Only show live posts
    serializer_class = PostSerializer

    # Use 'slug' in the URL instead of 'id' for SEO
    lookup_field = "slug"

    # Ensure the API is public
    permission_classes = [permissions.AllowAny]
