from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from fuzhuxian.views import CustomUserViewSet, TagViewSet, PostViewSet, CommentViewSet, SimilarPostsByTags

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)
router.register(r'tags', TagViewSet)
router.register(r'posts', PostViewSet)
router.register(r'comments', CommentViewSet)

router.register(r'similar_posts', SimilarPostsByTags, basename='similar_posts')

comments_router = routers.NestedDefaultRouter(router, r'posts', lookup='post')
comments_router.register(r'comments', CommentViewSet, basename='post-comments')

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('', include(router.urls)),
    path('', include(comments_router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)