PsyBrowse
=========

[PsyBrowse](http://www.psybrowse.com) is an open access search engine and user
subscription service. Subscribe to the topics, journals, authors, and papers you
care about, and receive the latest updates. PsyBrowse highlights open access
articles, data, and materials where available, making it easier than ever to
find and discuss the research you love.

PsyBrowse is still under heavy development, so it is **not yet ready for general
use**. However, we are looking for developers who want to help out! See below
for details about where to get started.

Current progress
----------------

A [mostly-functional prototype](http://psybrowse-env-znpdcpa6ns.elasticbeanstalk.com)
is currently available. It allows for user sign-ups and subscriptions; however,
searching is limited, and our database of articles is small at this point.

How to help
------------

- The primary area in which we need help is to build up our database of
  articles. We need people to work on creating "scrapers" that will scrape
  metadata from journal websites. These functions can be seen in
  `psybrowse_app/management/commands/harvesters.py`.
- We are also in the process of setting up code ("harvesters") to periodically
  check RSS feeds for updates. Help with gathering RSS URLs for journals and
  setting up a function to read them would be immensely helpful.
- The plan is to switch to Elasticsearch for our back-end database of articles;
  individuals experienced with this would be of enormous help!
- Greater front-end work to make system more user-friendly is another big area.
- We always need people to help test the system! Even if you have no experience
  with programming, testing the system can help us identify bugs.