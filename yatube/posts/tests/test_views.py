import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post, User

NUMBER_OF_POSTS_TEST_PAGINATOR = 13
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, в котором много букв',
            group=cls.group,
            image=cls.image,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug': PostPagesTests.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': PostPagesTests.user.username}):
                'posts/profile.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': PostPagesTests.post.id}):
                'posts/create_post.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': PostPagesTests.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
            reverse('posts:follow_index'):
                'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_comment_is_in_the_post_page(self):
        """Новый комментарий попадает на страницу поста."""
        comment = Comment.objects.create(
            text='Новый комментарий',
            author=PostPagesTests.user,
            post=PostPagesTests.post,
        )
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': PostPagesTests.post.id}
        ))
        object = response.context['comments'][0]
        self.assertEqual(
            object.id,
            comment.id
        )

    def test_post_is_in_follower_profile(self):
        """Новый пост отображается у подписчика
        и не отображается у неподпичика."""
        follower_user = User.objects.create_user(username='follower_user')
        unfollower_user = User.objects.create_user(username='unfollower_user')
        Follow.objects.create(
            user=follower_user,
            author=PostPagesTests.user,
        )
        new_post = Post.objects.create(
            text='Новый тестовый пост',
            author=PostPagesTests.user,
            group=PostPagesTests.group,
        )
        self.authorized_client.force_login(follower_user)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        object = response.context['page_obj'][0]
        self.assertEqual(
            object.id,
            new_post.id
        )
        self.authorized_client.force_login(unfollower_user)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        object = response.context['page_obj']
        self.assertFalse(object)

    def test_ability_following(self):
        """Возможность подписываться на других пользователей"""
        follower_user = User.objects.create_user(username='follower_user')
        self.authorized_client.force_login(follower_user)
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostPagesTests.user.username}
        ))
        follow = Follow.objects.get(
            user=follower_user,
            author=PostPagesTests.user,
        )
        self.assertTrue(follow)

    def test_ability_unfollowing(self):
        """Возможность отписываться от других пользователей"""
        follower_user = User.objects.create_user(username='follower_user')
        self.authorized_client.force_login(follower_user)
        Follow.objects.create(
            user=follower_user,
            author=PostPagesTests.user,
        )
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': PostPagesTests.user.username}
        ))
        unfollow = Follow.objects.filter(
            user=follower_user,
            author=PostPagesTests.user,
        ).exists()
        self.assertFalse(unfollow)

    def test_post_is_in_the_first_place(self):
        """Новый пост попадает на первое место страниц."""
        new_post = Post.objects.create(
            text='Новый тестовый пост',
            author=PostPagesTests.user,
            group=PostPagesTests.group,
        )
        pages_names = {
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug': PostPagesTests.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': PostPagesTests.user.username}),
        }
        for reverse_name in pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                self.assertEqual(
                    first_object.id,
                    new_post.id
                )

    def checking_context(self, post):
        """Проверка атрибутов поста."""
        self.assertEqual(post.id, PostPagesTests.post.id)
        self.assertEqual(post.text, PostPagesTests.post.text)
        self.assertEqual(post.author, PostPagesTests.post.author)
        self.assertEqual(post.group, PostPagesTests.group)
        self.assertEqual(post.image.name, f'posts/{PostPagesTests.image.name}')

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.checking_context(post)

    def test_follow_index_page_show_correct_context(self):
        """Шаблон follow_index сформирован с правильным контекстом."""
        follower_user = User.objects.create_user(username='follower_user')
        self.authorized_client.force_login(follower_user)
        Follow.objects.create(
            user=follower_user,
            author=PostPagesTests.user,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.checking_context(post)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': PostPagesTests.group.slug}
        ))
        self.assertEqual(response.context.get('group').title,
                         PostPagesTests.group.title)
        self.assertEqual(response.context.get('group').slug,
                         PostPagesTests.group.slug)
        self.assertEqual(response.context.get('group').description,
                         PostPagesTests.group.description)
        post = response.context['page_obj'][0]
        self.checking_context(post)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': PostPagesTests.user.username}
        ))
        self.assertEqual(response.context.get('author').username,
                         PostPagesTests.user.username)
        self.assertIsNotNone(response.context.get('following'))
        self.assertIsNotNone(response.context.get('check_author_is_user'))
        post = response.context['page_obj'][0]
        self.checking_context(post)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': PostPagesTests.post.id}
        ))
        post = response.context['post']
        self.checking_context(post)
        form_field = response.context.get('form').fields.get('text')
        self.assertIsInstance(form_field, forms.fields.CharField)

    def test_post_does_not_exist_in_any_group(self):
        """Тестовый пост не попадает на стр. другой группы."""
        new_group = Group.objects.create(
            title='Какая-то группа',
            slug='any_slug',
            description='Другое описание',
        )
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': new_group.slug})
        )
        object = response.context['page_obj']
        self.assertFalse(object)

    def test_form_pages_show_correct_context(self):
        """Шаблоны с формами сформированы с правильным контекстом."""
        pages_names = {
            reverse('posts:post_create'),
            reverse('posts:post_edit',
                    kwargs={'post_id': PostPagesTests.post.id}),
        }
        for reverse_name in pages_names:
            response = self.authorized_client.get(reverse_name)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
                'image': forms.fields.ImageField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)
            if reverse_name == reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTests.post.id}
            ):
                self.assertTrue(response.context.get('is_edit'))

    def test_cache_index(self):
        """Тест кеширования страницы index"""
        new_post = Post.objects.create(
            text='Новый тестовый пост',
            author=PostPagesTests.user,
            group=PostPagesTests.group,
        )
        first_index = self.authorized_client.get(reverse('posts:index'))
        Post.objects.get(id=new_post.id).delete()
        second_index = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_index.content, second_index.content)
        cache.clear()
        third_index = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_index.content, third_index.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        for i in range(NUMBER_OF_POSTS_TEST_PAGINATOR):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост №{i+1}, в котором много букв',
                group=cls.group,
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Проверка пагинатора на 1ой странице."""
        reverses = {
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug': PaginatorViewsTest.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.user.username}),
        }
        for rev in reverses:
            response = self.authorized_client.get(rev)
            self.assertEqual(
                len(response.context['page_obj']),
                settings.NUMBER_OF_POSTS
            )

    def test_second_page_contains_three_records(self):
        """Проверка пагинатора на 2ой странице."""
        reverses = {
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug': PaginatorViewsTest.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.user.username}),
        }
        for rev in reverses:
            response = self.authorized_client.get(rev + '?page=2')
            self.assertEqual(
                len(response.context['page_obj']),
                NUMBER_OF_POSTS_TEST_PAGINATOR - settings.NUMBER_OF_POSTS
            )
