from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from imagekit.models import ImageSpecField
from imagekit.processors import Transpose
from PIL import Image


# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    likes = models.IntegerField(default=0)
    image = models.ImageField(upload_to='post_pics', null=True, blank=True)
    image_thumbnail = ImageSpecField(
        source='image',
        processors=[Transpose()],
        format='JPEG',
        options={'quality': 75}
    )

    def save(self, *args, **kwargs):
        super().save()
        img = Image.open(self.image.path)

        # if img.height > 600 or img.width > 400:
        output_size = (600, 400)
        img = img.resize(output_size)

        img.save(self.image.path)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk})


class Comment(models.Model):
    comment_text = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    likes = models.IntegerField(default=0)

    def __str__(self):
        return self.comment_text


class ChildComment(models.Model):
    comment_text = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    parent_comment = models.ForeignKey(Comment, related_name='child_comments', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='child_comments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='child_comments', on_delete=models.CASCADE)
    likes = models.IntegerField(default=0)

    def __str__(self):
        return self.comment_text


class PostLikes(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)


class CommentLikes(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)


class ChildCommentLikes(models.Model):
    child_comment = models.ForeignKey(ChildComment, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)


class Notification(models.Model):
    notification_text = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True)
    child_comment = models.ForeignKey(ChildComment, on_delete=models.CASCADE, null=True)
    liked_post = models.ForeignKey(PostLikes, on_delete=models.CASCADE, null=True)
    liked_comment = models.ForeignKey(CommentLikes, on_delete=models.CASCADE, null=True)
    liked_child_comment = models.ForeignKey(ChildCommentLikes, on_delete=models.CASCADE, null=True)
