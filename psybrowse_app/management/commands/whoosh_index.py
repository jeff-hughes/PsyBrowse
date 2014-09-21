#!/usr/bin/env python

"""
This module contains a WhooshArticleIndex class to create a schema and index for indexing articles.
"""

from psybrowse_app.models import Article, Author, Journal, Keyword

import os, os.path
import datetime
import whoosh.index as index
from whoosh.fields import *

class WhooshArticleIndex(object):
    """This class contains methods to create a schema and index for indexing articles."""
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

        with ix.searcher() as searcher:
            writer = ix.writer()

            articles = Article.objects.all()
            for article in articles:
                write = True

                if not clear:
                    match = searcher.document_number(id=unicode(article.pk))

                    # for each article, index it if it has not been indexed yet or has been modified since indexing
                    if match:
                        match_fields = searcher.stored_fields(match)
                        if article.date_modified > match_fields['index_date']:
                            writer.delete_document(match)
                        else:
                            write = False

                if write:
                    d = article.pub_date
                    fields = ['id', 'source', 'type', 'title', 'journal', 'date', 'authors', 'abstract', 'keywords']
                    values = [
                        unicode(article.pk),
                        unicode(article.get_formatted_source()),
                        unicode(article.get_formatted_type()),
                        unicode(article.title),
                        unicode(article.journal.title),
                        datetime.datetime(d.year, d.month, d.day),
                        unicode(article.get_authors_str()),
                        unicode(article.abstract),
                        unicode(article.get_keywords_str(u',')),
                    ]
                    terms = {f:v for f, v in zip(fields, values) if v is not None}
                    writer.add_document(**terms)

                    """writer.add_document(
                        id=unicode(article.pk),
                        type=unicode(article.type),
                        title=(u'' if article.title is None else unicode(article.title)),
                        journal=(u'' if article.journal.title is None else unicode(article.journal.title)),
                        date=datetime.strptime(article.pub_date, '%Y-%m-%d'),
                        authors=(u'' if article.get_authors_str() is None else unicode(article.get_authors_str())),
                        abstract=(u'' if article.abstract is None else unicode(article.abstract)),
                        keywords=(u'' if article.get_keywords_str(u',') is None else unicode(article.get_keywords_str(u','))),
                    )"""
            writer.commit()
        print 'Index completed.'
        return True