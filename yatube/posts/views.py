from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from posts.utils import post_paginator

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    """Возвращает стартовую страницу с разбивкой по 10 постов."""
    template = 'posts/index.html'
    post_list = Post.objects.select_related('author', 'group').all()
    context = {'page_obj': post_paginator(request, post_list)}
    return render(request, template, context)


@login_required
def follow_index(request):
    """Возвращает страницу избранных авторов с разбивкой по 10 постов."""
    template = 'posts/follow.html'
    post_list = Post.objects.filter(author__following__user=request.user)
    context = {'page_obj': post_paginator(request, post_list)}
    return render(request, template, context)


def group_posts(request, slug):
    """Возвращает страницу группы с разбивкой по 10 постов."""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author').all()
    context = {
        'group': group,
        'page_obj': post_paginator(request, post_list),
    }
    return render(request, template, context)


def profile(request, username):
    """Возвращает страницу автора с разбивкой по 10 постов."""
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    check_author_is_user = author != request.user
    following = (request.user.is_authenticated
                 and author.following.filter(user=request.user).exists())
    post_list = author.posts.select_related('group').all()
    context = {
        'author': author,
        'page_obj': post_paginator(request, post_list),
        'following': following,
        'check_author_is_user': check_author_is_user,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Создание подписки на автора."""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отмена подписки на автора."""
    author = get_object_or_404(User, username=username)
    Follow.objects.get(
        user=request.user,
        author=author,
    ).delete()
    return redirect('posts:profile', username=username)


def post_detail(request, post_id):
    """Возвращает страницу с определенным постом."""
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.select_related('author').all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Создает новый пост."""
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=post.author)
        return render(request, 'posts/create_post.html', {'form': form})
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Редактирует n-ый пост."""
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id=post_id)
        return render(
            request,
            'posts/create_post.html',
            {'form': form, 'is_edit': True}
        )
    return render(
        request,
        'posts/create_post.html',
        {'form': form, 'is_edit': True}
    )


@login_required
def add_comment(request, post_id):
    """Добавляет комментарий к посту."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)
