import unittest
import feed_utils
import views
import webtest
import webapp2

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

        # call the method under test
        response = self.testapp.get('/check_feeds')

        # check the publish_entry method was called
        self.assertTrue(publish_entry_called[0],
            "publish_entry function not called")

        # check the feed's last_checked date was updated
        self.assertNotEquals(feed.last_checked, last_checked,
            "last_checked not updated")


    def tearDown(self):
        self.testbed.deactivate()
        feed_utils.publish_entry = self.orig_publish_entry_func
