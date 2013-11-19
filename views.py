# coding=utf-8

import jinja2
import os
import webapp2
import json
import logging
import feed_utils
import feedparser

from models import Feed, root_key
from datetime import datetime
from time import mktime
from google.appengine.api import users


JINJA_ENVIRONMENT = jinja2.Environment(
    autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])


def create_feed_from_url(url):
    """ Query the given URL, parse the results and create a Feed object. If
        the response isn't RSS then throw an error """
    f = feedparser.parse(url)

    if ('status' in f and f.status in (200, 301)) and not f.bozo:
        feed = Feed(parent=root_key(), name=f.channel.title, url=f.url)
        if len(f.entries) > 0:
            feed.date_of_last_entry = datetime.fromtimestamp(
                mktime(f.entries[0].updated_parsed))
        return feed
    elif f.bozo and f.bozo_exception:
        raise f.bozo_exception
    else:
        raise Exception("Unexpected response: %s" % f.status)


class IndexHandler(webapp2.RequestHandler):

    def get(self):
        feeds_query = Feed.query(ancestor=root_key())
        feeds = feeds_query.fetch()

        template_values = {
            'feeds': feeds,
        }

        # A logout URL is useful during dev
        DEV = os.environ['SERVER_SOFTWARE'].startswith('Development')
        if DEV:
            template_values['logout_url'] = users.create_logout_url('/')

        template = JINJA_ENVIRONMENT.get_template('templates/feeds.html')
        self.response.write(template.render(template_values))


class FeedAPIHandler(webapp2.RequestHandler):

    def post(self):
        """Create a new feed and save it to the database"""
        feed_url = self.request.get('feed_url')

        if feed_url:
            # Check if we already have this feed
            qry = Feed.query(Feed.url == feed_url)
            if qry.count() == 0:
                # Retrieve the feed details and then save it to the Datastore
                try:
                    feed = create_feed_from_url(feed_url)

                    # Do another check to see if we're following this feed
                    # The URL may have redirected
                    qry = Feed.query(Feed.url == feed.url)
                    if qry.count() > 0:
                        return webapp2.Response(status=409,
                            body="You're already following that feed")

                    # Set the date of last post to now so we only look for future posts
                    feed.last_checked = datetime.min

                    feed.put()

                    self.response.headers['Content-Type'] = 'application/json'
                    obj = {
                        'feed_name': feed.name,
                        'feed_url': feed.url
                    }
                    self.response.out.write(json.dumps(obj))
                except Exception as e:
                    return webapp2.Response(status=400, body=e.message)
            else:
                return webapp2.Response(status=409, body="You're already following that feed")
        else:
            return webapp2.Response(status=400, body="Missing parameter 'feed_url'")


    def delete(self):
        """Delete a feed from the database"""
        feed_url = self.request.get('feed_url')

        if feed_url:
            qry = Feed.query(Feed.url == feed_url)
            if qry.count():
                feed = qry.get()
                feed.key.delete()
            else:
                return webapp2.Response(status=404, body="Feed doesn't exist")
        else:
            return webapp2.Response(status=400, body="Missing parameter 'feed_url'")


class CheckFeedsHandler(webapp2.RequestHandler):

    def get(self):
        recipent_address = self.app.config.get('recipent_address')
        if not recipent_address:
            raise Exception("'recipent_address' not configured in config.py")

        feeds_to_check = feed_utils.find_feeds_to_check()
        logging.debug("Number of feeds to check: %d" % len(feeds_to_check))

        for feed in feeds_to_check:
            # Retrieve the feed XML
            logging.debug("Checking feed \"%s\"" % feed.url)
            new_entries = 0
            parsed_feed = feedparser.parse(feed.url)

            # 304 means the feed hasn't changed since the last request so let's
            # move on to the next feed
            if "status" in parsed_feed and parsed_feed.status == 304:
                continue

            # Determine the last update date of the feed. The feedparser
            # documentation suggests this should be available at
            # parsed_feed.updated_parsed regardless of the feed type.
            # Unfortunately that doesn't appear to be the case.
            # If we can't determine the feed's update date then skip it.
            feed_update_date = parsed_feed.updated_parsed \
                if "updated_parsed" in parsed_feed \
                    else parsed_feed.feed.updated_parsed
            if feed_update_date is None:
                logging.debug("Feed '%s' has no updated date" % feed.url)
                continue

            # Determine the date of the last entry. This will usually come
            # from the database but if that value is None (for whatever reason)
            # lets assume we've never checked this feed and only want to see
            # entries from now on. In this case we'll use the date the feed was
            # last updated.
            date_of_last_entry = feed.date_of_last_entry \
                if feed.date_of_last_entry is not None \
                    else datetime.utcfromtimestamp(mktime(feed_update_date))

            # This is the new date_of_last_entry to store on the feed
            date_of_most_recent_entry = date_of_last_entry

            # Find new entries and publish them
            if feed_update_date > date_of_last_entry.utctimetuple():
                for entry in parsed_feed.entries:
                    date_entry_published = None
                    # If the entry doesn't have an update or published date
                    # then let's ignore it and move on
                    if "published_parsed" in entry:
                        date_entry_published = entry.published_parsed
                    elif "updated_parsed" in entry:
                        date_entry_published = entry.updated_parsed
                    if date_entry_published is None:
                        logging.debug("Entry '%s' has no published/update date" \
                            % entry.title)
                        continue

                    if date_entry_published > date_of_last_entry.utctimetuple():
                        # publish this new entry
                        feed_utils.publish_entry(parsed_feed.feed.title, entry,
                            recipent_address)
                        # If this is the most recent entry then record it's date
                        if date_entry_published > \
                                date_of_most_recent_entry.utctimetuple():
                            date_of_most_recent_entry = \
                                datetime.utcfromtimestamp(
                                    mktime(date_entry_published))
                        new_entries = new_entries + 1

            # Update dates on the feed
            feed.last_checked = datetime.now()
            feed.date_of_last_entry = date_of_most_recent_entry
            feed.put()

            logging.debug("Published %d new extries for \"%s\"" % (new_entries, feed.url))
