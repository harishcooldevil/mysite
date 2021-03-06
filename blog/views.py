from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User
from .models import Post, Comment, ChildComment, Notification, CommentLikes, PostLikes, ChildCommentLikes
from .forms import CommentCreateForm, ChildCommentCreateForm
from django.db.models import Q

# from django.http import HttpResponse
# Create your views here.


def home(request):
    context = {
        'posts': Post.objects.all()
    }
    return render(request, 'blog/home.html', context)


class PostListView(ListView):
    model = Post
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 5


class UserPostListView(ListView):
    model = Post
    template_name = 'blog/user_posts.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user).order_by('-date_posted')


class PostDetailView(DetailView):
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post_pk = self.kwargs.get('pk')
        post = get_object_or_404(Post, pk=post_pk)
        if self.request.user.is_authenticated:
            if self.request.user.postlikes_set.filter(post=post).exists():
                context['post_liked'] = 'yes'
            filtered_comment_keys = post.comments.all().values_list('pk', flat=True)
            context['comments_liked'] = self.request.user.commentlikes_set.\
                filter(comment__pk__in=filtered_comment_keys).values_list('comment__pk', flat=True)
            filtered_c_comment_keys = post.child_comments.all().values_list('pk', flat=True)
            context['child_comments_liked'] = self.request.user.childcommentlikes_set.\
                filter(child_comment__pk__in=filtered_c_comment_keys).values_list('child_comment__pk', flat=True)
        if self.request.GET.get('cpk'):
            context['cpk'] = int(self.request.GET.get('cpk'))
        if self.request.GET.get('ccpk'):
            context['ccpk'] = int(self.request.GET.get('ccpk'))
        return context

    def post(self, request, *args, **kwargs):
        form = CommentCreateForm(request.POST)
        if form.is_valid() and request.user.is_authenticated:
            form.instance.author = request.user
            form.instance.post = Post.objects.get(pk=self.kwargs.get('pk'))
            form.save()
            return redirect(reverse('post-detail',
                                    kwargs={'pk': self.kwargs.get('pk')}) + '?cpk={}'.format(form.instance.pk))
        else:
            if not request.user.is_authenticated:
                messages.error(request, 'you need to be logged in to comment')
            else:
                messages.error(request, 'error while posting comment')
            return redirect('post-detail', pk=self.kwargs.get('pk'))


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['title', 'content', 'image']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'content', 'image']

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['update'] = 'update'
        return context

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})


