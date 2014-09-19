from django.db import models
from django.contrib.auth.models import User

import whoosh.index
from whoosh.qparser import MultifieldParser
from whoosh.qparser.dateparse import DateParserPlugin

class Author(models.Model):
    """Stores details for an author of an Article. Authors have a many-to-many relationship with Articles."""
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    initials = models.CharField(max_length=50, blank=True, null=True)

    flag_conflict = models.BooleanField(default=False)  # this flag is used when an Author name is similar to an
                                                        # existing Author; for use with admin management
    flag_missing = models.BooleanField(default=False)   # this flag is used when an Author is missing important
                                                        # information; for use with admin management

    def __unicode__(self):
        return self.get_name()

    def get_name(self):
        """Returns nicely formatted string with Author's full name."""
        if self.initials:
            return u'{:s} {:s} {:s}'.format(self.first_name, self.initials, self.last_name)
        else:
            return u'{:s} {:s}'.format(self.first_name, self.last_name)


class Keyword(models.Model):
    """A keyword identifying an Article's content. Keywords have a many-to-many relationship with Articles."""
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    value = models.CharField(max_length=200)

    def __unicode__(self):
        return self.value


class Journal(models.Model):
    """
    A journal or other publication medium. Journals have a many-to-one relationship with Articles (each Article can be
    associated with exactly one Journal.)
    """
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=800)

    flag_conflict = models.BooleanField(default=False)  # this flag is used when a Journal title is similar to an
                                                        # existing Journal; for use with admin management
    flag_missing = models.BooleanField(default=False)   # this flag is used when a Journal is missing important
                                                        # information; for use with admin management

    def __unicode__(self):
        return self.title


