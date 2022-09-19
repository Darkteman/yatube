from django.conf import settings
from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, в котором много букв'
        )

    def test_models_have_correct_object_names(self):
        """Проверяет, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        expected_group_title = group.title
        self.assertEqual(
            expected_group_title,
            str(group),
            '__str__ группы отображается не верно'
        )
        post = PostModelTest.post
        expected_post_text = post.text[:settings.CHARS_LIMIT]
        self.assertEqual(
            expected_post_text,
            str(post),
            '__str__ поста отображается не верно'
        )

    def test_verbose_name_post(self):
        """Проверяет, что verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Картинка',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text_post(self):
        """Проверяет, что help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Загрузите картинку',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
