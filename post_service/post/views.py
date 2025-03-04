from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .serializers import PostSerializer
from .models import Post
from .utils.auth_utils import get_authenticated_user_id


class PostListProv(APIView):
    def get(self, request):
        user_id = get_authenticated_user_id(request)
        if not user_id:
            return Response({"error": "Invalid or missing token"}, status=status.HTTP_401_UNAUTHORIZED)

        # Query all posts related to the authenticated user
        posts = Post.objects.filter(user_id=user_id)
        serializer = PostSerializer(posts, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PostCreateProv(APIView):
    def post(self, request):
        user_id = get_authenticated_user_id(request)
        if not user_id:
            return Response({"error": "Invalid or missing token"}, status=status.HTTP_401_UNAUTHORIZED)

        data = request.data.copy()
        data["user_id"] = user_id  # Inject user_id into request data

        serializer = PostSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostDetailProv(APIView):
    def get(self, request, id):
        user_id = get_authenticated_user_id(request)
        if not user_id:
            return Response({"error": "Invalid or missing token"}, status=status.HTTP_401_UNAUTHORIZED)
        
        post = get_object_or_404(Post, id=id, user_id=user_id)  
        serializer = PostSerializer(post)
        return Response(serializer.data)

    def put(self, request, id):
        user_id = get_authenticated_user_id(request)
        if not user_id:
            return Response({"error": "Invalid or missing token"}, status=status.HTTP_401_UNAUTHORIZED)
    
        post = get_object_or_404(Post, id=id, user_id=user_id)

        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