class Article(models.Model):
    """
    An Article is one of the major models in this app, and define the information for a single published text.

    Articles have a source, the database from which the information for the article was pulled, and can be one of
    several types. Articles also have a title, publication date, etc. An Article has a one-to-many relationship with
    Journals (each Article can be associated with exactly one Journal), a many-to-many relationship with Authors, a
    many-to-many relationship with Keywords, and a many-to-many relationship with other Articles (references).
    """
    # sources
    PUBMED = 'PM'
    SOURCES = (
        (PUBMED, 'PubMed'),
    )
    URLS = {
        'PM': 'http://www.ncbi.nlm.nih.gov/pubmed/{:s}',
    }  # it may be easier to store the URL directly in the database, but this works for now

    SOURCE_DICT = {
        PUBMED: 'PubMed',
    }

    # types
    ARTICLE = 1
    BOOK = 2
    CHAPTER = 3
    DISSERTATION = 4
    TYPES = (
        (ARTICLE, 'Article'),
        (BOOK, 'Book'),
        (CHAPTER, 'Chapter'),
        (DISSERTATION, 'Dissertation'),
    )

    # the string value here is for referencing the appropriate object attribute, based on the type
    # for example, getattr(self, TYPE_DICT[AUTHOR])
    TYPE_DICT = {
        ARTICLE: 'article',
        BOOK: 'book',
        CHAPTER: 'chapter',
        DISSERTATION: 'dissertation',
    }

    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    source = models.CharField(max_length=2, choices=SOURCES, blank=True, null=True)
        # database source from which Article information was pulled
    source_id = models.CharField(max_length=200, blank=True, null=True)  # proprietary ID for the Article from the
                                                                         # source database

    type = models.PositiveIntegerField(choices=TYPES)

    # basic citation information
    title = models.CharField(max_length=400)
    journal = models.ForeignKey(Journal, on_delete=models.SET_NULL, blank=True, null=True)
    volume = models.CharField(max_length=100, blank=True, null=True)
    issue = models.CharField(max_length=100, blank=True, null=True)
    pages = models.CharField(max_length=15, blank=True, null=True)

    pub_date = models.DateField(verbose_name='date published', blank=True, null=True)
    authors = models.ManyToManyField(Author, blank=True, null=True)

    # additional information
    abstract = models.TextField(blank=True, null=True)
    keywords = models.ManyToManyField(Keyword, blank=True, null=True)
    references = models.ManyToManyField('self', symmetrical=False, blank=True, null=True)
        # Articles can be related to other Articles, asymmetrically (one references the other)

    # standardized IDs for Article publications
    doi = models.CharField(max_length=200, blank=True, null=True)
    issn = models.CharField(max_length=9, blank=True, null=True)
    isbn = models.CharField(max_length=13, blank=True, null=True)

    # links to data and materials, if available
    data_url = models.CharField(max_length=400, blank=True, null=True)
    materials_url = models.CharField(max_length=400, blank=True, null=True)

    flag_conflict = models.BooleanField(default=False)  # this flag is used when information for an Article is similar
                                                        # to an existing Article; for use with admin management
    flag_missing = models.BooleanField(default=False)   # this flag is used when an Article is missing important
                                                        # information; for use with admin management

    # site stats
    view_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return self.title

    @classmethod
    def search(cls, value):
        """
        Searches Articles for 'value' in title, authors, journal, and abstract, and returns QuerySet. If 'value' is not
        a valid search string, search() will return an instance of EmptyQuerySet.
        """

        """if value and isinstance(value, basestring):
            return Article.objects.filter(
                models.Q(title__icontains=value) |
                models.Q(authors__first_name__icontains=value) |
                models.Q(authors__last_name__icontains=value) |
                models.Q(journal__title__icontains=value) |
                models.Q(abstract__icontains=value)
            ).distinct()
        else:
            return None"""

        if value and isinstance(value, basestring):
            ix = whoosh.index.open_dir('psybrowse_app/article_index')  # open Whoosh index

            qp = MultifieldParser(['title', 'authors', 'journal', 'abstract'], schema=ix.schema)
            qp.add_plugin(DateParserPlugin())  # add more natural-language date searching
                                               # info: http://whoosh.readthedocs.org/en/latest/dates.html
            q = qp.parse(value)

            with ix.searcher() as searcher:
                results = searcher.search(q, limit=None)  # don't limit here, because we paginate in the view instead

                if not results.is_empty():
                    ids = [x['id'] for x in results]  # grab Article IDs for each matching document
                    return Article.objects.filter(pk__in=ids).distinct()
                else:
                    return Article.objects.none()
        else:
            return Article.objects.none()


    @classmethod
    def search_by_subscription(cls, subscription):
        """Searches for Articles that match a Subscription object given by 'subscription'. Returns a QuerySet."""
        sub_item = subscription.get_item()

        # here we set up the appropriate query, depending on the type of Subscription
        if subscription.sub_type == Subscription.SEARCH_STRING:
            # special handling for subscriptions to search results, since they can search on multiple fields
            return Article.search(sub_item)
        elif subscription.sub_type == Subscription.KEYWORD:
            q = models.Q(keywords=sub_item)
        elif subscription.sub_type == Subscription.AUTHOR:
            q = models.Q(authors=sub_item)
        elif subscription.sub_type == Subscription.ARTICLE:
            q = models.Q(references=sub_item)
        elif subscription.sub_type == Subscription.JOURNAL:
            q = models.Q(journal=sub_item)

        if q is not None:
            return Article.objects.filter(q).distinct()
        else:
            return Article.objects.none()

    def get_authors_str(self):
        """Returns nicely formatted string with the list of Authors."""
        authors_list = [a.get_name() for a in self.authors.all()]
        author_length = len(authors_list)

        if author_length == 0:
            return u''
        if author_length == 1:
            return authors_list[0]
        elif author_length == 2:
            return u' & '.join(authors_list)
        else:
            return u'{:s}, & {:s}'.format(', '.join(authors_list[:-1]), authors_list[-1])

    def get_url(self):
        """Returns the URL for the Article, directing to the proper source."""
        return Article.URLS[self.source].format(self.source_id)

    def get_keywords_str(self, sep=u','):
        """Returns string of all Article keywords, separated by 'sep'."""
        kw_list = [k.value for k in self.keywords.all()]
        return sep.join(kw_list)


