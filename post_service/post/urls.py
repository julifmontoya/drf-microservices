# post/urls.py
from django.urls import path
from post.views import PostListProv, PostCreateProv, PostDetailProv

urlpatterns = [
    path('posts/', PostListProv.as_view()),
    path('posts/create/', PostCreateProv.as_view()),
    path('posts/<id>/', PostDetailProv.as_view()),
]