def comment_update(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post_id = comment.post.id
    if request.method == "POST":
        form = CommentCreateForm(instance=comment, data=request.POST)
        if form.is_valid() and request.user == form.instance.author:
            form.save()
            return redirect(reverse('post-detail', kwargs={'pk': post_id}) + '?cpk={}'.format(comment.pk))
        else:
            messages.error(request, "you don't have permission to do this")
    else:
        messages.error(request, "you don't have permission to do this")
    return redirect('post-detail', pk=post_id)


def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post_id = comment.post.id
    if request.method == "POST":
        if request.user == comment.author:
            comment.delete()
        else:
            messages.error(request, "you don't have permission to do this")
    else:
        messages.error(request, "you don't have permission to do this")
    return redirect('post-detail', pk=post_id)


def child_comment_update(request, pk):
    comment = get_object_or_404(ChildComment, pk=pk)
    post_id = comment.post.id
    if request.method == "POST":
        form = ChildCommentCreateForm(instance=comment, data=request.POST)
        if form.is_valid() and request.user == form.instance.author:
            form.save()
            return redirect(reverse('post-detail', kwargs={'pk': post_id}) + '?ccpk={}'.format(comment.pk))
        else:
            messages.error(request, "you don't have permission to do this")
    else:
        messages.error(request, "you don't have permission to do this")
    return redirect('post-detail', pk=post_id)


def child_comment_delete(request, pk):
    comment = get_object_or_404(ChildComment, pk=pk)
    post_id = comment.post.id
    if request.method == "POST":
        if request.user == comment.author:
            comment.delete()
        else:
            messages.error(request, "you don't have permission to do this")
    else:
        messages.error(request, "you don't have permission to do this")
    return redirect('post-detail', pk=post_id)


def child_comment_create(request, ppk, cpk):
    post = get_object_or_404(Post, pk=ppk)
    if request.method == "POST":
        form = ChildCommentCreateForm(data=request.POST)
        form.instance.author = request.user
        form.instance.post = post
        form.instance.parent_comment = get_object_or_404(Comment, pk=cpk)
        if request.user.is_authenticated and form.is_valid():
            form.save()
            return redirect(reverse('post-detail', kwargs={'pk': post.pk}) + '?ccpk={}'.format(form.instance.pk))
        else:
            messages.error(request, "you don't have permission to do this")
    else:
        messages.error(request, "you don't have permission to do this")
    return redirect('post-detail', pk=post.pk)


def update_comment_likes(request):
    if request.user.is_authenticated:
        pk = int(request.GET.get('pk'))
        comment = get_object_or_404(Comment, pk=pk)
        if request.user.commentlikes_set.filter(comment__pk=pk).exists():
            request.user.commentlikes_set.filter(comment__pk=pk).delete()
            mute = 1
        else:
            CommentLikes.objects.create(comment=comment, author=request.user)
            mute = 0
        return JsonResponse(data={'likes': len(comment.commentlikes_set.all()), 'mute': mute})
    else:
        return JsonResponse(data={'permission': 'denied'})


def update_post_likes(request):
    if request.user.is_authenticated:
        pk = int(request.GET.get('pk'))
        post = get_object_or_404(Post, pk=pk)
        if request.user.postlikes_set.filter(post__pk=pk).exists():
            request.user.postlikes_set.filter(post__pk=pk).delete()
            mute = 1
        else:
            PostLikes.objects.create(post=post, author=request.user)
            mute = 0
        return JsonResponse(data={'likes': len(post.postlikes_set.all()), 'mute': mute})
    else:
        return JsonResponse(data={'permission': 'denied'})


def update_child_comment_likes(request):
    if request.user.is_authenticated:
        pk = int(request.GET.get('pk'))
        child_comment = get_object_or_404(ChildComment, pk=pk)
        if request.user.childcommentlikes_set.filter(child_comment__pk=pk).exists():
            request.user.childcommentlikes_set.filter(child_comment__pk=pk).delete()
            mute = 1
        else:
            ChildCommentLikes.objects.create(child_comment=child_comment, author=request.user)
            mute = 0
        return JsonResponse(data={'likes': len(child_comment.childcommentlikes_set.all()), 'mute': mute})
    else:
        return JsonResponse(data={'permission': 'denied'})


class PostSearchListView(ListView):
    model = Post
    template_name = 'blog/search.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 5

    def get_queryset(self):
        return Post.objects.filter(
            Q(title__icontains=self.request.GET.get('search')) |
            Q(content__icontains=self.request.GET.get('search')) |
            Q(author__username__icontains=self.request.GET.get('search'))).order_by('-date_posted')


class LatestPosts(ListView):
    model = Post
    template_name = 'blog/latest.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 5

    def get_queryset(self):
        return Post.objects.order_by('-date_posted')[:10]


def delete_notification(request, pk):
    if request.user.is_authenticated:
        notification = get_object_or_404(Notification, pk=pk)
        if notification.author == request.user:
            notification.delete()
            return JsonResponse(data={'success': 'success', 'count': len(request.user.notification_set.all())})
    return JsonResponse(data={'error': 'Permission denied'})


def who_liked_post(request, pk):
    if request.user.is_authenticated:
        post = get_object_or_404(Post, pk=pk)
        if post.postlikes_set.all().exists():
            liked_usernames = '|||'.join(post.postlikes_set.all().values_list('author__username', flat=True))
            return JsonResponse(data={'success': 'success', 'liked_usernames': liked_usernames})
    return JsonResponse(data={'error': 'Permission denied'})


def who_liked_comment(request, pk):
    if request.user.is_authenticated:
        comment = get_object_or_404(Comment, pk=pk)
        if comment.commentlikes_set.all().exists():
            liked_usernames = '|||'.join(comment.commentlikes_set.all().values_list('author__username', flat=True))
            return JsonResponse(data={'success': 'success', 'liked_usernames': liked_usernames})
    return JsonResponse(data={'error': 'Permission denied'})


def who_liked_child_comment(request, pk):
    if request.user.is_authenticated:
        child_comment = get_object_or_404(ChildComment, pk=pk)
        if child_comment.childcommentlikes_set.all().exists():
            liked_usernames = '|||'.join(child_comment.childcommentlikes_set.all().values_list('author__username', flat=True))
            print(liked_usernames)
            return JsonResponse(data={'success': 'success', 'liked_usernames': liked_usernames})
    return JsonResponse(data={'error': 'Permission denied'})
