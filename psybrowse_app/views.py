import urllib
import datetime
import json
from collections import defaultdict

from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth import logout, get_user
from django.contrib.auth.decorators import login_required

from django.contrib.auth.models import User
from psybrowse_app.models import Author, Keyword, Journal, Article, UserProfile, Subscription
from psybrowse_app.forms import SearchForm, AdvSearchForm, CustomUserCreationForm

def _is_subscribed(request, sub_type, sub_item):
    """Returns True if request.user is logged in and subscribed to 'sub_item' of ('sub_type'), False otherwise."""
    is_subscribed = False
    if request.user.is_authenticated():
        terms = {}
        if isinstance(sub_type, int):
            s_type = Subscription.TYPE_DICT[sub_type]  # convert numeric subscription type to text value
        else:
            s_type = sub_type
        terms[s_type] = sub_item
        terms['users'] = get_user(request).userprofile
        sub_count = Subscription.objects.filter(**terms).count()
        if sub_count > 0:
            is_subscribed = True
    return is_subscribed


def _format_article_detail(subscription, article):
    """
    Takes raw Subscription and Article objects and returns a formatted tuple: (subscription type, subscription display,
    subscription item URL, article, authors list). If 'subscription' is a string rather than a Subscription object, the
    subscription type and URL will be None, and the subscription display will be the string.
    """
    if isinstance(subscription, Subscription):
        sub_info = _format_subscription_detail(subscription)
    else:
        sub_info = (None, subscription, None)

    authors = article.authors.all()
    authors_list = [(a.pk, a.get_name()) for a in authors]

    return (sub_info[0], sub_info[1], sub_info[2], article, authors_list)


def _format_subscription_detail(subscription):
    """
    Takes raw Subscription and returns a formatted tuple: (subscription type, subscription display, subscription
    item URL).
    """
    s_type = subscription.get_formatted_type(capitalized=False)
    item = subscription.get_item()
    if subscription.sub_type == Subscription.SEARCH_STRING:
        item_url = '{:s}?s={:s}'.format(reverse('search'), urllib.quote_plus(item))
        display = item
    else:
        item_url = reverse(s_type + ' detail', args=(item.pk,))
        display = unicode(item)
    return (s_type.capitalize(), display, item_url)


def index(request):
    """
    The index view displays a list of recent articles if the user is not registered/logged in, or the user's custom
    newsfeed if they are logged in.
    """
    NUM_ARTICLES = 15
    articles = []

    # if user is logged in, we get articles for all their subscriptions first, then top up any remaining space with
    # other recent articles
    if request.user.is_authenticated():
        subscriptions = request.user.userprofile.subscription_set.all()

        seen = set()  # avoid duplicates
        count_q = 0
        for sub in subscriptions:
            query = Article.search_by_subscription(sub).prefetch_related('authors').order_by('-pub_date')

            # adds result to 'articles' if the result is not a duplicate from a previous subscription
            for result in query:
                if result.pk not in seen:
                    articles.append(_format_article_detail(sub, result))
                    seen.add(result.pk)

        articles.sort(key=lambda x: x[3].pub_date, reverse=True)  # sort descending by publication date

        count = len(articles)
        if count < NUM_ARTICLES:
            # add more recent articles to fill up newsfeed, if subscriptions are not enough
            extras = Article.objects.prefetch_related('authors').order_by('-pub_date')
            for result in extras:
                if result.pk not in seen:
                    articles.append(_format_article_detail('recent', result))
                    seen.add(result.pk)
                    count += 1
                if count >= NUM_ARTICLES:
                    break

        articles = articles[:NUM_ARTICLES]  # slice feed down to proper size

    # if user is not registered/logged in, we show NUM_ARTICLES of the most recent articles
    else:
        query = Article.objects.prefetch_related('authors').order_by('-pub_date')[:NUM_ARTICLES]
        for result in query:
            articles.append(_format_article_detail('recent', result))

    return render(request, 'psybrowse_app/index.html', {
        'articles': articles, 
            # end result should be: [(sub_type, sub_item_id, sub_display, article1, [(auth1), (auth2), ...]),
            # (sub_type, sub_item_id, sub_display, article2, [(auth1), (auth2), ...]), ...]
            # if article is not from a subscription, 'sub_info' field will be the string 'recent'
    })


