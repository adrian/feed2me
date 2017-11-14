import logging

from datetime import datetime
from models import Feed, root_key
from google.appengine.api import mail, users, app_identity
from google.appengine.ext import ndb

def find_feeds_to_check(working_date = None):
    """
    The goal is to check each feed for updates once per day. This function will
    return all feeds that haven't yet been checked today on working_date
    spread out across the day. The assumption is this function is called once
    per day, e.g. if there are 5 hours left in the day and 20 feeds to check
    the feeds will be returned in blocks of four. The balancing is recalculated
    each time the function is called to ensure every feed is checked each day.
    """
    logging.debug("working_date parameter: %s" % working_date)

    if working_date == None:
        working_date = datetime.utcnow()
        logging.debug("working_date set to: %s" % working_date)

    start_of_day = working_date.replace(hour=0, minute=0 ,second=0, microsecond=0)
    start_of_day_str = start_of_day.strftime('%Y-%m-%d %H:%M:%S')
    feeds_query_str = "SELECT * from Feed WHERE last_checked < DATETIME(:1) ORDER BY last_checked ASC"
    logging.debug("Feeds eligible for check query: %s, start_of_day: %s" %
        (feeds_query_str, start_of_day_str))
    feeds_query = ndb.gql(feeds_query_str, start_of_day_str)
    feeds_eligible_for_check = feeds_query.fetch(limit=None)
    logging.debug("Feeds eligible for check: %d" % len(feeds_eligible_for_check))
    if len(feeds_eligible_for_check) == 0:
        return []

    end_of_day = working_date.replace(hour=23, minute=59, second=59, microsecond=0)
    time_left_in_day = end_of_day - working_date
    hours_left_in_day = max(divmod(time_left_in_day.total_seconds(), 3600)[0], 0)
    logging.debug("Hours left in the day: %d" % hours_left_in_day)

    # if there are more hours in the day then there are feeds to check then
    # check one per hour
    if hours_left_in_day > len(feeds_eligible_for_check):
        number_of_feeds_per_block = 1
    elif hours_left_in_day == 0:
        number_of_feeds_per_block = len(feeds_eligible_for_check)
    else:
        number_of_feeds_per_block = int(
            len(feeds_eligible_for_check) / hours_left_in_day
        )
    logging.debug("number_of_feeds_per_block: %d" % number_of_feeds_per_block)

    return feeds_eligible_for_check[:number_of_feeds_per_block]

def publish_entry(feed_title, entry, recipent_address):
    """Send an email for this new entry"""
    logging.debug('publishing "%s"' % entry.title)
    sender_address = _sender_address('rss')
    subject = "(RSS) %s :: %s" % (feed_title, entry.title)
    body = entry.link

    mail.send_mail(sender_address, recipent_address, subject, body)

def report_error(title, message, recipent_address):
    """Send an email to report an error"""
    logging.debug('reporting error for "%s"' % title)
    sender_address = _sender_address('error')
    subject = "(ERROR) %s" % title
    body = message

    mail.send_mail(sender_address, recipent_address, subject, body)

def _sender_address(from_type):
    return "%s@%s.appspotmail.com" % \
        (from_type, app_identity.get_application_id())
