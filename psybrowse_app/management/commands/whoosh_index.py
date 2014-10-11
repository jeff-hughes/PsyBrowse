#!/usr/bin/env python

"""
This module contains a WhooshArticleIndex class to create a schema and index
for indexing articles.
"""

import os, os.path
import datetime

import whoosh.index as index
from whoosh.fields import *

from psybrowse_app.models import Article, Author, Journal, Keyword

class WhooshArticleIndex(object):
    """
    This class contains methods to create a schema and index for indexing
    articles.
    """
    DIR_PATH = 'psybrowse_app/article_index'

    def get_schema(self):
        return Schema(
            index_date=STORED,
            id=ID(stored=True, unique=True),
            source=KEYWORD,
            type=KEYWORD,
            title=TEXT,
            journal=TEXT,
            date=DATETIME(sortable=True),
            authors=TEXT,
            abstract=TEXT,
            keywords=KEYWORD(commas=True, scorable=True),
        )

    def create_index(self, dir_path=None):
        if not dir_path:
            dir_path = WhooshArticleIndex.DIR_PATH

        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        ix = index.create_in(dir_path, self.get_schema())
        return ix

    def get_index(self):
        if self.index:
            return self.index
        else:
            self.index = self.create_index()

    def index_articles(self, clear=False):
        if clear:
            ix = self.create_index()
        else:
            ix = self.get_index()

        articles = Article.objects.all()
        for article in articles:
            article.index_article(ix, commit=False, clear=clear)

        ix.writer().commit()

        print 'Index completed.'
        return True