def article_detail(request, article_id):
    """Displays detailed information for the requested Article."""
    article = get_object_or_404(Article, pk=article_id)
    author_list = [(a.pk, a.get_name()) for a in article.authors.all()]
    is_subscribed = _is_subscribed(request, Subscription.ARTICLE, article)

    return render(request, 'psybrowse_app/article_detail.html', {
        'source': article.get_source_display(),
        'url': article.get_url(),
        'article': article,
        'authors': article.get_authors_str(),
        'author_list': author_list,
        'is_subscribed': is_subscribed,
    })


def author_detail(request, author_id):
    """Displays detailed information for the requested Author."""
    author = get_object_or_404(Author, pk=author_id)
    is_subscribed = _is_subscribed(request, Subscription.AUTHOR, author)
    return render(request, 'psybrowse_app/author_detail.html', {
        'author': author,
        'articles': author.article_set.all(),
        'is_subscribed': is_subscribed,
    })


def journal_detail(request, journal_id):
    """Displays detailed information for the requested Journal."""
    journal = get_object_or_404(Journal, pk=journal_id)
    is_subscribed = _is_subscribed(request, Subscription.JOURNAL, journal)
    return render(request, 'psybrowse_app/journal_detail.html', {
        'journal': journal,
        'articles': journal.article_set.all(),
        'is_subscribed': is_subscribed,
    })


def user_detail(request, user_id):
    """Displays detailed information for the requested User."""
    user = get_object_or_404(User, pk=user_id)
    return render(request, 'psybrowse_app/user_detail.html', {
        'user': user,
    })


def keyword_detail(request, keyword_id):
    """Displays detailed information for the requested Keyword."""
    keyword = get_object_or_404(Keyword, pk=keyword_id)
    is_subscribed = _is_subscribed(request, Subscription.KEYWORD, keyword)
    return render(request, 'psybrowse_app/keyword_detail.html', {
        'keyword': keyword,
        'articles': keyword.article_set.all(),
        'is_subscribed': is_subscribed,
    })


