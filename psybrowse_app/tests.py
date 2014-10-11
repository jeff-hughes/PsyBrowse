import datetime

from django.test import TestCase
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login

from django.contrib.auth.models import User
from psybrowse_app.models import (Author, Keyword, Journal, Article,
                                  UserProfile, Subscription)

class ArticleTests(TestCase):
    def test_create_article_with_one_author(self):
        """
        Should create a new Article, plus a new Author, both connected with
        each other.
        """
        article = Article(
            title='New article title',
            type=Article.ARTICLE,
            pub_date=(timezone.now() - datetime.timedelta(days=30)))
        article.save()
        a1 = article.authors.create(first_name='First', last_name='Last',
                                    initials='I.')

        author_set = article.authors.all()

        self.assertEquals(article.title, 'New article title')
        self.assertEquals(author_set[0].first_name, 'First')
        self.assertEquals(author_set[0].last_name, 'Last')

    def test_create_article_with_three_authors(self):
        """
        Should create a new Article, plus a new Author, both connected with
        each other.
        """
        article = Article(
            title='New article title',
            type=Article.ARTICLE,
            pub_date=(timezone.now() - datetime.timedelta(days=30)))
        article.save()
        a1 = article.authors.create(first_name='First', last_name='Last',
                                    initials='I.')
        a2 = article.authors.create(first_name='First2', last_name='Last2',
                                    initials='I.')
        a3 = article.authors.create(first_name='First3', last_name='Last3',
                                    initials='I.')

        author_set = article.authors.all()

        self.assertEquals(article.title, 'New article title')
        self.assertEquals(author_set[0].first_name, 'First')
        self.assertEquals(author_set[0].last_name, 'Last')
        self.assertEquals(author_set[1].first_name, 'First2')
        self.assertEquals(author_set[1].last_name, 'Last2')
        self.assertEquals(author_set[2].first_name, 'First3')
        self.assertEquals(author_set[2].last_name, 'Last3')

    def test_create_article_with_journal(self):
        """
        Should create a new Article, plus a new Journal, both connected with
        each other.
        """
        article = Article(
            title='New article title',
            type=Article.ARTICLE,
            pub_date=(timezone.now() - datetime.timedelta(days=30)))
        article.save()
        j = Journal(title='Fake Journal')
        j.save()
        article.journal = j

        self.assertEquals(article.title, 'New article title')
        self.assertEquals(article.journal.title, 'Fake Journal')

class AuthorTests(TestCase):
    def test_create_author_with_initials(self):
        """Should create an Author with initials."""
        author = Author(first_name='First', last_name='Last', initials='I.')
        author.save()

        self.assertEquals(author.first_name, 'First')
        self.assertEquals(author.last_name, 'Last')
        self.assertEquals(author.initials, 'I.')

    def test_create_author_without_initials(self):
        """Should create an Author without initials."""
        author = Author(first_name='First', last_name='Last')
        author.save()

        self.assertEquals(author.first_name, 'First')
        self.assertEquals(author.last_name, 'Last')
        self.assertEquals(author.initials, None)


class IndexViewTests(TestCase):
    def test_index_view_with_no_articles(self):
        """If no Articles exist, an appropriate message should be displayed."""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No articles are available.')
        self.assertQuerysetEqual(response.context['articles_authors'], [])

    def test_index_view_with_articles(self):
        """Recent Articles should be displayed on the index page."""
        article = Article(
            title='New article title',
            type=Article.ARTICLE,
            pub_date=(timezone.now() - datetime.timedelta(days=30)))
        article.save()

        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['articles_authors'][0][0].title,
                                          'New article title')

class DetailViewTests(TestCase):
    def test_article_detail_with_no_article(self):
        """If Article does not exist, should return 404."""
        response = self.client.get(reverse('article detail', args=(15,)))
        self.assertEqual(response.status_code, 404)

    def test_author_detail_with_no_author(self):
        """If Author does not exist, should return 404."""
        response = self.client.get(reverse('author detail', args=(15,)))
        self.assertEqual(response.status_code, 404)

    def test_journal_detail_with_no_journal(self):
        """If Journal does not exist, should return 404."""
        response = self.client.get(reverse('journal detail', args=(15,)))
        self.assertEqual(response.status_code, 404)

    def test_user_detail_with_no_user(self):
        """If User does not exist, should return 404."""
        response = self.client.get(reverse('user detail', args=(15,)))
        self.assertEqual(response.status_code, 404)

