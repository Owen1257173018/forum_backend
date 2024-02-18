from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Tag, Post, Comment, Image, STATUS_CHOICES


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id', 'image', 'post', 'comment')


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, required=False, )
    images = ImageSerializer(many=True, read_only=True, source='image_set', required=False)
    status = serializers.ChoiceField(choices=STATUS_CHOICES, default="n")

    class Meta:
        model = Post
        fields = ('id', 'title', 'status', 'tags', 'body', 'created_at', 'update_at', 'author', 'images')

    def create(self, validated_data):
        request = self.context.get('view').request
        images_data = request.FILES
        post = Post.objects.create(**validated_data)

        # 检测 content_type，根据不同的 content_type 处理 tags
        if request.content_type == 'application/json':
            tags_data = validated_data.pop('tags', [])
            for tag_data in tags_data:
                tag, _ = Tag.objects.get_or_create(name=tag_data['name'])
                post.tags.add(tag.id)
        else:  # 处理 form-data 中的 tags
            tag_names = request.data.get('tags', '').split(",")
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
                post.tags.add(tag.id)
            for image_data in images_data.values():
                Image.objects.create(post=post, image=image_data)

        return post



    def update(self, instance, validated_data):
        request = self.context.get('view').request
        images_data = request.FILES
        instance.title = validated_data.get('title', instance.title)
        instance.body = validated_data.get('body', instance.body)
        instance.status = validated_data.get('status', instance.status)
        instance.tags.clear()

        instance.image_set.all().delete()

        # 检测 content_type，根据不同的 content_type 处理 tags
        if request.content_type == 'application/json':
            tags_data = validated_data.pop('tags', [])
            for tag_data in tags_data:
                tag, _ = Tag.objects.get_or_create(name=tag_data['name'])
                instance.tags.add(tag.id)
        else:  # 处理 form-data 中的 tags
            tag_names = request.data.get('tags', '').split(",")
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
                instance.tags.add(tag.id)
            for image_data in images_data.values():
                Image.objects.create(post=instance, image=image_data)

        instance.save()
        return instance



class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())
    images = ImageSerializer(many=True, read_only=True, source='image_set')
    tags = TagSerializer(many=True, required=False)
    modify_tags = serializers.BooleanField(default=False)

    class Meta:
        model = Comment
        fields = ('id', 'post', 'body', 'created_at', 'update_at', 'author', 'images', 'tags', 'modify_tags')

    def create(self, validated_data):
        request = self.context.get('view').request
        modify_tags = validated_data.pop('modify_tags', False)
        images_data = request.FILES
        comment = Comment.objects.create(**validated_data)
        post = comment.post

        if modify_tags:
            post.tags.clear()

            if request.content_type == 'application/json':
                tags_data = validated_data.pop('tags', [])
                for tag_data in tags_data:
                    tag, _ = Tag.objects.get_or_create(name=tag_data['name'])
                    post.tags.add(tag.id)
            else:  # 处理 form-data 中的 tags
                tag_names = request.data.get('tags', '').split(",")
                for tag_name in tag_names:
                    tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
                    post.tags.add(tag.id)

                for image_data in images_data.values():
                    Image.objects.create(comment=comment, image=image_data)

        post.save()
        return comment

    def update(self, instance, validated_data):
        request = self.context.get('view').request
        modify_tags = validated_data.pop('modify_tags', False)
        images_data = request.FILES
        instance.body = validated_data.get('body', instance.body)

        instance.image_set.all().delete()


        if modify_tags:
            post = instance.post
            post.tags.clear()

            if request.content_type == 'application/json':
                tags_data = validated_data.pop('tags', [])
                for tag_data in tags_data:
                    tag, _ = Tag.objects.get_or_create(name=tag_data['name'])
                    post.tags.add(tag)
            else:  # 处理 form-data 中的 tags
                tag_names = request.data.get('tags', '').split(",")
                for tag_name in tag_names:
                    tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
                    post.tags.add(tag)

                for image_data in images_data.values():
                    Image.objects.create(comment=instance, image=image_data)

            post.save()
        instance.save()
        return instance