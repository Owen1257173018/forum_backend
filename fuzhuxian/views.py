from django.contrib.auth.models import User
from rest_framework.pagination import PageNumberPagination
from .models import Tag, Post, Comment, Image ,CustomUser
from .serializers import  PostSerializer, TagSerializer, CommentSerializer, CustomUserSerializer, ImageSerializer
from rest_framework import viewsets,status
from rest_framework.permissions import IsAuthenticatedOrReadOnly,AllowAny


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
            queryset = Post.objects.all()
            status = self.request.query_params.get('status', None)
            if status is not None:
                queryset = queryset.filter(status=status)
            return queryset


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = Comment.objects.all()
        post_id = self.kwargs.get('post_pk')
        if post_id is not None:
            queryset = queryset.filter(post__id=post_id)
        return queryset


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    Serializerpermission_classes = [IsAuthenticatedOrReadOnly]


from django.db.models import Count, Value, When, Case
from rest_framework.response import Response
from django.db.models import Q,F

def find_posts(user_tags):
    total_tags = len(user_tags)
    split_tags = [word for tag in user_tags for word in tag.split(' ')]

    # 用Q查询一次性构建所需的筛选条件
    query = Q(tags__name__icontains=split_tags[0])
    for tag in split_tags[1:]:
        query |= Q(tags__name__icontains=tag)

    # 使用上述筛选条件，找出所有部分或全反精度最高的帖子
    posts = Post.objects.filter(query) \
        .annotate(matching_tags=Count('tags')) \
        .annotate(matching_score=Value(1.0) * F('matching_tags') / total_tags) \
        .order_by('-matching_score', '-matching_tags')

    # 返回与用户给定标签最匹配的5个帖子
    return posts[:5] if posts.exists() else None

# 新建一个ViewSet，用于处理与标签匹配的帖子的请求
class SimilarPostsByTags(viewsets.ViewSet):

    permission_classes = [AllowAny]

    def create(self, request):
        tags_list = request.data.get('tags')
        posts = find_posts(tags_list)

        # 我们在此假设你有一个PostSerializer类，可用于序列化Post对象
        serializer = PostSerializer(posts, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)