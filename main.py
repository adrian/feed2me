# coding=utf-8

import webapp2
import logging

import fix_path

from routes import route_list
from config import app_config

app = webapp2.WSGIApplication(route_list,
                                config = app_config,
                                debug = app_config.get('debug', True))
