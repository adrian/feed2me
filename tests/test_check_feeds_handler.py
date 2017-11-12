import unittest
import feed_utils
import views
import webtest
import webapp2
import feedparser
import logging

from models import Feed, root_key
from datetime import datetime,  timedelta
from google.appengine.ext import testbed
from views import CheckFeedsHandler
from collections import namedtuple
from feedparser import FeedParserDict


class CheckFeedsHandlerTestCase(unittest.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([('/check_feeds', CheckFeedsHandler)],
            True, {'recipent_address': 'test@test.com'})
        self.testapp = webtest.TestApp(app)
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

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

        # Replace feedparser.parse with our own version that sets the status
        # code to 200 and the href to a new URL
        def _parse(url):
            parsed_feed = self.orig_parse_func(url)
            parsed_feed['status'] = 200
            return parsed_feed
        feedparser.parse = _parse

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


    def test_check_feed_with_probem(self):
        last_checked = datetime(2000, 1, 1)
        date_of_last_entry = datetime(2000, 1, 1)
        feed_url = 'http://x.y.z'
        feed = Feed(name = "Test Feed",
                    last_checked = last_checked,
                    date_of_last_entry = date_of_last_entry,
                    url = feed_url,
                    parent = root_key())
        feed.put()

        # Replace feedparser.parse with our own version that sets the status
        # code to 500 to simulate a server side error
        def _parse(url):
            parsed_feed = FeedParserDict(status = 500, bozo = False)
            return parsed_feed
        feedparser.parse = _parse

        reported_title = [0]
        reported_message = [0]
        reported_recipient = [0]
        orig_report_error = feed_utils.report_error
        def _report_error(title, message, recipent_address):
            reported_title[0] = title
            reported_message[0] = message
            reported_recipient[0] = recipent_address
            orig_report_error(title, message, recipent_address)
        feed_utils.report_error = _report_error

        # run the method under test
        # set logging to CRITICAL so-as not to print exception generated by
        # the test
        try:
            logging.getLogger().setLevel(logging.CRITICAL)
            response = self.testapp.get('/check_feeds')
            self.assertEquals(reported_title[0], feed.name)
            self.assertTrue('returned HTTP code 500' in reported_message[0])
            self.assertEquals(reported_recipient[0], 'test@test.com')
            #self.fail("Should have raised an exception as server returned 500")
        finally:
            logging.getLogger().setLevel(logging.ERROR)

        # there should be one email message describing the problem
        messages = self.mail_stub.get_sent_messages()
        self.assertEquals(1, len(messages))
        self.assertTrue("URL '%s' returned HTTP code 500" % feed_url in
            messages[0].body.payload)

        # check the feed's last_checked date was updated
        self.assertNotEqual(feed.last_checked, last_checked)


    def tearDown(self):
        self.testbed.deactivate()
        feed_utils.publish_entry = self.orig_publish_entry_func
        feed_utils.find_feeds_to_check = self.orig_find_feeds_to_check
        feedparser.parse = self.orig_parse_func
