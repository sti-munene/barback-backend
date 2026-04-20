from django.urls import path

from blog.views import PostViewSet

post_list = PostViewSet.as_view({"get": "list"})
post_detail = PostViewSet.as_view({"get": "retrieve"})


urlpatterns = [
    path(
        "posts/",
        post_list,
        name="post_list",
    ),
    path(
        "posts/<str:slug>/",
        post_detail,
        name="post_detail",
    ),
]
