from .models import Tag, Post, Comment, Image ,CustomUser
from .serializers import  PostSerializer, TagSerializer, CommentSerializer, CustomUserSerializer, ImageSerializer
from rest_framework import viewsets,status
from rest_framework.permissions import IsAuthenticatedOrReadOnly,AllowAny
from rest_framework.views import APIView
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import ValidationError


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

    def get_queryset(self):
        # 尝试通过JWT认证获取请求用户
        user = None
        try:
            user = JWTAuthentication().authenticate(self.request)
        except ValidationError:
            # 如果token无效，可以处理异常或简单地忽略，
            # 因为下面的代码在`user`为None时会返回所有用户数据
            pass

        if user is not None:
            # 已经认证，返回该用户数据
            return CustomUser.objects.filter(id=user[0].id)
        else:
            # 未认证，返回所有用户信息
            return CustomUser.objects.all()


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
    permission_classes = [AllowAny]

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

    def list(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # 用户已认证，不使用分页器，返回所有结果
            queryset = self.filter_queryset(self.get_queryset())

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            # 如果没有启用分页或者已经是全部数据，直接序列化所有查询集
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        else:
            # 用户未认证，按默认方式处理，这将应用分页器
            return super(PostViewSet, self).list(request, *args, **kwargs)


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
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        # 从请求获取post_id和comment_id
        post_id = request.data.get('post')
        comment_id = request.data.get('comment')
        # 准备要修改的数据
        data = request.data.copy()

        # 根据post_id获取Post实例的ID
        if post_id:
            post_instance = Post.objects.filter(id=post_id).first()
            # 确保实例存在
            if post_instance:
                data['post'] = post_instance.id
            else:
                return Response({'post': ['No Post with this ID.']}, status=status.HTTP_400_BAD_REQUEST)

        # 根据comment_id获取Comment实例的ID
        if comment_id:
            comment_instance = Comment.objects.filter(id=comment_id).first()
            # 确保实例存在
            if comment_instance:
                data['comment'] = comment_instance.id
            else:
                return Response({'comment': ['No Comment with this ID.']}, status=status.HTTP_400_BAD_REQUEST)

        # 创建新的序列化器实例
        serializer = self.get_serializer(data=data)

        # 校验数据
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # 发送成功创建的响应
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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