#!/usr/bin/env python

"""
This module pulls article data from various databases and populates the Django database.
"""
import os
from optparse import make_option
from django.core.management.base import BaseCommand
from psybrowse_app.models import Article, Author, Journal
import harvesters

class Command(BaseCommand):
    help = 'Populates the Article and Author database with new articles'

    option_list = BaseCommand.option_list + (
        make_option('--initial',
            action='store_true',
            dest='initial',
            default=False,
            help='Indicates an initial population of the database, so articles are not constantly being reindexed.'),
        )

    def _create_article(self, result, source):
        """Creates a new Article based on data in `result` and `source`, and returns the new Article."""
        art = Article(
            source=source,
            source_id=result['source_id'],
            type=result['type'],
            title=result['title'],
            volume=result['volume'],
            issue=result['issue'],
            pages=result['pages'],
            pub_date=result['pub_date'],
            abstract=result['abstract'],  
            doi=result['doi'],
            issn=result['issn'],
            isbn=result['isbn'],
        )
        art.save()
        return art

    def _add_authors(self, article, authors):
        """Adds authors to an Article, creating new Authors if they do not currently exist. Returns the Article."""
        for author in authors:
            search_authors = Author.objects.filter(
                first_name__iexact=author['first_name'],
                last_name__iexact=author['last_name'])

            if search_authors:
                if search_authors[0].initials == author['initials']:
                    # if exact match, use existing author
                    article.authors.add(search_authors[0])
                else:
                    # if close match, create new author but flag for conflict
                    author['flag_conflict'] = True
                    article.authors.create(**author)
                    search_authors[0].flag_conflict = True
                    search_authors[0].save(update_fields=['flag_conflict'])
            else:
                if not author['first_name'] or not author['last_name']:
                    author['flag_missing'] = True

                a = article.authors.create(**author)
        return article

    def _add_journal(self, article, journal):
        """Adds journal to an Article, creating new Journal if it does not currently exist. Returns the Article."""
        #search_journal = Journal.objects.filter(title__iexact=journal)

        obj, created = Journal.objects.get_or_create(title=journal)
        article.journal = obj
        article.save()

        #if search_journal:
            # if match, use existing journal
            #article.journal.add(search_journal[0])
        #else:
            # create new journal
            #article.journal.create(title=journal)
        return article

    def handle(self, *args, **options):
        # only populate database if --initial flag is not set, or if it is but there are no existing Articles
        # primary purpose for this is so command can be used when updating AWS environment without overwriting all the
        # existing articles in the database every time
        if not options['initial'] or (options['initial'] and Article.objects.count() == 0):

            if 'WHOOSH_DISABLED' in os.environ:
                use_whoosh = False
            else:
                use_whoosh = True

            pubmed_search = harvesters.PubMedHarvester('psychology', 100)

            if use_whoosh:
                ix = whoosh.index.open_dir('psybrowse_app/article_index')  # open Whoosh index

            for result in pubmed_search.get_results():
                search_articles = Article.objects.filter(source__exact=Article.PUBMED, source_id__exact=result['source_id'])

                # only create articles that don't already exist
                if not search_articles:
                    article = self._create_article(result, Article.PUBMED)

                    if article:
                        if result['authors']:
                            self._add_authors(article, result['authors'])

                        if result['journal']:
                            self._add_journal(article, result['journal'])

                        if use_whoosh:
                            article.index_article(ix, commit=False)

                        # look for missing values in critical fields, to be reviewed later
                        critical_fields = ['type', 'title', 'journal', 'pub_date', 'authors']
                        for f in critical_fields:
                            attr = getattr(article, f)
                            if not attr:
                                article.flag_missing = True

                        article.save()

                        print unicode(article).encode('utf-8')

            if use_whoosh:
                ix.writer().commit()  # commit all changes to Whoosh search index