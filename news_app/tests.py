from django.test import TestCase
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from .models import User, Publisher, Article
from .signals import create_groups_and_permissions


class UserGroupAssignmentTest(TestCase):

    def setUp(self):
        create_groups_and_permissions()

    def test_reader_assigned_to_reader_group(self):
        user = User.objects.create_user(username='reader1', password='pass', role=User.READER)
        self.assertTrue(user.groups.filter(name='Reader').exists())

    def test_journalist_assigned_to_journalist_group(self):
        user = User.objects.create_user(username='journalist1', password='pass', role=User.JOURNALIST)
        self.assertTrue(user.groups.filter(name='Journalist').exists())

    def test_editor_assigned_to_editor_group(self):
        user = User.objects.create_user(username='editor1', password='pass', role=User.EDITOR)
        self.assertTrue(user.groups.filter(name='Editor').exists())


class SubscribedArticlesAPITest(TestCase):

    def setUp(self):
        create_groups_and_permissions()

        self.publisher = Publisher.objects.create(name='Tech Weekly', website='http://techweekly.com')

        self.journalist = User.objects.create_user(
            username='journalist_a', password='pass', role=User.JOURNALIST
        )

        self.reader = User.objects.create_user(
            username='reader_a', password='pass', role=User.READER
        )
        self.reader.subscribed_publishers.add(self.publisher)

        self.journalist_subscriber = User.objects.create_user(
            username='reader_b', password='pass', role=User.READER
        )
        self.journalist_subscriber.subscribed_journalists.add(self.journalist)

        self.unsubscribed_reader = User.objects.create_user(
            username='reader_c', password='pass', role=User.READER
        )

        self.article_from_publisher = Article.objects.create(
            title='Publisher Article',
            content='Content about tech.',
            author=self.journalist,
            publisher=self.publisher,
            status=Article.APPROVED,
        )

        self.article_from_journalist = Article.objects.create(
            title='Independent Article',
            content='Content by journalist.',
            author=self.journalist,
            publisher=None,
            status=Article.APPROVED,
        )

        self.draft_article = Article.objects.create(
            title='Draft Article',
            content='Not yet published.',
            author=self.journalist,
            publisher=self.publisher,
            status=Article.DRAFT,
        )

        self.client = APIClient()

    def test_reader_subscribed_to_publisher_sees_publisher_article(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(reverse('api_articles'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [a['title'] for a in response.data]
        self.assertIn('Publisher Article', titles)

    def test_reader_subscribed_to_journalist_sees_journalist_article(self):
        self.client.force_authenticate(user=self.journalist_subscriber)
        response = self.client.get(reverse('api_articles'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [a['title'] for a in response.data]
        self.assertIn('Independent Article', titles)

    def test_unsubscribed_reader_sees_no_articles(self):
        self.client.force_authenticate(user=self.unsubscribed_reader)
        response = self.client.get(reverse('api_articles'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_draft_articles_not_returned_in_api(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(reverse('api_articles'))
        titles = [a['title'] for a in response.data]
        self.assertNotIn('Draft Article', titles)

    def test_unauthenticated_user_denied(self):
        response = self.client.get(reverse('api_articles'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ArticleApprovalWorkflowTest(TestCase):

    def setUp(self):
        create_groups_and_permissions()
        self.journalist = User.objects.create_user(
            username='j_test', password='pass', role=User.JOURNALIST
        )
        self.editor = User.objects.create_user(
            username='e_test', password='pass', role=User.EDITOR
        )
        self.article = Article.objects.create(
            title='Test Article',
            content='Some content.',
            author=self.journalist,
            status=Article.PENDING,
        )

    def test_editor_can_approve_article(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse('approve_article', args=[self.article.pk]),
            {'action': 'approve'}
        )
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, Article.APPROVED)
        self.assertEqual(self.article.approved_by, self.editor)

    def test_non_editor_cannot_approve_article(self):
        self.client.force_login(self.journalist)
        response = self.client.post(
            reverse('approve_article', args=[self.article.pk]),
            {'action': 'approve'}
        )
        self.assertEqual(response.status_code, 403)
        self.article.refresh_from_db()
        self.assertNotEqual(self.article.status, Article.APPROVED)


class SignupViewTest(TestCase):
    """Validate account registration behavior from the public signup page."""

    def test_signup_page_is_accessible(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)

    def test_signup_creates_reader_and_redirects_to_login(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'new_reader',
                'email': 'reader@example.com',
                'password': 'StrongPass123!',
                'confirm_password': 'StrongPass123!',
                'role': User.READER,
            }
        )
        self.assertRedirects(response, reverse('login'))
        created_user = User.objects.get(username='new_reader')
        self.assertEqual(created_user.role, User.READER)

    def test_signup_creates_journalist_when_role_selected(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'new_journalist',
                'email': 'journalist@example.com',
                'password': 'StrongPass123!',
                'confirm_password': 'StrongPass123!',
                'role': User.JOURNALIST,
            }
        )
        self.assertRedirects(response, reverse('login'))
        created_user = User.objects.get(username='new_journalist')
        self.assertEqual(created_user.role, User.JOURNALIST)

    def test_signup_creates_editor_when_role_selected(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'new_editor',
                'email': 'editor@example.com',
                'password': 'StrongPass123!',
                'confirm_password': 'StrongPass123!',
                'role': User.EDITOR,
            }
        )
        self.assertRedirects(response, reverse('login'))
        created_user = User.objects.get(username='new_editor')
        self.assertEqual(created_user.role, User.EDITOR)

    def test_signup_with_invalid_role_falls_back_to_reader(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'invalid_role_user',
                'email': 'invalid@example.com',
                'password': 'StrongPass123!',
                'confirm_password': 'StrongPass123!',
                'role': 'admin',
            }
        )
        self.assertRedirects(response, reverse('login'))
        created_user = User.objects.get(username='invalid_role_user')
        self.assertEqual(created_user.role, User.READER)

    def test_signup_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'bad_reader',
                'email': 'reader@example.com',
                'password': 'StrongPass123!',
                'confirm_password': 'WrongPass123!',
                'role': User.READER,
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='bad_reader').exists())

    def test_signup_rejects_duplicate_username(self):
        User.objects.create_user(username='existing', password='pass', role=User.READER)

        response = self.client.post(
            reverse('signup'),
            {
                'username': 'existing',
                'email': 'reader@example.com',
                'password': 'StrongPass123!',
                'confirm_password': 'StrongPass123!',
                'role': User.READER,
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username='existing').count(), 1)

    def test_signup_requires_email(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'no_email_user',
                'email': '',
                'password': 'StrongPass123!',
                'confirm_password': 'StrongPass123!',
                'role': User.READER,
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='no_email_user').exists())


class RoleLoginRedirectTest(TestCase):
    """Ensure users land on the correct dashboard after login."""

    def setUp(self):
        create_groups_and_permissions()
        self.reader = User.objects.create_user(
            username='reader_login',
            password='pass',
            role=User.READER,
            email='reader@login.test',
        )
        self.journalist = User.objects.create_user(
            username='journalist_login',
            password='pass',
            role=User.JOURNALIST,
            email='journalist@login.test',
        )
        self.editor = User.objects.create_user(
            username='editor_login',
            password='pass',
            role=User.EDITOR,
            email='editor@login.test',
        )

    def test_reader_redirected_to_reader_dashboard(self):
        response = self.client.post(
            reverse('login'),
            {'username': self.reader.username, 'password': 'pass'},
        )
        self.assertRedirects(response, reverse('reader_dashboard'))

    def test_journalist_redirected_to_journalist_dashboard(self):
        response = self.client.post(
            reverse('login'),
            {'username': self.journalist.username, 'password': 'pass'},
        )
        self.assertRedirects(response, reverse('journalist_dashboard'))

    def test_editor_redirected_to_editor_dashboard(self):
        response = self.client.post(
            reverse('login'),
            {'username': self.editor.username, 'password': 'pass'},
        )
        self.assertRedirects(response, reverse('editor_dashboard'))