def search(request):
    """
    The search view takes search terms from GET data ('s') and queries for matching Articles, then displays that list.
    It also accepts a 'sort' parameter and a 'filter' parameter.
    """

    NUM_RESULTS = 15
    DEFAULT_SORT = '-pub_date'

    if request.GET.get('s'):
        translate = { 'search': urllib.unquote_plus(request.GET.get('s')) }
        form = SearchForm(translate)
        terms = True
    else:
        error = 'No search parameters.'
        terms = False

    if terms:
        if form.is_valid():
            # deal with filtering results
            filterText = ''
            if request.GET.get('filter'):
                filters = request.GET.get('filter').split('|')
                filtersDict = {
                    'date': [],
                    'type': [],
                    'authors': [],
                }
                # pull all data from the URL query
                for f in filters:
                    keyval = f.split(':')
                    if keyval[0] == 'date':
                        filtersDict['date'].append(keyval[1])
                    elif keyval[0] == 'type':
                        filtersDict['type'].append(keyval[1])
                    elif keyval[0] == 'author':
                        filtersDict['authors'].append(keyval[1])

                # arrange into text to insert into query
                for cat in filtersDict:
                    if len(filtersDict[cat]) == 1:
                        filterText += ' {:s}:{:s}'.format(cat, filtersDict[cat][0])
                    elif len(filtersDict[cat]) > 1:
                        filterText += ' {:s}:({:s})'.format(cat, ' OR '.join(filtersDict[cat]))

            # deal with sorting results
            if request.GET.get('sort'):
                sort = request.GET.get('sort')
                real_sort = sort
                if sort == 'relevance':
                    real_sort == ''  # search engine should by default provide results according to match percentage
            else:
                sort = DEFAULT_SORT
                real_sort = sort

            query = form.cleaned_data['search'] + filterText
            query_set = Article.search(query).prefetch_related('authors').order_by(real_sort)
            summary = {
                'dates': defaultdict(int),
                'types': defaultdict(int),
                'authors': defaultdict(int),
            }

            if query_set:
                author_list = []

                # pull all summary (count) data
                for article in query_set:
                    summary['dates'][article.pub_date.year] += 1
                    summary['types'][Article.TYPE_DICT[article.type].capitalize()] += 1

                    authors = article.authors.all()
                    author_list.append([(a.pk, a.get_name()) for a in authors])
                    for author in authors:
                        summary['authors'][author.get_name()] += 1

                articles_authors = zip(query_set, author_list)
                summary['dates_order'] = sorted(summary['dates'].keys(), reverse=True)
                summary['types_order'] = sorted(summary['types'].keys())
                summary['authors_order'] = sorted(summary['authors'].keys())

                paginator = Paginator(articles_authors, NUM_RESULTS, orphans=3)

                page = request.GET.get('page')
                try:
                    results = paginator.page(page)
                except PageNotAnInteger:
                    # if page is not an integer, deliver first page
                    results = paginator.page(1)
                except EmptyPage:
                    # if page is out of range, deliver last page of results
                    results = paginator.page(paginator.num_pages)
            else:
                results = None

            is_subscribed = _is_subscribed(request, Subscription.SEARCH_STRING, form.cleaned_data['search'])

            return render(request, 'psybrowse_app/search.html', {
                'num_results': query_set.count(),
                'summary': summary,
                'search_term': query,
                'search_term_url': urllib.quote_plus(query),
                'sort': sort,
                'results': results,
                'is_subscribed': is_subscribed,
            })

        else:
            error = 'Invalid search parameters.'

    return render(request, 'psybrowse_app/search.html', {
        'error': error,
        'articles_authors': [],
    })


def adv_search(request):
    """The advanced search view takes form data, converts it to a search query string, then sends it to the search view."""
    if request.method == 'POST':
        form = AdvSearchForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            fields = ['title', 'abstract', 'authors', 'type', 'journal', 'source', 'keywords']
            search_terms = ''

            # loop through fields and construct search string
            for f in fields:
                if f in data and data[f]:
                    name = None
                    value = None

                    # do specific processing for certain fields
                    if f == 'type':
                        if len(data[f]) < len(Article.TYPES):  # if all types are selected, ignore
                            name = f
                            sel_types = [Article.TYPE_DICT[int(t)].capitalize() for t in data[f]]
                            value = ' OR '.join(sel_types)
                    elif f == 'source':
                        if len(data[f]) < len(Article.SOURCES):  # if all sources are selected, ignore
                            name = f
                            sel_sources = [Article.SOURCE_DICT[t] for t in data[f]]
                            value = ' OR '.join(sel_sources)
                    else:
                        name = f
                        value = data[f]

                    # group multiple terms together in parentheses
                    if isinstance(value, basestring) and ' ' in value:
                        value = '({:s})'.format(value)

                    if name and value:
                        search_terms += '{:s}:{:s} '.format(name, value)

            # handle dates separately, to create range
            if data['pub_date_from'] or data['pub_date_to']:
                name = 'date'
                date_from = (data['pub_date_from'].strftime('%Y%m%d') + ' ') if data['pub_date_from'] else ''
                date_to = (' ' + data['pub_date_to'].strftime('%Y%m%d')) if data['pub_date_to'] else ''

                value = '[{:s}TO{:s}]'.format(date_from, date_to)  # e.g., [20120101 TO 20141231] or [20120101 TO] or
                                                                   # [TO 20141231]

                search_terms += '{:s}:{:s} '.format(name, value)

            search_terms = search_terms.strip()

            return HttpResponseRedirect('{:s}?s={:s}'.format(reverse('search'), urllib.quote_plus(search_terms)))
                # send completed search query string to search view

    else:
        form = AdvSearchForm()

    return render(request, 'psybrowse_app/adv_search.html', {
        'form': form,
    })


