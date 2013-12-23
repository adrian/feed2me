import unittest
import views
import feedparser

class TestCreateFeedFromURL(unittest.TestCase):

    def setUp(self):
        self.orig_parse_func = feedparser.parse

    def test_with_character_encoding_exception(self):
        test_feed = feedparser.FeedParserDict()
        test_feed['bozo'] = True
        test_feed['bozo_exception'] = feedparser.ThingsNobodyCaresAboutButMe()
        test_feed['status'] = 200
        test_feed['channel'] = feedparser.FeedParserDict()
        test_feed['channel']['title'] = "A Test Feed"
        test_feed['url'] = 'http://abc.com'
        test_feed['entries'] = []

        feedparser.parse = lambda url: test_feed

        feed = views.create_feed_from_url("http://abc.com")
        self.assertEquals("A Test Feed", feed.name)

    def teardown():
        feedparser.parse = self.orig_parse_func
