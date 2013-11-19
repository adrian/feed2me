# coding=utf-8

from google.appengine.ext import ndb


def root_key():
    """Constructs a key to act as the root for all Feeds. This ensures Feeds
    are all part of the same entity group."""
    return ndb.Key('Feeds', 'feeds')


class Feed(ndb.Model):
    name = ndb.StringProperty()
    url = ndb.StringProperty()
    last_checked = ndb.DateTimeProperty()
    date_of_last_entry = ndb.DateTimeProperty()