# coding=utf-8
# @CREATE_TIME: 2021/4/7 下午5:57
# @LAST_MODIFIED: 2021/4/7 下午5:57
# @FILE: app.py
# @AUTHOR: Ray
import os
import sys
import yaml

import aiomysql
import tornado.ioloop
import tornado.locks
import tornado.web
from tornado.httpserver import HTTPServer

from handlers import MainHandler

# load config.yml
config = yaml.safe_load(open("config.yml"))

users_ws_count = {}  # [req sid]


async def maybe_create_tables(db):
    async with db.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute("SELECT COUNT(*) FROM ad LIMIT 1")
                await cur.fetchone()
            except Exception as e:
                with open("schema.sql") as f:
                    schema = f.read()
                    await cur.execute(schema)


class Application(tornado.web.Application):  # 引入Application类，重写方法，这样做的好处在于可以自定义，添加另一些功能
    def __init__(self, db):
        self.db = db
        handlers = [
            tornado.web.url(r'/', MainHandler.IndexHandler, name='index'),
            tornado.web.url(r'/login', MainHandler.LoginHandler, name='login'),
            tornado.web.url(r'/logout', MainHandler.LogoutHandler, name='logout'),
        ]
        settings = dict(
            debug=config["debug_mode"],  # 调试模式，修改后自动重启服务，不需要自动重启，生产情况下切勿开启，安全性
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            login_url='/login',  # 没有登录则跳转至此
            cookie_secret='guijutech@!',  # 加密cookie的字符串
            xsrf_cookie=True,
            pycket={  # 固定写法packet，用于保存用户登录信息
                'engine': 'redis',
                'storage': {
                    'host': 'localhost',
                    'port': 6379,
                    'db_sessions': 15,
                    'db_notifications': 11,
                    'max_connections': 2 ** 33,
                },
                'cookie': {
                    'expires_days': 1,
                    'max_age': 100
                }
            }
        )

        super(Application, self).__init__(handlers,
                                          **settings)  # 用super方法将父类的init方法重新执行一遍，然后将handlers和settings传进去，完成初始化


async def main():
    port = config["server"]["port"]
    debug_mode = config["debug_mode"]

    # Create the global connection pool.
    async with aiomysql.create_pool(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='89914062',
            db='eiko',
    ) as db:
        await maybe_create_tables(db)
        app = Application(db)
        if debug_mode:
            # 单进程启动
            app.listen(port)
        else:
            # 多进程启动
            server = HTTPServer(app)
            server.ssl_options = {"certfile": config["server"].get("ssl_key"),
                                  "keyfile": config["server"].get("ssl_cert")}
            # 在Linux系统bind方法不起作用，需要使用listen；在macOS系统listen方法不起作用，需要使用bind
            if sys.platform == 'linux':
                server.listen(port)
            else:
                server.bind(port)
            server.start(num_processes=0)
        # the server will simply run until interrupted
        # with Ctrl-C, but if you want to shut down more gracefully,
        # call shutdown_event.set().
        print(f"tornado running on port {port}")
        shutdown_event = tornado.locks.Event()
        await shutdown_event.wait()


if __name__ == "__main__":
    tornado.ioloop.IOLoop.instance().run_sync(main)
