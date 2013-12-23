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
        test_feed['entries'] = []

        feedparser.parse = lambda url: test_feed

        feed = views.create_feed_from_url("http://abc.com")
        self.assertEquals("A Test Feed", feed.name)

    def test_with_temp_redirect(self):
        test_feed = feedparser.FeedParserDict()
        test_feed['bozo'] = False
        test_feed['status'] = 302
        test_feed['channel'] = feedparser.FeedParserDict()
        test_feed['channel']['title'] = "A Test Feed"
        test_feed['entries'] = []
        test_feed['href'] = 'http://def.com'

        feedparser.parse = lambda url: test_feed

        feed = views.create_feed_from_url("http://abc.com")
        self.assertEquals("A Test Feed", feed.name)
        self.assertEquals('http://abc.com', feed.url)

    def test_with_permanent_redirect(self):
        test_feed = feedparser.FeedParserDict()
        test_feed['bozo'] = False
        test_feed['status'] = 301
        test_feed['channel'] = feedparser.FeedParserDict()
        test_feed['channel']['title'] = "A Test Feed"
        test_feed['entries'] = []
        test_feed['href'] = 'http://def.com'

        feedparser.parse = lambda url: test_feed

        feed = views.create_feed_from_url("http://abc.com")
        self.assertEquals("A Test Feed", feed.name)
        self.assertEquals('http://def.com', feed.url)

    def teardown():
        feedparser.parse = self.orig_parse_func
