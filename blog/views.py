from rest_framework import filters, permissions, viewsets

from blog.models import Post
from blog.serializers import PostSerializer
from utils.pagination import BasePaginationSet


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for viewing published blog posts.
    """

    queryset = Post.objects.filter(status="PUBLISHED")  # Only show live posts
    serializer_class = PostSerializer
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]
    pagination_class = BasePaginationSet
    search_fields = ["title"]
    filter_backends = (filters.SearchFilter,)
