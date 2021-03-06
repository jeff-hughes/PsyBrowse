import os

from django.db import models
from django.contrib.auth.models import User

import whoosh.index
from whoosh.qparser import MultifieldParser
from whoosh.qparser.dateparse import DateParserPlugin

class Author(models.Model):
    """
    Store details for an author of an Article. Authors have a many-to-many
    relationship with Articles.
    """
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    initials = models.CharField(max_length=50, blank=True, null=True)

    flag_conflict = models.BooleanField(default=False)
        # This flag is used when an Author name is similar to an existing
        # Author. For use with admin management.
    flag_missing = models.BooleanField(default=False)
        # This flag is used when an Author is missing important information.
        # For use with admin management.

    def __unicode__(self):
        return self.get_name()

    def get_name(self):
        """Return nicely formatted string with Author's full name."""
        if self.initials:
            return u'{:s} {:s} {:s}'.format(
                self.first_name,
                self.initials,
                self.last_name)
        else:
            return u'{:s} {:s}'.format(self.first_name, self.last_name)


class Keyword(models.Model):
    """
    A keyword identifying an Article's content. Keywords have a many-to-many
    relationship with Articles.
    """
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    value = models.CharField(max_length=200)

    def __unicode__(self):
        return self.value


class Journal(models.Model):
    """
    A journal or other publication medium. Journals have a many-to-one
    relationship with Articles (each Article can be associated with exactly one
    Journal.)
    """
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=800)

    flag_conflict = models.BooleanField(default=False)
        # This flag is used when a Journal title is similar to an existing
        # Journal. For use with admin management.
    flag_missing = models.BooleanField(default=False)
        # This flag is used when a Journal is missing important information. For
        # use with admin management.

    def __unicode__(self):
        return self.title


