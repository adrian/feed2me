import unittest
import feed_utils
import views
import webtest
import webapp2
import feedparser

from models import Feed, root_key
from datetime import datetime
from google.appengine.ext import testbed
from views import CheckFeedsHandler


class CheckFeedsHandlerTestCase(unittest.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([('/check_feeds', CheckFeedsHandler)],
            True, {'recipent_address': 'test@test.com'})
        self.testapp = webtest.TestApp(app)
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()
        self.orig_publish_entry_func = feed_utils.publish_entry
        self.orig_find_feeds_to_check = feed_utils.find_feeds_to_check
        self.orig_parse_func = feedparser.parse

    def test_get(self):
        # Create a dummy feed with a last_checked date well in the past
        last_checked = datetime(2013, 9, 21, 10, 0, 0, 0)
        date_of_last_entry = datetime(2013, 9, 20, 8, 45, 0, 0)
        feed = Feed(name = "Test Feed1",
                    last_checked = last_checked,
                    date_of_last_entry = date_of_last_entry,
                    url = './test-feeds/test-rss.xml',
                    parent = root_key())
        feed.put()

        # Create a dummy function to capture calls to publish_entry
        publish_entry_called = [False]
        def _publish_entry(feed_title, entry, recipent_address):
            publish_entry_called[0] = True
        feed_utils.publish_entry = _publish_entry

        # Create a dummy function to return the feeds to check
        def _find_feeds_to_check(working_date = datetime.now()):
            return [feed]
        feed_utils.find_feeds_to_check = _find_feeds_to_check

        # call the method under test
        response = self.testapp.get('/check_feeds')

        # check the publish_entry method was called
        self.assertTrue(publish_entry_called[0],
            "publish_entry function not called")

        # check the feed's last_checked date was updated
        self.assertNotEquals(feed.last_checked, last_checked,
            "last_checked not updated")


    def test_get_with_permanent_redirect(self):
        # Create a dummy feed with a last_checked date well in the past
        last_checked = datetime(2013, 9, 21, 10, 0, 0, 0)
        date_of_last_entry = datetime(2013, 9, 20, 8, 45, 0, 0)
        feed = Feed(name = "Test Feed1",
                    last_checked = last_checked,
                    date_of_last_entry = date_of_last_entry,
                    url = './test-feeds/test-rss.xml',
                    parent = root_key())
        feed.put()

        # Stub out the publish_entry function so we don't have to deal with
        # the GAE mail API
        def _publish_entry(feed_title, entry, recipent_address):
            pass
        feed_utils.publish_entry = _publish_entry

        # Create a dummy function to return the feeds to check
        def _find_feeds_to_check(working_date = datetime.now()):
            return [feed]
        feed_utils.find_feeds_to_check = _find_feeds_to_check

        # Replace feedparser.parse with our own version that sets the status
        # code to 301 and the href to a new URL
        def _parse(url):
            parsed_feed = self.orig_parse_func(url)
            parsed_feed['status'] = 301
            parsed_feed['href'] = 'http://def.com'
            return parsed_feed
        feedparser.parse = _parse

        response = self.testapp.get('/check_feeds')

        # check the feed's URL has been updated
        self.assertEquals(feed.url, 'http://def.com')


    def tearDown(self):
        self.testbed.deactivate()
        feed_utils.publish_entry = self.orig_publish_entry_func
        feed_utils.find_feeds_to_check = self.orig_find_feeds_to_check
        feedparser.parse = self.orig_parse_func
