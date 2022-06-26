import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

POST_ID = 'post_id'


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.user,
            group=cls.group,
        )
        cls.form = PostForm()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.form_data = {
            'text': 'test-text',
            'group': cls.group.pk,
            'author': cls.user.username,
            'image': uploaded,
        }
        cls.comment_form = CommentForm()
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='test-text'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.form_data = {
            'text': self.post.text,
            'group': self.group.pk,
        }

        self.comment_form_data = {
            'text': self.comment.text,
        }

    def test_create_post(self):
        post_count = Post.objects.count()
        response_first = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        response_second = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={POST_ID: f'{self.post.id}'}))
        first_object = response_second.context['post']
        self.assertRedirects(response_first, reverse('posts:profile',
                                                     args=[f'{self.user}']))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(first_object.image, self.post.image)
        self.assertTrue(
            Post.objects.filter(
                text='test-text',
                group=self.group.pk,
                author=self.user,
            ).exists()
        )

    def test_edit_post(self):
        form_data = {
            'text': self.post.text,
            'group': self.group.slug,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(f'{self.post.id}',)),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                group=self.post.group,
                text=self.post.text,
            ).exists()
        )

    def test_auth_create_comment(self):
        comments_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={POST_ID: f'{self.post.pk}'}),
            data=self.comment_form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={POST_ID: f'{self.post.pk}'}))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=self.comment.text,
            ).exists()
        )

    def test_not_auth_create_comment(self):
        comments_count = Comment.objects.count()
        response = self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={POST_ID: f'{self.post.pk}'}),
            data=self.comment_form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('users:login') + '?next='
                             + reverse('posts:add_comment',
                             kwargs={POST_ID: f'{self.post.pk}'}))
        self.assertEqual(Comment.objects.count(), comments_count)