def register(request):
    """Registers a new User, creating a Django auth User and a UserProfile."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return HttpResponseRedirect(reverse('index'))
    else:
        form = CustomUserCreationForm()

    return render(request, 'psybrowse_app/register.html', {
        'form': form,
    })


# NOTE: Login function is handled automatically by 'django.contrib.auth.views.login'.

def logout_page(request):
    """Logs out a User that is currently logged in."""
    logout(request)
    return HttpResponseRedirect(reverse('index'))


@login_required
def subscribe(request):
    """
    If user is logged in, this view will subscribe them to the item of type 'type' and ID 'id' sent through GET
    parameters. If subscribing to a search string, the parameters are 'type' and 'value' instead.

    This view also handles AJAX requests, and returns a JSON string with a 'response' of True or False, depending on
    whether the user was successfully subscribed. If False, the JSON will include an 'error' key indicating the error.
    """
    if request.method == 'GET' and request.GET.get('type'):
        ajax = request.is_ajax()  # if AJAX, we return JSON strings instead of redirecting page

        type = request.GET.get('type')
        subs_dict = { v: k for k, v in Subscription.TYPE_DICT.items() }  # reverse keys and values of TYPE_DICT to make
                                                                         # it easier to search
        if type in subs_dict:
            sub_type = subs_dict[type]
            terms = {}

            if sub_type == Subscription.SEARCH_STRING:
                key = Subscription.TYPE_DICT[sub_type]
                value = request.GET.get('value')
            else:
                key = Subscription.TYPE_DICT[sub_type] + '__pk'  # need to search for primary key of these
                value = request.GET.get('id')

            terms['sub_type'] = sub_type
            terms[key] = value

            try:
                sub = Subscription.objects.get(**terms)  # pass in 'terms' as keyword arguments
            except Subscription.DoesNotExist:
                sub = Subscription(sub_type=sub_type)  # create a new Subscription
                sub.save()

                if sub_type == Subscription.KEYWORD:
                    item = Keyword.objects.get(pk=value)
                elif sub_type == Subscription.AUTHOR:
                    item = Author.objects.get(pk=value)
                elif sub_type == Subscription.SEARCH_STRING:
                    item = value
                elif sub_type == Subscription.ARTICLE:
                    item = Article.objects.get(pk=value)
                elif sub_type == Subscription.JOURNAL:
                    item = Journal.objects.get(pk=value)

                sub.set_item(sub_type, item)

            user_profile = get_user(request).userprofile

            user_exists = sub.users.filter(pk=user_profile.pk)
            if user_exists.count() == 0:
                sub.users.add(user_profile)  # add user to subscription
                sub.save()

                if not ajax:
                    # redirect back to item
                    if sub_type == Subscription.SEARCH_STRING:
                        return HttpResponseRedirect('{:s}?s={:s}'.format(reverse('search'), urllib.quote_plus(value)))
                    else:
                        return HttpResponseRedirect(reverse(Subscription.TYPE_DICT[sub_type]+' detail', args=(value,)))
                else:
                    return HttpResponse(json.dumps({'response': True}), mimetype='application/json')
            else:
                error = 'You are already subscribed to this item.'

        else:
            error = 'Invalid subscription type.'
    else:
        error = 'No subscription identified.'

    if not ajax:
        return render(request, 'psybrowse_app/subscribe_error.html', {
            'error': error,
        })
    else:
        return HttpResponse(json.dumps({'response': False, 'error': error}), mimetype='application/json')


@login_required
def unsubscribe(request):
    """
    If user is logged in, this view will unsubscribe them from the item of type 'type' and ID 'id' sent through GET
    parameters. If unsubscribing from a search string, the parameters are 'type' and 'value' instead.

    This view also handles AJAX requests, and returns a JSON string with a 'response' of True or False, depending on
    whether the user was successfully unsubscribed. If False, the JSON will include an 'error' key indicating the error.
    """
    if request.method == 'GET' and request.GET.get('type'):
        ajax = request.is_ajax()  # if AJAX, we return JSON strings instead of redirecting page

        type = request.GET.get('type')
        subs_dict = { v: k for k, v in Subscription.TYPE_DICT.items() }  # reverse keys and values of TYPE_DICT to make
                                                                         # it easier to search
        if type in subs_dict:
            sub_type = subs_dict[type]
            user_profile = get_user(request).userprofile
            terms = {}

            if sub_type == Subscription.SEARCH_STRING:
                key = Subscription.TYPE_DICT[sub_type]
                value = request.GET.get('value')
            else:
                key = Subscription.TYPE_DICT[sub_type] + '__pk'  # need to search for primary key of these
                value = request.GET.get('id')

            terms['sub_type'] = sub_type
            terms[key] = value
            terms['users'] = user_profile

            try:
                sub = Subscription.objects.get(**terms)  # pass in 'terms' as keyword arguments
                sub.users.remove(user_profile)
                sub.save()

                if sub.users.count() == 0:
                    sub.delete()  # if there are no more users subscribed, then just delete the whole Subscription

                if not ajax:
                    # redirect back to item
                    if sub_type == Subscription.SEARCH_STRING:
                        return HttpResponseRedirect('{:s}?s={:s}'.format(reverse('search'), urllib.quote_plus(value)))
                    else:
                        return HttpResponseRedirect(reverse(Subscription.TYPE_DICT[sub_type]+' detail', args=(value,)))
                else:
                    return HttpResponse(json.dumps({'response': True}), mimetype='application/json')

            except Subscription.DoesNotExist:
                error = 'No subscription identified.'
        else:
            error = 'Invalid subscription type.'
    else:
        error = 'No subscription identified.'

    if not ajax:
        return render(request, 'psybrowse_app/unsubscribe_error.html', {
            'error': error,
        })
    else:
        return HttpResponse(json.dumps({'response': False, 'error': error}), mimetype='application/json')


@login_required
def unsubscribe_all(request):
    """If user is logged in, this view will unsubscribe them from all their current subscriptions."""
    user_profile = get_user(request).userprofile
    subscriptions = user_profile.subscription_set.all()

    for sub in subscriptions:
        sub.users.remove(user_profile)
        sub.save()

        if sub.users.count() == 0:
            sub.delete()  # if there are no more users subscribed, then just delete the whole Subscription

    return render(request, 'psybrowse_app/subscriptions.html', {
        'message': 'All subscriptions have been deleted.'
    })


@login_required
def subscriptions(request):
    """If user is logged in, this view will display a list of all their current subscriptions."""
    user_profile = get_user(request).userprofile
    subscriptions = user_profile.subscription_set.all()
    subs_list = []
    for sub in subscriptions:
        type_url = Subscription.TYPE_DICT[sub.sub_type]
        if sub.sub_type == Subscription.SEARCH_STRING:
            value = sub.get_item()
            unsub_url = '{:s}?type={:s}&value={:s}'.format(reverse('unsubscribe'), type_url, urllib.quote_plus(value))
        else:
            item_id = sub.get_item().pk
            unsub_url = '{:s}?type={:s}&id={:n}'.format(reverse('unsubscribe'), type_url, item_id)

        subs_list.append(_format_subscription_detail(sub) + (unsub_url, type_url))
    return render(request, 'psybrowse_app/subscriptions.html', {
        'subscriptions': subs_list,
            # list of tuples: (subscription type, subscription display, subscription item URL, unsubscribe URL,
            # subscription type URL-friendly)
    })