class UserProfile(models.Model):
    """
    This class holds additional information for each User, and is meant to informally "extend" the built-in Django auth
    User class. UserProfiles have a one-to-one relationship with an auth User. They also have a many-to-many
    relationship with Subscriptions.
    """
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(User)

    affiliation = models.CharField(max_length=600, blank=True, null=True)

    def __unicode__(self):
        return u'{:s} <{:s}>'.format(self.user.get_full_name(), self.user.email)


class Subscription(models.Model):
    """
    A Subscription is used to keep track of one item, which can be one of various types (e.g., keyword, article, search
    string). Subscriptions can have a many-to-many relationship with UserProfiles. They also have a one-to-many
    relationship with the object of the type that they keep track of (except in the case of search strings, which are
    simply stored in a character field.)
    """
    # item types
    KEYWORD = 1
    AUTHOR = 2
    SEARCH_STRING = 3
    ARTICLE = 4
    JOURNAL = 5

    # this is for Django's use, and includes string displays for each choice for users/admins
    SUB_TYPES = (
        (KEYWORD, 'Keyword'),
        (AUTHOR, 'Author'),
        (SEARCH_STRING, 'Search string'),
        (ARTICLE, 'Article'),
        (JOURNAL, 'Journal'),
    )

    # the string value here is for referencing the appropriate object attribute, based on the type
    # for example, getattr(self, TYPE_DICT[AUTHOR])
    TYPE_DICT = {
        KEYWORD: 'keyword',
        AUTHOR: 'author',
        SEARCH_STRING: 'search_string',
        ARTICLE: 'article',
        JOURNAL: 'journal',
    }

    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField(UserProfile)  # all subscriptions belong to at least one user

    sub_type = models.PositiveIntegerField(choices=SUB_TYPES)  # this identifies the type of object being subscribed to

    # only one of the following should be filled, depending on the sub_type
    keyword = models.ForeignKey(Keyword, blank=True, null=True)
    author = models.ForeignKey(Author, blank=True, null=True)
    search_string = models.CharField(max_length=400, blank=True, null=True)
    article = models.ForeignKey(Article, blank=True, null=True)
    journal = models.ForeignKey(Journal, blank=True, null=True)

    def __unicode__(self):
        rel_object = getattr(self, TYPE_DICT[self.sub_type])
        return u'{:s}: {:s}'.format(self.get_sub_type_display(), unicode(rel_object))

    def get_formatted_type(self, capitalized=True):
        """Returns nicely formatted string description of Subscription type (optionally capitalized)."""
        sub_text = Subscription.TYPE_DICT[self.sub_type].replace('_', ' ')
        if capitalized:
            sub_text = sub_text.capitalize()
        return sub_text

    def get_item(self):
        """Returns the item object (e.g., article, author, journal) to which the Subscription refers."""
        return getattr(self, Subscription.TYPE_DICT[self.sub_type])

    def set_item(self, sub_type, item):
        """Sets the item to which the Subscription refers, given a particular 'sub_type' and 'item'."""
        if not sub_type or sub_type not in Subscription.TYPE_DICT:
            if self.sub_type:
                sub_type = self.sub_type
            else:
                raise ValueError('Invalid subscription type.')

        if sub_type == Subscription.KEYWORD:
            self.keyword = item
        elif sub_type == Subscription.AUTHOR:
            self.author = item
        elif sub_type == Subscription.SEARCH_STRING:
            self.search_string = item
        elif sub_type == Subscription.ARTICLE:
            self.article = item
        elif sub_type == Subscription.JOURNAL:
            self.journal = item