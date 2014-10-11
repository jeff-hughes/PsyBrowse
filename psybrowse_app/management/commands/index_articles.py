#!/usr/bin/env python

"""
This module indexes article information, for use with the Whoosh search engine.
"""
from optparse import make_option

from django.core.management.base import BaseCommand

from whoosh_index import WhooshArticleIndex

class Command(BaseCommand):
    help = 'Index article information for use with the Whoosh search engine.'

    option_list = BaseCommand.option_list + (
        make_option('--clear',
            action='store_true',
            dest='clear',
            default=False,
            help='Clear the index and index all articles.'),
        )

    def handle(self, *args, **options):
        index = WhooshArticleIndex()
        if options['clear']:
            index.index_articles(clear=True)
        else:
            index.index_articles()

        