from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """Создает форму по модели Post для заполнения шаблона."""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    """Создает форму по модели Comment."""
    class Meta:
        model = Comment
        fields = ('text',)
