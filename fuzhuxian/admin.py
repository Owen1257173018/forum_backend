from django.contrib import admin
from .models import Tag, Post, Comment, Image

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)  # 在Admin列表中显示的字段
    search_fields = ('name',)  # 在Admin中搜索的字段

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    fields = ('title', 'body', 'author',  'tags','status')
    list_display = ('title', 'body', 'author', 'status','created_at')
    search_fields = ('title','body',)
    list_filter = ('created_at','author', 'tags','status')  # 右侧筛选栏
    date_hierarchy = 'created_at'  # 顶部时间导航栏

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    fields = ('body', 'author', 'post')
    list_display = ('body', 'created_at', 'author', 'post', 'created_at')
    search_fields = ('body',)
    list_filter = ('created_at','author', 'post')

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('image', 'post', 'comment')