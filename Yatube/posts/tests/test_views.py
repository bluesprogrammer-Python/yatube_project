from django import forms
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from Yatube.settings import VIEW_COEFF

from posts.models import Follow, Group, Post, User

POSTS_CREATED = 13
SLUG = 'slug'
USERNAME = 'username'
POST_ID = 'post_id'


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
            description='test-description'
        )
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.user,
            group=cls.group
        )
        cls.new_post = Post.objects.create(
            text='test-cache',
            group=cls.group,
            author=cls.user
        )

    def setUp(self):
        self.author = CacheTests.user
        self.author_client = Client()
        self.author_client.force_login(self.author)
        cache.clear()

    def test_cache_index_page(self):
        response = self.author_client.get(reverse('posts:index'))
        self.assertContains(response, self.new_post)
        self.new_post.delete()
        response = self.author_client.get(reverse('posts:index'))
        self.assertContains(response, self.new_post)
        cache.clear()
        response = self.author_client.get(reverse('posts:index'))
        self.assertNotContains(response, self.new_post)


class GroupPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test')
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-group',
            description='test-describe',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test-text',
            group=cls.group,
        )
        cls.group1 = Group.objects.create(
            title='test-title1',
            slug='test-group1',
            description='test-describe1',
        )
        cls.post1 = Post.objects.create(
            author=cls.user,
            text='test-text1',
            group=cls.group1,
        )

    def setUp(self):
        self.user = User.objects.create_user(username='test-user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)
        cache.clear()

    def test_new_post_with_group_shown_on_group_list(self):
        response = self.authorized_client.get(reverse('posts:group_list',
                                              kwargs={SLUG:
                                                      f'{self.group.slug}'}))
        post_text = response.context['page_obj'][0].text
        expected_text = GroupPagesTests.post.text
        self.assertEqual(post_text, expected_text)

    def test_new_post_with_group_doesnt_shown_on_other_group_list(self):
        response = self.authorized_client.get(reverse('posts:group_list',
                                              kwargs={SLUG:
                                                      f'{self.group1.slug}'})
                                              )
        expected_text = GroupPagesTests.post.text
        self.assertNotEqual(expected_text,
                            response.context['page_obj'][0].text
                            )


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.other_user = User.objects.create_user(username='test-user1')
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.user,
            group=cls.group,
        )
        cls.follower = Follow.objects.create(
            author=cls.user,
            user=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.other_authorized_client = Client()
        self.other_authorized_client.force_login(self.other_user)

    def test_delete_follower(self):
        Follow.objects.create(
            user=self.other_user,
            author=self.user
        )
        followers_count = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={USERNAME: self.user.username})
        )
        self.assertEqual(Follow.objects.count(), followers_count - 1)

    def test_add_follower(self):
        followers_count = Follow.objects.count()
        self.other_authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={USERNAME: self.user.username})
        )
        self.assertEqual(Follow.objects.count(), followers_count + 1)
        self.assertTrue(Follow.objects.filter(
            user=self.other_user,
            author=self.user,
        ).exists()
        )

    def test_adding_to_favorites(self):
        followers_count = Follow.objects.count()
        self.other_authorized_client.get(
            reverse('posts:profile_follow', kwargs={USERNAME:
                                                    self.user.username})
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        follow_index = response.context['page_obj'][0]
        self.assertEqual(follow_index, self.post)
        self.assertEqual(Follow.objects.count(), followers_count + 1)

    def test_authorized_user_unfollow(self):
        Follow.objects.create(
            author=self.other_user,
            user=self.other_user
        )
        new_user = User.objects.create(username='new-test-user')
        new_authorized_client = Client()
        new_authorized_client.force_login(new_user)
        new_authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={USERNAME: self.other_user.username}
        ))
        self.assertTrue(
            Follow.objects.filter(
                author=self.other_user,
                user=self.other_user
            ).exists()
        )


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-group',
            description='test-describe',
        )
        for i in range(13):
            cls.post = Post.objects.create(
                author=cls.user,
                text='test-text',
                group=cls.group,
            )
        cls.urls = {
            1: reverse('posts:index'),
            2: reverse('posts:group_list', kwargs={SLUG:
                                                   cls.group.slug}),
            3: reverse('posts:profile', kwargs={USERNAME: cls.user}),
        }

    def setUp(self):
        self.user = User.objects.create_user(username='test_name')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)
        cache.clear()

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={SLUG: f'{self.group.slug}'}):
            'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={USERNAME: self.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={POST_ID: f'{self.post.pk}'}):
            'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={POST_ID: f'{self.post.pk}'}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_views_index_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_post = response.context['page_obj'][0]
        first_post_text = first_post.text
        first_post_author = first_post.author.username
        first_post_group = first_post.group
        self.assertEqual(first_post_text, self.post.text)
        self.assertEqual(first_post_author, self.post.author.username)
        self.assertEqual(first_post_group, self.post.group)

    def test_views_groups_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={SLUG: f'{self.group.slug}'}
                    )
        )
        group = response.context.get('group')
        self.assertIsInstance(group, Group)
        group_title = group.title
        group_slug = group.slug
        group_description = group.description
        self.assertEqual(group_title, self.group.title)
        self.assertEqual(group_slug, self.group.slug)
        self.assertEqual(group_description, self.group.description)

    def test_views_profile_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={USERNAME: f'{self.post.author}'}
                    )
        )
        first_post = response.context['page_obj'][0]
        first_post_text = first_post.text
        first_post_author = first_post.author.username
        first_post_group = first_post.group
        self.assertEqual(first_post_text, self.post.text)
        self.assertEqual(first_post_author, self.post.author.username)
        self.assertEqual(first_post_group, self.post.group)

    def test_views_post_detail_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_detail',
                                              kwargs={POST_ID:
                                                      f'{self.post.pk}'}))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)

    def test_post_create_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_group_excisting_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(f'{self.post.id}',)))
        first_object = response.context['post']
        task_group_0 = first_object.group
        self.assertEqual(task_group_0, self.post.group)

    def test_new_post_with_group_shown_on_index(self):
        response = self.authorized_client.get(reverse('posts:index'))
        post_text = response.context['page_obj'][0].text
        expected_text = self.post.text
        self.assertEqual(post_text, expected_text)

    def test_new_post_with_group_shown_on_profile(self):
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={USERNAME:
                                                      PostPagesTests.user})
                                              )
        post_text = response.context['page_obj'][0].text
        expected_text = self.post.text
        self.assertEqual(post_text, expected_text)

    def test_first_page_contains_ten_records(self):
        for i in self.urls.keys():
            with self.subTest(i=i):
                response = self.client.get(self.urls[i])
                self.assertEqual(len(
                    response.context.get('page_obj').object_list), VIEW_COEFF)

    def test_second_page_contains_three_records(self):
        for i in PostPagesTests.urls.keys():
            with self.subTest(i=i):
                response = self.client.get(self.urls[i] + '?page=2')
                self.assertEqual(len(
                    response.context.get('page_obj').object_list),
                    POSTS_CREATED - VIEW_COEFF)
