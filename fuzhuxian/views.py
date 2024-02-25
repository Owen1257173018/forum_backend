from .models import Tag, Post, Comment, Image ,CustomUser
from .serializers import  PostSerializer, TagSerializer, CommentSerializer, CustomUserSerializer, ImageSerializer
from rest_framework import viewsets,status
from rest_framework.permissions import IsAuthenticatedOrReadOnly,AllowAny
from rest_framework.views import APIView
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from django.contrib.auth import get_user_model



class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    # 重写create方法来允许未认证用户注册，并返回token
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token = serializer.get_token(user)  # 获取token

        headers = self.get_success_headers(serializer.data)
        return Response({
            'user': serializer.data,
            'token': token
        }, status=status.HTTP_201_CREATED, headers=headers)

    # 确保create操作可以由任何人访问
    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [AllowAny, ]
        else:
            self.permission_classes = [IsAuthenticatedOrReadOnly, ]
        return super(CustomUserViewSet, self).get_permissions()

User = get_user_model()

class CustomTokenObtainView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        number = request.data.get('number', None)
        password = request.data.get('password', None)

        try:
            # 根据学号查找对应的用户
            user = User.objects.get(number=number)
        except User.DoesNotExist:
            return Response({'error': 'Invalid number or password'}, status=status.HTTP_401_UNAUTHORIZED)

        # 使用RequestFactory模拟一个请求到/token/接口
        factory = APIRequestFactory()
        token_request = factory.post('/user/token/', {
            'username': user.username,  # 使用找到的用户名
            'password': password
        }, format='json')

        # 创建一个TokenObtainPairView实例并调用它的post方法
        view = TokenObtainPairView.as_view()
        token_response = view(token_request)

        # 从TokenObtainPairView的响应中提取token数据
        if token_response.status_code == status.HTTP_200_OK:
            return Response(token_response.data, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid number or password'}, status=token_response.status_code)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at',)  # 假设'created'是存储创建时间的字段
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


    def get_queryset(self):
        """
        Optionally restricts the returned posts to a given user,
        by adding a `my_posts` query parameter to the URL.
        """
        queryset = Post.objects.all().order_by('-created_at')
        status = self.request.query_params.get('status')
        if status is not None:
            queryset = queryset.filter(status=status)

        # Check if 'my_posts' query param is set to true
        my_posts = self.request.query_params.get('my_posts') == 'true'
        if my_posts and self.request.user.is_authenticated:
            queryset = queryset.filter(author=self.request.user)

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