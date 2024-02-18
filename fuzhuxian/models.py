from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class Tag(models.Model):
    name = models.CharField(max_length=200,verbose_name='标签名称',help_text='标签名称')

    def __str__(self):
        return self.name

class Content(models.Model):
    body = models.TextField(verbose_name='内容',help_text='内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间',help_text='创建时间')
    update_at = models.DateTimeField(auto_now_add=True, verbose_name='更新时间',help_text='更新时间')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,verbose_name='作者',help_text='作者')

#定义为抽象类，数据库不用专门生成一个表
    class Meta:
        abstract = True

STATUS_CHOICES = {
    ("n",  "未开始"),
    ("i", "正在进行"),
    ("a",  "已解决"),
}

class Post(Content):
    title = models.CharField(max_length=200,verbose_name='标题',help_text='标题')
    tags = models.ManyToManyField(Tag,  blank=True, verbose_name='标签',help_text='标签')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES , default="n", verbose_name='状态', help_text='状态')

    def __str__(self):
        return self.title
class Comment(Content):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE, verbose_name='帖子外键',help_text='帖子外键')

    def __str__(self):
        return self.body

class Image(models.Model):
    image = models.ImageField(verbose_name="图片", help_text="图片")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, verbose_name="对应帖子或评论", help_text="对应帖子或评论")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, verbose_name="对应帖子或评论", help_text="对应帖子或评论")

    def __str__(self):
        return self.image

