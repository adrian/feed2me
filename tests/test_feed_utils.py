import unittest
import feed_utils

from google.appengine.ext import db
from google.appengine.ext import testbed
from google.appengine.ext import ndb
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
        ndb.get_context().clear_cache()

    def testFindFeedsToCheckMoreHoursThanFeeds(self):
        feeds = [
            {
                'name': 'Test 1',
                'last_checked': datetime(2017, 5, 6, 19, 7, 33)
            },
            {
                'name': 'Test 2',
                'last_checked': datetime(2017, 5, 5, 19, 6, 9)
            },
            {
                'name': 'Test 3',
                'last_checked': datetime(2017, 5, 4, 18, 23, 56)
            }
        ]

        for feed_data in feeds:
            feed = Feed(name = feed_data['name'],
                        last_checked = feed_data['last_checked'],
                        parent = root_key())
            feed.put()

        working_date = datetime(2017, 5, 6, 19, 45, 0)
        feeds = feed_utils.find_feeds_to_check(working_date)
        self.assertEqual(1, len(feeds))
        self.assertEqual("Test 3", feeds[0].name)

    def testFindFeedsToCheckThreeHoursSixFeeds(self):
        feeds = [
            {
                'name': 'Test 1',
                'last_checked': datetime(2017, 5, 6, 19, 7, 33)
            },
            {
                'name': 'Test 2',
                'last_checked': datetime(2017, 5, 5, 19, 6, 9)
            },
            {
                'name': 'Test 3',
                'last_checked': datetime(2017, 5, 2, 18, 23, 56)
            },
            {
                'name': 'Test 4',
                'last_checked': datetime(2017, 5, 3, 18, 23, 56)
            },
            {
                'name': 'Test 5',
                'last_checked': datetime(2017, 5, 1, 18, 23, 56)
            },
            {
                'name': 'Test 6',
                'last_checked': datetime(2017, 5, 4, 18, 23, 56)
            }
        ]

        for feed_data in feeds:
            feed = Feed(name = feed_data['name'],
                        last_checked = feed_data['last_checked'],
                        parent = root_key())
            feed.put()

        working_date = datetime(2017, 5, 7, 20, 45, 0)
        feeds = feed_utils.find_feeds_to_check(working_date)
        self.assertEqual(2, len(feeds))
        self.assertEqual("Test 5", feeds[0].name)
        self.assertEqual("Test 3", feeds[1].name)

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

    def testReportError(self):
        feed_title = "Test Feed"
        recipent_address = "test_recipent@test.com"
        message = "problem with XYZ"

        feed_utils.report_error(feed_title, message, recipent_address)

        messages = self.mail_stub.get_sent_messages()
        self.assertEqual(1, len(messages))
        self.assertEqual(recipent_address, messages[0].to)
        self.assertEqual('error@testbed-test.appspotmail.com', messages[0].sender)
        self.assertEqual("(ERROR) %s" % feed_title, messages[0].subject)
        self.assertEqual(message, messages[0].body.decode())

    def tearDown(self):
        self.testbed.deactivate()

