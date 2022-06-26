from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test-author')
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.author,
            id='10',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_user = Client()
        self.authorized_client_author = Client()
        self.authorized_client_user.force_login(self.user)
        self.authorized_client_author.force_login(self.author)
        cache.clear()

    def test_http_status_correct_guest_template(self):
        templates_url_names = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user}/',
            f'/posts/{self.post.id}/',
        ]
        for url in templates_url_names:
            response = self.guest_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post(self):
        response = self.authorized_client_user.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post(self):
        response = self.authorized_client_author.get(
            f'/posts/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_error_404(self):
        response = self.guest_client.get('unesiating_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
