#!/usr/bin/env python

"""
This module pulls article data from various databases and populates the Django database.
"""
from django.core.management.base import BaseCommand
from psybrowse_app.models import Article, Author, Journal
import harvesters

class Command(BaseCommand):
    help = 'Populates the Article and Author database with new articles'

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
                    article.authors.create(
                        first_name=author['first_name'],
                        last_name=author['last_name'],
                        initials=author['initials'],
                        flag_conflict=True
                    )
                    search_authors[0].flag_conflict = True
                    search_authors[0].save(update_fields=['flag_conflict'])
            else:
                article.authors.create(
                    first_name=author['first_name'],
                    last_name=author['last_name'],
                    initials=author['initials']
                )
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
        pubmed_search = harvesters.PubMedHarvester('psychology', 100)
        for result in pubmed_search.get_results():
            search_articles = Article.objects.filter(source__exact=Article.PUBMED, source_id__exact=result['source_id'])

            # only create articles that don't already exist
            if not search_articles:
                article = self._create_article(result, Article.PUBMED)

                if article and result['authors']:
                    self._add_authors(article, result['authors'])

                if article and result['journal']:
                    self._add_journal(article, result['journal'])

                print unicode(article)