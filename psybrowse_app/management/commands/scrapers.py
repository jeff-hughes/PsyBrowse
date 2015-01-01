#!/usr/bin/env python

"""
This module contains Scrapers to retrieve back issues of journal articles from
from journal websites.
"""

import urllib
import collections
import requests
import json
import datetime
import re
from bs4 import BeautifulSoup

from psybrowse_app.models import Article

MONTHS = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7,
          'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

class Scraper(object):
    """
    An abstract class that defines the interface for scraping articles from
    journal websites.
    """
    def __init__(self, volume=None, issue=None):
        """
        Initialize a new Scraper, which searches a journal website for 'volume'
        and 'issue'. If these are not specified, it will retrieve all articles.
        """
        NotImplemented

    def _extract_data(self, id):
        """
        Extract the relevant information for each result, to return data
        consistently regardless of how it is stored in the original database.
        """
        NotImplemented

    def get_results(self):
        """Create a generator to yield results one at a time."""
        NotImplemented


class JPSP_Scraper(Scraper):
    JOURNAL = 'Journal of Personality and Social Psychology'
    SCRAPE_URL = 'http://psycnet.apa.org/journals/psp/{:s}/{:s}/'
    BASE_URL = 'http://psycnet.apa.org{:s}'
    NUM_VOL = 107
    ISS_PER_VOL = 6
    EXCEPTIONS = {
        5: [1, 2, 3, 4],
        6: [1, 2, 3, '4p1', '4p2'],
        7: ['1p1', '1p2', '2p1', '2p2', '3p1', '3p2', '4p1', '4p2'],
        8: ['1p1', '1p2', '2p1', '2p2', '3p1', '3p2', '4p1', '4p2'],
        9: [1, '2p1', '2p2', 3, 4],
        10: [1, 2, 3, 4],
        11: [1, 2, 3, 4],
        12: [1, 2, 3, 4],
        13: [1, 2, 3, 4],
        14: [1, 2, 3, 4],
        15: [1, 2, 3, 4],
        16: [1, 2, 3, 4],
        17: [1, 2, 3],
        18: [1, 2, 3],
        19: [1, 2, 3],
        20: [1, 2, 3],
        21: [1, 2, 3],
        22: [1, 2, 3],
        23: [1, 2, 3],
        24: [1, 2, 3],
        25: [1, 2, 3],
        26: [1, 2, 3],
        27: [1, 2, 3],
        28: [1, 2, 3],
        35: range(1, 13),
        36: range(1, 13),
        37: range(1, 13),
    }
    META_RGX = re.compile(r'([0-9]{4}).+\s+Volume ([0-9]+),\s+Issue ([0-9]+) \((.+)\)')

    def __init__(self, volume=None, issue=None):
        """
        Initialize a new JPSP_Scraper, which searches the JPSP website for
        'volume' and 'issue'. If these are not specified, it will retrieve all
        articles.
        """
        self.results = collections.OrderedDict()
        self.metadata = {}
        if issue and not volume:
            raise TypeError("'volume' must be set if 'issue' is set.")

        if not volume:
            volume = range(1, JPSP_Scraper.NUM_VOL+1)

        for v in volume:
            if not issue:
                if v in JPSP_Scraper.EXCEPTIONS:
                    issue = JPSP_Scraper.EXCEPTIONS[v]
                else:
                    issue = range(1, JPSP_Scraper.ISS_PER_VOL+1)
            for i in issue:
                fetch = requests.get(JPSP_Scraper.SCRAPE_URL.format(
                    str(v),
                    str(i)
                ))
                results = BeautifulSoup(fetch.content, from_encoding='iso-8859-1')
                    # Raw output, in BeautifulSoup format

                self.results[(v, i)] = results  # Result saved with tuple representing volume and issue
                self.metadata[(v, i)] = {}

                metadata = results.find(id='bwaArticlesZone').h2.text
                match = JPSP_Scraper.META_RGX.search(metadata)
                if match is not None:
                    date = datetime.datetime(
                        int(match.group(1)),
                        int(MONTHS[match.group(4)]),
                        1)
                    self.metadata[(v, i)]['date'] = date.strftime('%Y-%m-%d')
                else:
                    self.metadata[(v, i)]['date'] = None

    def _safe_get_text(self, elem, default=''):
        """
        Get text node of XML element, or return 'default' if element does not
        exist.
        """
        if elem is not None:
            return elem.text
        else:
            return default

    def _extract_data(self, result, volume, issue):
        """
        Extract the relevant information for each result, to return data
        consistently regardless of how it is stored in the original feed.
        """
        title = result.find(class_='bwaazTitle').a.text.strip()
        link = JPSP_Scraper.BASE_URL.format(
            result.find(class_='bwaazTitle').a['href'].strip())
        pages = result.find(class_='bwaazPages').text.strip()

        authors_text = unicode(result.find(class_='bwaazAuthor').text.strip())
        if authors_text == u'No authorship indicated':
            authors_text = None

        authors = []
        if authors_text is not None:
            authors_list = authors_text.split('; ')
            for author in authors_list:
                author_split = author.split(', ')

                author_split2 = author_split[1].split(' ')
                name_first = []
                name_initials = []
                for name in range(len(author_split2)):
                    # Always put first word in first name, and any words
                    # that are longer than 2 characters (initial and period)
                    if name == 0 or len(author_split2[name]) > 2:
                        name_first.append(author_split2[name])
                    else:
                        name_initials.append(author_split2[name])
                name_first = ' '.join(name_first)
                name_initials = ' '.join(name_initials)
                if name_initials == '':
                    name_initials = None

                authors.append({
                    'first_name': name_first,
                    'last_name': author_split[0],
                    'initials': name_initials
                })


        fetch = requests.get(link)
        results = BeautifulSoup(fetch.content, from_encoding='iso-8859-1')
        doi = results.find('meta', attrs={'name': 'citation_doi'})['content']
        abstract = unicode(
            results.find('meta', property='og:description')['content']
        )

        return {
            'source_id': doi,
            'type': Article.ARTICLE,
            'title': title,
            'journal': JPSP_Scraper.JOURNAL,
            'volume': volume,
            'issue': issue,
            'pages': pages,
            'pub_date': self.metadata[(volume, issue)]['date'],
            'authors': authors,
            'abstract': abstract,
            'references': None,
            'doi': doi,
            'issn': None,
            'isbn': None,
        }

    def get_results(self):
        """Create a generator to yield results one at a time."""
        if self.results is not None:
            for key, value in self.results.items():
                articleList = value.find(id='bwaArticlesZone')
                for article in articleList.select('#tocList > li'):
                    data = self._extract_data(article, key[0], key[1])
                    yield data