class Article(models.Model):
    """
    An Article defines the information for a single published text.

    Articles have a source, the database from which the information for the
    article was pulled, and can be one of several types. Articles also have a
    title, publication date, etc. An Article has a one-to-many relationship with
    Journals (each Article can be associated with exactly one Journal), a
    many-to-many relationship with Authors, a many-to-many relationship with
    Keywords, and a many-to-many relationship with other Articles (references).
    """
    # Sources
    PUBMED = 'PM'
    SOURCES = (
        (PUBMED, 'PubMed'),
    )
    URLS = {
        'PM': 'http://www.ncbi.nlm.nih.gov/pubmed/{:s}',
    }  # It may be easier to store the URL directly in the database, but this
       # works for now

    SOURCE_DICT = {
        PUBMED: 'PubMed',
    }

    # Types
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

    # The string value here is for referencing the appropriate object attribute,
    # based on the type -- for example, getattr(self, TYPE_DICT[AUTHOR])
    TYPE_DICT = {
        ARTICLE: 'article',
        BOOK: 'book',
        CHAPTER: 'chapter',
        DISSERTATION: 'dissertation',
    }

    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    source = models.CharField(max_length=2, choices=SOURCES, blank=True,
                              null=True)
        # Database source from which Article information was pulled
    source_id = models.CharField(max_length=200, blank=True, null=True)
        # Proprietary ID for the Article from the source database

    type = models.PositiveIntegerField(choices=TYPES)

    # Basic citation information
    title = models.CharField(max_length=400)
    journal = models.ForeignKey(Journal, on_delete=models.SET_NULL, blank=True,
                                null=True)
    volume = models.CharField(max_length=100, blank=True, null=True)
    issue = models.CharField(max_length=100, blank=True, null=True)
    pages = models.CharField(max_length=15, blank=True, null=True)

    pub_date = models.DateField(verbose_name='date published', blank=True,
                                null=True)
    authors = models.ManyToManyField(Author, blank=True, null=True)

    # Additional information
    abstract = models.TextField(blank=True, null=True)
    keywords = models.ManyToManyField(Keyword, blank=True, null=True)
    references = models.ManyToManyField('self', symmetrical=False, blank=True,
                                        null=True)
        # Articles can be related to other Articles, asymmetrically (one
        # references the other)

    # Standardized IDs for Article publications
    doi = models.CharField(max_length=200, blank=True, null=True)
    issn = models.CharField(max_length=9, blank=True, null=True)
    isbn = models.CharField(max_length=13, blank=True, null=True)

    # Links to data and materials, if available
    data_url = models.CharField(max_length=400, blank=True, null=True)
    materials_url = models.CharField(max_length=400, blank=True, null=True)

    flag_conflict = models.BooleanField(default=False)
        # This flag is used when information for an Article is similar to an
        # existing Article. For use with admin management.
    flag_missing = models.BooleanField(default=False)
        # This flag is used when an Article is missing important information.
        # For use with admin management.

    # Site stats
    view_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return self.title

    @classmethod
    def search(cls, value):
        """
        Search Articles for 'value' in title, authors, journal, and abstract,
        and return a QuerySet. If 'value' is not a valid search string, search()
        will return an instance of EmptyQuerySet.
        """

        # Use a crappier search mechanism if Whoosh is not enabled
        if 'WHOOSH_DISABLED' in os.environ:
            if value and isinstance(value, basestring):
                queries = []

                words = value.split(' ')
                for word in words:
                    queries.append(
                        models.Q(title__icontains=word) |
                        models.Q(authors__first_name__icontains=word) |
                        models.Q(authors__last_name__icontains=word) |
                        models.Q(journal__title__icontains=word) |
                        models.Q(abstract__icontains=word)
                    )

                return Article.objects.filter(*queries).distinct()
            else:
                return None

        # Use Whoosh if enabled
        else:
            if value and isinstance(value, basestring):
                ix = whoosh.index.open_dir('psybrowse_app/article_index')
                    # Open Whoosh index

                qp = MultifieldParser(
                    ['title', 'authors', 'journal', 'abstract'],
                    schema=ix.schema)
                qp.add_plugin(DateParserPlugin())
                    # Add more natural-language date searching
                    # Info: http://whoosh.readthedocs.org/en/latest/dates.html
                q = qp.parse(value)

                with ix.searcher() as searcher:
                    results = searcher.search(q, limit=None)
                        # Don't limit here, because we paginate in the view
                        # instead

                    if not results.is_empty():
                        ids = [x['id'] for x in results]
                            # Grab Article IDs for each matching document
                        return Article.objects.filter(pk__in=ids).distinct()
                    else:
                        return Article.objects.none()

            else:
                return Article.objects.none()


    @classmethod
    def search_by_subscription(cls, subscription):
        """
        Search for Articles that match a Subscription object given by
        'subscription'. Returns a QuerySet.
        """
        sub_item = subscription.get_item()

        # Here we set up the appropriate query, depending on the type of
        # Subscription
        if subscription.sub_type == Subscription.SEARCH_STRING:
            # Special handling for subscriptions to search results, since they
            # can search on multiple fields
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
        """Return nicely formatted string with the list of Authors."""
        authors_list = [a.get_name() for a in self.authors.all()]
        author_length = len(authors_list)

        if author_length == 0:
            return u''
        if author_length == 1:
            return authors_list[0]
        elif author_length == 2:
            return u' & '.join(authors_list)
        else:
            return u'{:s}, & {:s}'.format(
                ', '.join(authors_list[:-1]),
                authors_list[-1])
    # This is stuff used in the admin panel; why the hell does Django make you
    # put it here??
    get_authors_str.admin_order_field = 'authors'
    get_authors_str.short_description = 'Authors'

    def get_formatted_type(self, capitalized=True):
        """
        Return nicely formatted string description of Article type (optionally
        capitalized).
        """
        article_text = Article.TYPE_DICT[self.type]
        if capitalized:
            article_text = article_text.capitalize()
        return article_text

    def get_formatted_source(self):
        """Return nicely formatted string description of Article source."""
        return Article.SOURCE_DICT[self.source]

    def get_url(self):
        """Return the URL for the Article, directing to the proper source."""
        return Article.URLS[self.source].format(self.source_id)

    def get_keywords_str(self, sep=u','):
        """Return string of all Article keywords, separated by 'sep'."""
        kw_list = [k.value for k in self.keywords.all()]
        return sep.join(kw_list)

    def index_article(self, index=None, commit=True, clear=False):
        """
        Add Article to the Whoosh search index.

        If 'clear' is set to True, Article will be re-indexed if it already
        exists in the index; otherwise, it will only be indexed if it does not
        already exist or has been modified since. The 'index' parameter can be
        given an existing Whoosh index that will be used; otherwise, the
        function will use its own. The 'commit' parameter determines whether the
        changes are automatically committed (set to False if you are indexing a
        number of Articles all at the same time and only want to make one
        database call).
        """
        write = True
        if index:
            ix = index
        else:
            ix = whoosh.index.open_dir('psybrowse_app/article_index')
                # Open Whoosh index

        with ix.searcher() as searcher:
            writer = ix.writer()
            if not clear:
                match = searcher.document_number(id=unicode(self.pk))

                # Index article if it has not been indexed yet or has been
                # modified since indexing
                if match:
                    match_fields = searcher.stored_fields(match)
                    if self.date_modified > match_fields['index_date']:
                        writer.delete_document(match)
                    else:
                        write = False

            if write:
                d = self.pub_date
                fields = ['id', 'source', 'type', 'title', 'journal', 'date',
                          'authors', 'abstract', 'keywords']
                values = [
                    unicode(self.pk),
                    unicode(self.get_formatted_source()),
                    unicode(self.get_formatted_type()),
                    unicode(self.title),
                    unicode(self.journal.title),
                    datetime.datetime(d.year, d.month, d.day),
                    unicode(self.get_authors_str()),
                    unicode(self.abstract),
                    unicode(self.get_keywords_str(u',')),
                ]
                terms = {f:v for f, v in zip(fields, values) if v is not None}
                writer.add_document(**terms)

                if commit:
                    writer.commit()


