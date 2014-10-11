#!/usr/bin/env python

"""
This module creates a search schema and index for indexing article information,
for use with the Whoosh search engine.
"""
from django.core.management.base import BaseCommand

from whoosh_index import WhooshArticleIndex

class Command(BaseCommand):
    help = ('Creates a search schema and index for use with the Whoosh'
            'search engine.')

    def handle(self, *args, **options):
        index = WhooshArticleIndex()
        ix = index.create_index()