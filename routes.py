# coding=utf-8

from views import *

route_list = [
    (r'^/$', IndexHandler),
    (r'^/feed/', FeedAPIHandler),
	(r'^/check_feeds$', CheckFeedsHandler)
]