class UserProfile(models.Model):
    """
    This class holds additional information for each User, and is meant to
    informally "extend" the built-in Django auth User class. UserProfiles have
    a one-to-one relationship with an auth User. They also have a many-to-many
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
    A Subscription is used to keep track of one item, which can be one of
    various types (e.g., keyword, article, search string). Subscriptions can
    have a many-to-many relationship with UserProfiles. They also have a
    one-to-many relationship with the object of the type that they keep track
    of (except in the case of search strings, which are simply stored in a
    character field.)
    """
    # Item types
    KEYWORD = 1
    AUTHOR = 2
    SEARCH_STRING = 3
    ARTICLE = 4
    JOURNAL = 5

    # This is for Django's use, and includes string displays for each choice
    # for users/admins
    SUB_TYPES = (
        (KEYWORD, 'Keyword'),
        (AUTHOR, 'Author'),
        (SEARCH_STRING, 'Search string'),
        (ARTICLE, 'Article'),
        (JOURNAL, 'Journal'),
    )

    # The string value here is for referencing the appropriate object attribute,
    # based on the type -- for example, getattr(self, TYPE_DICT[AUTHOR])
    TYPE_DICT = {
        KEYWORD: 'keyword',
        AUTHOR: 'author',
        SEARCH_STRING: 'search_string',
        ARTICLE: 'article',
        JOURNAL: 'journal',
    }

    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField(UserProfile)
        # All subscriptions belong to at least one user

    sub_type = models.PositiveIntegerField(choices=SUB_TYPES)
        # This identifies the type of object being subscribed to

    # Only one of the following should be filled, depending on the sub_type
    keyword = models.ForeignKey(Keyword, blank=True, null=True)
    author = models.ForeignKey(Author, blank=True, null=True)
    search_string = models.CharField(max_length=400, blank=True, null=True)
    article = models.ForeignKey(Article, blank=True, null=True)
    journal = models.ForeignKey(Journal, blank=True, null=True)

    def __unicode__(self):
        rel_object = getattr(self, Subscription.TYPE_DICT[self.sub_type])
        return u'{:s}: {:s}'.format(
            self.get_sub_type_display(),
            unicode(rel_object))

    def get_formatted_type(self, capitalized=True):
        """
        Return nicely formatted string description of Subscription type
        (optionally capitalized).
        """
        sub_text = Subscription.TYPE_DICT[self.sub_type].replace('_', ' ')
        if capitalized:
            sub_text = sub_text.capitalize()
        return sub_text

    def get_item(self):
        """
        Return the item object (e.g., article, author, journal) to which the
        Subscription refers.
        """
        return getattr(self, Subscription.TYPE_DICT[self.sub_type])

    def set_item(self, sub_type, item):
        """
        Set the item to which the Subscription refers, given a particular
        'sub_type' and 'item'.
        """
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