class SearchViewTests(TestCase):
    def test_search_with_no_results(self):
        """
        If search produces no results, an appropriate message should be
        displayed.
        """
        response = self.client.post(reverse('search'), {'search': 'psychology'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your search returned no results.')
        self.assertQuerysetEqual(response.context['articles_authors'], [])

    def test_search_with_results(self):
        """Should produce list of results."""
        article = Article(
            title='Psychology article',
            type=Article.ARTICLE,
            pub_date=(timezone.now() - datetime.timedelta(days=30)))
        article.save()

        response = self.client.post(reverse('search'), {'search': 'psychology'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['articles_authors'][0][0].title,
                                          'Psychology article')

    def test_advanced_search_with_no_results(self):
        pass

    def test_advanced_search_with_results(self):
        pass

class UserViewTests(TestCase):
    def test_register_invalid_user(self):
        pass

    def test_register_valid_user(self):
        pass

class SubscribeViewTests(TestCase):
    def setUp(self):
        """Create a test User and UserProfile for subscriptions."""
        self.user = User.objects.create(username='testuser',
                                        password='password')
        self.user.set_password('password')
        self.user.save()

        self.user_profile = UserProfile(user=self.user)
        self.user_profile.save()

        user = authenticate(username='testuser', password='password')
        login = self.client.login(username='testuser', password='password')

    def tearDown(self):
        """Delete test User and UserProfile."""
        self.user_profile.delete()
        self.user.delete()

    def test_subscribe_unsubscribe_keyword(self):
        keyword = Keyword(value='keyword')
        keyword.save()

        response = self.client.get(
            reverse('subscribe'),
            {'type': 'keyword', 'id': keyword.pk})

        self.assertEqual(response.status_code, 302)
            # Should redirect upon success
        subs = self.user_profile.subscription_set.all()
        self.assertEqual(subs[0].sub_type, Subscription.KEYWORD)
        self.assertEqual(subs[0].keyword.pk, keyword.pk)

        response2 = self.client.get(
            reverse('unsubscribe'),
            {'type': 'keyword', 'id': keyword.pk})

        self.assertEqual(response2.status_code, 302)
            # Should redirect upon success
        self.assertEqual(self.user_profile.subscription_set.count(), 0)

    def test_subscribe_unsubscribe_author(self):
        author = Author(first_name='First', last_name='Last')
        author.save()

        response = self.client.get(
            reverse('subscribe'),
            {'type': 'author', 'id': author.pk})

        self.assertEqual(response.status_code, 302)
            # Should redirect upon success
        subs = self.user_profile.subscription_set.all()
        self.assertEqual(subs[0].sub_type, Subscription.AUTHOR)
        self.assertEqual(subs[0].author.pk, author.pk)

        response2 = self.client.get(
            reverse('unsubscribe'),
            {'type': 'author', 'id': author.pk})

        self.assertEqual(response2.status_code, 302)
            # Should redirect upon success
        self.assertEqual(self.user_profile.subscription_set.count(), 0)

    def test_subscribe_unsubscribe_search_string(self):
        search_string = 'test search'

        response = self.client.get(
            reverse('subscribe'),
            {'type': 'search_string', 'value': search_string})

        self.assertEqual(response.status_code, 302)
            # Should redirect upon success
        subs = self.user_profile.subscription_set.all()
        self.assertEqual(subs[0].sub_type, Subscription.SEARCH_STRING)
        self.assertEqual(subs[0].search_string, search_string)

        response2 = self.client.get(
            reverse('unsubscribe'),
            {'type': 'search_string', 'value': search_string})

        self.assertEqual(response2.status_code, 302)
            # Should redirect upon success
        self.assertEqual(self.user_profile.subscription_set.count(), 0)

    def test_subscribe_unsubscribe_article(self):
        article = Article(
            title='New article title',
            type=Article.ARTICLE,
            pub_date=(timezone.now() - datetime.timedelta(days=30)))
        article.save()

        response = self.client.get(
            reverse('subscribe'),
            {'type': 'article', 'id': article.pk})

        self.assertEqual(response.status_code, 302)
            # Should redirect upon success
        subs = self.user_profile.subscription_set.all()
        self.assertEqual(subs[0].sub_type, Subscription.ARTICLE)
        self.assertEqual(subs[0].article.pk, article.pk)

        response2 = self.client.get(
            reverse('unsubscribe'),
            {'type': 'article', 'id': article.pk})

        self.assertEqual(response2.status_code, 302)
            # Should redirect upon success
        self.assertEqual(self.user_profile.subscription_set.count(), 0)

    def test_subscribe_unsubscribe_journal(self):
        journal = Journal(title='Fake Journal')
        journal.save()

        response = self.client.get(
            reverse('subscribe'),
            {'type': 'journal', 'id': journal.pk})

        self.assertEqual(response.status_code, 302)
            # Should redirect upon success
        subs = self.user_profile.subscription_set.all()
        self.assertEqual(subs[0].sub_type, Subscription.JOURNAL)
        self.assertEqual(subs[0].journal.pk, journal.pk)

        response2 = self.client.get(
            reverse('unsubscribe'),
            {'type': 'journal', 'id': journal.pk})

        self.assertEqual(response2.status_code, 302)
            # Should redirect upon success
        self.assertEqual(self.user_profile.subscription_set.count(), 0)