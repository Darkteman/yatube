import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Тестовое описание группы 2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, в котором много букв',
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        """Валидная форма создает новый пост."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        posts_before = list(Post.objects.values_list('id', flat=True))
        form_data = {
            'text': 'Тестовый пост 2',
            'group': PostCreateFormTests.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': PostCreateFormTests.user.username}
        ))
        self.assertEqual(Post.objects.count(), len(posts_before) + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                author=PostCreateFormTests.user,
                image=f'posts/{uploaded.name}'
            ).exclude(id__in=posts_before).exists()
        )

    def test_edit_post(self):
        """Валидная форма редактирует n-ый пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост редактированный',
            'group': PostCreateFormTests.group2.id,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostCreateFormTests.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': PostCreateFormTests.post.id}
        ))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                id=PostCreateFormTests.post.id,
                text=form_data['text'],
                group=form_data['group'],
                author=PostCreateFormTests.user,
            ).exists()
        )

    def test_create_comment(self):
        """Валидная форма создает новый комментарий."""
        comments_before = list(Comment.objects.values_list('id', flat=True))
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostCreateFormTests.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': PostCreateFormTests.post.id}
        ))
        self.assertEqual(Comment.objects.count(), len(comments_before) + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                author=PostCreateFormTests.user,
                post=PostCreateFormTests.post
            ).exclude(id__in=comments_before).exists()
        )
