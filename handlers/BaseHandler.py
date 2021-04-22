# coding=utf-8
# @CREATE_TIME: 2021/4/20 下午1:53
# @LAST_MODIFIED: 2021/4/20 下午1:53
# @FILE: BaseHandler.py
# @AUTHOR: Ray
from pycket.session import SessionMixin
from typing import Optional, Awaitable
import tornado.web
import tornado.util

from utils.async_authenticated import async_authenticated


class BaseHandler(tornado.web.RequestHandler, SessionMixin):
    # def set_default_headers(self):
    #     """
    #     通用的request请求。
    #     在每次请求前添加头信息。
    #     """
    #     # 允许跨域
    #     self.set_header('Access-Control-Allow-Origin', '*')
    #     self.set_header("Access-Control-Allow-Headers", "Content-Type,Authorization")
    #     self.set_header('Access-Control-Allow-Methods', 'POST, GET, DELETE, PUT, PATCH, OPTIONS')

    # 这个函数是必要的，有些浏览器或者测试工具在访问之前都会预先访问，你不写的话会导致出错的
    # 例如vue一般需要访问options方法
    def options(self):
        self.finish()

    def row_to_obj(self, row, cur):
        """Convert a SQL row to an object supporting dict and attribute access."""
        obj = tornado.util.ObjectDict()
        for val, desc in zip(row, cur.description):
            obj[desc[0]] = val
        return obj

    async def execute(self, stmt, *args):
        """Execute a SQL statement.
        Must be called with ``await self.execute(...)``
        """
        async with self.application.db.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(stmt, args)
                await conn.commit()

    async def query(self, stmt, *args):
        """Query for a list of results.
        Typical usage::
            results = await self.query(...)
        Or::
            for row in await self.query(...)
        """
        # with (await self.application.db.cursor()) as cur:
        async with self.application.db.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(stmt, args)
                return [self.row_to_obj(row, cur) for row in await cur.fetchall()]

    async def queryone(self, stmt, *args):
        """Query for exactly one result.
        Raises NoResultError if there are no results, or ValueError if
        there are more than one.
        """
        results = await self.query(stmt, *args)
        if len(results) == 0:
            raise Exception
        elif len(results) > 1:
            raise ValueError("Expected 1 result, got %d" % len(results))
        return results[0]

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def get_current_user(self):  # 重写get_current_user()方法
        return self.session.get('user_id', None)  # session是一种会话状态，跟数据库的session可能不一样
        # pass


class IndexHandler(BaseHandler):
    @async_authenticated  # @tornado.web.authenticated装饰器包裹get方法时，表示这个方法只有在用户合法时才会调用，authenticated装饰器会调用get_current_user()方法获取current_user的值，若值为False，则重定向到登录url装饰器判断有没有登录，如果没有则跳转到配置的路由下去，但是要在app.py里面设置login_url
    async def get(self, *args, **kwargs):
        res = await self.query("SELECT * FROM admin LIMIT %s", 1)
        await self.application.cache.set('key', 'value')

        self.write(str(await self.application.cache.get('key')))