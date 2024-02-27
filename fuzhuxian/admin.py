from django.contrib import admin
from .models import Tag, Post, Comment, Image,CustomUser
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.admin import UserAdmin

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = CustomUser
        fields = ('username', 'number')

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm):
        model = CustomUser
        fields = UserChangeForm.Meta.fields

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['username', 'number', 'is_staff']
    # ...

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('number',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser',
                                   'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'number', 'password1', 'password2'),
        }),
    )

class ImageInline(admin.TabularInline): # 可以改成 admin.StackedInline，如果你希望它显示为堆栈形式
    model = Image
    extra = 1  # 设置默认显示的空白数量


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)  # 在Admin列表中显示的字段
    search_fields = ('name',)  # 在Admin中搜索的字段

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    inlines = [ImageInline,]  # 添加inline属性
    fields = ('title', 'body', 'author',  'tags','status')
    list_display = ('id', 'title', 'body', 'author', 'status','created_at')
    search_fields = ('title','body',)
    list_filter = ('created_at','author', 'tags','status')  # 右侧筛选栏
    date_hierarchy = 'created_at'  # 顶部时间导航栏


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    inlines = [ImageInline,]  # 添加inline属性相同
    fields = ('body', 'author', 'post')
    list_display = ('id', 'body', 'created_at', 'author', 'post', 'created_at')
    search_fields = ('body',)
    list_filter = ('created_at','author', 'post')


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'post', 'comment')