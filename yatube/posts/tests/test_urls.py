from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='other')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, в котором много букв'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        cache.clear()

    def test_unauth_url_exists_at_desired_location(self):
        """Страницы для любого пользователя соответсвуют
        ожидаемым HTTP-статусам.
        """
        url_names = {
            '/': HTTPStatus.OK,
            f'/group/{PostURLTests.group.slug}/': HTTPStatus.OK,
            f'/profile/{PostURLTests.user.username}/': HTTPStatus.OK,
            f'/posts/{PostURLTests.post.pk}/': HTTPStatus.OK,
            f'/posts/{PostURLTests.post.pk}/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.FOUND,
            f'/posts/{PostURLTests.post.pk}/comment/': HTTPStatus.FOUND,
            '/follow/': HTTPStatus.FOUND,
            f'/profile/{PostURLTests.user.username}/follow/': HTTPStatus.FOUND,
            f'/profile/{PostURLTests.user.username}/unfollow/':
                HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for address, http_status in url_names.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, http_status)

    def test_auth_url_exists_at_desired_location(self):
        """Соответсвующие страницы доступны авториз. пользователю."""
        url_names = {
            f'/posts/{PostURLTests.post.pk}/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
        }
        for address, http_status in url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, http_status)

    def test_create_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /posts/<post_id>/edit/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.client.get(
            f'/posts/{PostURLTests.post.pk}/edit/',
            follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{PostURLTests.post.pk}/edit/'
        )

    def test_post_edit_url_redirect_unauthor_on_post_detail(self):
        """Страница по адресу /posts/<post_id>/edit/ перенаправит не автора
        поста на страницу этого поста.
        """
        self.authorized_client.force_login(PostURLTests.user2)
        response = self.authorized_client.get(
            f'/posts/{PostURLTests.post.pk}/edit/',
            follow=True
        )
        self.assertRedirects(
            response, f'/posts/{PostURLTests.post.pk}/'
        )

    def test_comment_post_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /posts/<post_id>/comment/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.client.get(
            f'/posts/{PostURLTests.post.pk}/comment/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{PostURLTests.post.pk}/comment/'
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.pk}/': 'posts/post_detail.html',
            f'/posts/{PostURLTests.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
            '/unexisting_page/': 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
