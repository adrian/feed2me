import logging

from datetime import datetime, timedelta
from models import Feed, root_key
from google.appengine.api import mail, users, app_identity

def find_feeds_to_check():
    """Find feeds that need to be checked to see if they have any new items"""
    fifteen_minutes = timedelta(minutes=15)
    fifteen_minutes_ago = datetime.now() - fifteen_minutes
    feeds_query = Feed.query(Feed.last_checked < fifteen_minutes_ago,
        ancestor=root_key()).order(-Feed.last_checked)
    return feeds_query.fetch(limit=None)

def publish_entry(feed_title, entry, recipent_address):
    """Send an email for this new entry"""
    logging.debug('publishing "%s"' % entry.title)
    sender_address = _sender_address()
    subject = "(RSS) %s :: %s" % (feed_title, entry.title)
    body = entry.link

    mail.send_mail(sender_address, recipent_address, subject, body)

def _sender_address():
    return "rss@%s.appspotmail.com" % app_identity.get_application_id()
