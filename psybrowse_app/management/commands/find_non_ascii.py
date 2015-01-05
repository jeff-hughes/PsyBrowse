#!/usr/bin/env python

"""
This module searches the Article, Author, and Journal databases for any text
items that are not ASCII (i.e., have symbols or accents).
"""

from django.core.management.base import BaseCommand
from psybrowse_app.models import Article, Author, Journal

class Command(BaseCommand):
    help = 'Search the database for non-ASCII characters and return the IDs of those items.'

    def _safe_decode(self, obj):
        """
        Decodes object if object is of type 'unicode', else returns None.
        """
        if isinstance(obj, unicode):
            return obj.decode('ascii')
        else:
            return None

    def handle(self, *args, **options):
        if Article.objects.count() > 0:
            print 'Articles:'

            all_articles = Article.objects.all()
            for art in all_articles:
                try:
                    self._safe_decode(art.title)
                    self._safe_decode(art.abstract)
                except (UnicodeEncodeError, UnicodeDecodeError):
                    art.flag_non_ascii = True
                    art.save()
                    print art.pk

        if Author.objects.count() > 0:
            print '\nAuthors:'

            all_authors = Author.objects.all()
            for auth in all_authors:
                try:
                    self._safe_decode(auth.first_name)
                    self._safe_decode(auth.last_name)
                    self._safe_decode(auth.initials)
                except (UnicodeEncodeError, UnicodeDecodeError):
                    auth.flag_non_ascii = True
                    auth.save()
                    print auth.pk

        if Journal.objects.count() > 0:
            print '\nJournals:'

            all_journals = Journal.objects.all()
            for journal in all_journals:
                try:
                    self._safe_decode(journal.title)
                except (UnicodeEncodeError, UnicodeDecodeError):
                    journal.flag_non_ascii = True
                    journal.save()
                    print journal.pk