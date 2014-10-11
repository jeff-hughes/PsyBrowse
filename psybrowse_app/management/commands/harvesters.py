#!/usr/bin/env python

"""
This module contains Harvesters to search and retrieve articles and resources
from various database APIs.
"""

import urllib
import requests
import json
import datetime
import xml.etree.ElementTree as etree

from psybrowse_app.models import Article

MONTHS = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7,
          'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

class Harvester(object):
    """
    An abstract class that defines the interface for harvesting articles and
    resources from various database APIs.
    """
    def __init__(self, search_term, num_results=10):
        """
        Initialize a new Harvester, which searches a database for 'search_term'
        and returns 'num_results' maximum.
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


class PubMedHarvester(Harvester):
    SEARCH_URL = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmax=0&retmode=json&usehistory=y&term={:s}'
    FETCH_URL = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&query_key={:s}&WebEnv={:s}&retstart=0&retmax={:d}'

    def __init__(self, search_term, num_results=10):
        """
        Initialize a new PubMedHarvester, which searches PubMed for
        'search_term' and returns 'num_results' maximum.
        """
        if search_term:
            url = PubMedHarvester.SEARCH_URL.format(
                urllib.quote_plus(search_term))
            search = requests.get(url)
            self.search = json.loads(search.content)
                # Primarily need this for the querykey and webenv parameters

            url2 = PubMedHarvester.FETCH_URL.format(
                self.search['esearchresult']['querykey'],
                self.search['esearchresult']['webenv'],
                num_results)
            fetch = requests.get(url2)

            self.results = etree.ElementTree(etree.fromstring(fetch.content))
                # Raw output, in etree format
            self.articles = self.results.findall('PubmedArticle')

    def _safe_get_text(self, elem, default=''):
        """
        Get text node of XML element, or return 'default' if element does not
        exist.
        """
        if elem is not None:
            return elem.text
        else:
            return default

    def _extract_data(self, result):
        """
        Extract the relevant information for each result, to return data
        consistently regardless of how it is stored in the original database.
        """

        source_id = self._safe_get_text(
            result.find('.//ArticleIdList/ArticleId[@IdType="pubmed"]'))
        article = result.find('.//Article')

        if article is not None:
            title = self._safe_get_text(article.find('ArticleTitle'), None)
            journal = self._safe_get_text(article.find('Journal/Title'), None)
            volume = self._safe_get_text(
                article.find('Journal/JournalIssue/Volume'), None)
            issue = self._safe_get_text(
                article.find('Journal/JournalIssue/Issue'), None)
            pages = self._safe_get_text(
                article.find('Pagination/MedlinePgn'), None)

            pub_date = article.find('Journal/JournalIssue/PubDate')
            if pub_date is None or pub_date.find('Year') is None:
                pub_date = article.find('ArticleDate')
            if pub_date is None or pub_date.find('Year') is None:
                pub_date = result.find('DateCreated')

            if pub_date is not None:
                year = self._safe_get_text(pub_date.find('Year'), None)
                month = self._safe_get_text(pub_date.find('Month'), '1')
                if not month.isdigit():
                    month = MONTHS[month]
                if year is not None:  # Having at least the year is required
                    date = datetime.datetime(
                        int(year),
                        int(month),
                        int(self._safe_get_text(pub_date.find('Day'), 1)))
                else:
                    date = datetime.datetime.now()
            else:
                date = datetime.datetime.now()
            date = date.strftime('%Y-%m-%d')

            authors_list = article.findall('AuthorList/Author')
            authors = []
            if authors_list is not None:
                for author in authors_list:
                    author_first_name = self._safe_get_text(
                        author.find('ForeName'))
                    author_split = author_first_name.split(' ')
                    name_first = []
                    name_initials = []
                    for name in range(len(author_split)):
                        # Always put first word in first name, and any words
                        # that are longer than 1 character
                        if name == 0 or len(author_split[name]) > 1:
                            name_first.append(author_split[name])
                        else:
                            name_initials.append(author_split[name])
                    name_first = ' '.join(name_first)
                    name_initials = ' '.join(name_initials)
                    if name_initials == '':
                        name_initials = None

                    authors.append({
                        'first_name': name_first,
                        'last_name': self._safe_get_text(
                            author.find('LastName')),
                        'initials': name_initials
                    })

            abstract = article.find('Abstract')
            abstract_text = []
            if abstract is not None:
                abstract_text = []
                for text in abstract.findall('AbstractText'):
                    category = text.get('NlmCategory', '')
                        # Categories can include things like background,
                        # methods, etc.
                    if category != 'UNLABELLED':
                        abstract_text.append(category + ': ')
                    abstract_text.append(self._safe_get_text(text) + '\n')
            abstract_text = ''.join(abstract_text)
            if abstract_text == '':
                abstract_text = None

            doi = self._safe_get_text(
                result.find('.//ArticleIdList/ArticleId[@IdType="doi"]'), None)
            issn = self._safe_get_text(article.find('Journal/ISSN'), None)

            return {
                'source_id': source_id,
                'type': Article.ARTICLE,
                'title': title,
                'journal': journal,
                'volume': volume,
                'issue': issue,
                'pages': pages,
                'pub_date': date,
                'authors': authors,
                'abstract': abstract_text,
                'references': None,
                'doi': doi,
                'issn': issn,
                'isbn': None,
            }

        else:
            return False

    def get_results(self):
        """Create a generator to yield results one at a time."""
        if self.articles is not None:
            for art in self.articles:
                data = self._extract_data(art)
                yield data
