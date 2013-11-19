import unittest
import feed_utils

from google.appengine.ext import db
from google.appengine.ext import testbed
from datetime import datetime
from models import Feed, root_key


class FeedUtilsTestCase(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

    def testFindFeedsToCheckExpect1(self):
        feed = Feed(name="Test",
                    url="./test-feeds/test-rss.xml",
                    last_checked = datetime.min,
                    parent=root_key())
        feed.put()
        feeds = feed_utils.find_feeds_to_check()
        self.assertEqual(1, len(feeds))

    def testFindFeedsToCheckExpect0(self):
        feed = Feed(name="Test",
                    url="./test-feeds/test-rss.xml",
                    last_checked = datetime.max,
                    parent=root_key())
        feed.put()
        feeds = feed_utils.find_feeds_to_check()
        self.assertEqual(0, len(feeds))

    def testPublishEmail(self):
        feed_title = "Test Feed"
        recipent_address = "test_recipent@test.com"

        class Entry:
            pass
        entry = Entry()
        entry.title = 'Test Entry'
        entry.link = 'http://www.test.com'

        feed_utils.publish_entry(feed_title, entry, recipent_address)

        messages = self.mail_stub.get_sent_messages()
        self.assertEqual(1, len(messages))
        self.assertEqual('test_recipent@test.com', messages[0].to)
        self.assertEqual('rss@testbed-test.appspotmail.com', messages[0].sender)
        self.assertEqual("(RSS) %s :: %s" % (feed_title, entry.title), messages[0].subject)
        self.assertEqual(entry.link, messages[0].body.decode())

    def tearDown(self):
        self.testbed.deactivate()

