from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    """Группы, с описанием их тематики."""

    title = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name="Сокращенное название для URL"
    )
    description = models.TextField(verbose_name="Описание")

    def __str__(self):
        """Метод возвращающий строку title."""
        return self.title


class Post(models.Model):
    """Текстовые посты, с указанием автора, даты создания и группы."""

    text = models.TextField(
        'Текст поста',
        help_text='Текст нового поста',
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        help_text='Загрузите картинку'
    )

    def __str__(self):
        """выводим текст поста"""
        return self.text[:settings.CHARS_LIMIT]

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'


class Comment(models.Model):
    """Комментарии к постам."""

    text = models.TextField(
        'Комментарий',
        help_text='Введите текст комментария',
    )
    created = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )


class Follow(models.Model):
    """Подписки на авторов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )
