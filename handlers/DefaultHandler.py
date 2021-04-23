# coding=utf-8
# @CREATE_TIME: 2021/4/23 下午4:25
# @LAST_MODIFIED: 2021/4/23 下午4:25
# @FILE: DefaultHandler.py
# @AUTHOR: Ray
from abc import ABC

import tornado.web


class DefaultHandler(tornado.web.RequestHandler, ABC):
    def prepare(self):
        # Use prepare() to handle all the HTTP methods
        self.set_status(404)
        self.finish("error: 404")
