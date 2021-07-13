# coding=utf-8
# @CREATE_TIME: 2021/4/7 下午5:57
# @LAST_MODIFIED: 2021/4/7 下午5:57
# @FILE: app.py
# @AUTHOR: Ray
import argparse
import os
import tornado.ioloop
import tornado.locks
import tornado.web

import socketio
# from handlers.socketio.SioHandler import sio
from handlers.DefaultHandler import DefaultHandler
from handlers.index import MainHandler
from tornado.httpserver import HTTPServer

from utils.PikaClient import PikaClient
from utils.singleton_config import config


class Application(tornado.web.Application):  # 引入Application类，重写方法，这样做的好处在于可以自定义，添加另一些功能
    def __init__(self):
        handlers = [
            tornado.web.url(r'/', MainHandler.IndexHandler, name='index'),
            tornado.web.url(r'/login', MainHandler.LoginHandler, name='login'),
            tornado.web.url(r'/logout', MainHandler.LogoutHandler, name='logout'),
            tornado.web.url(r'/upload', MainHandler.UploadHandler, name='upload'),
            # (r"/socket.io/", socketio.get_tornado_handler(sio))
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
                    'host': config["pycket"]["redis_host"],
                    'port': config["pycket"]["redis_port"],
                    'db_sessions': config["pycket"]["redis_sessions"],
                    'db_notifications': config["pycket"]["redis_notifications"],
                    'max_connections': 2 ** 33,
                },
                'cookie': {
                    'expires_days': config["pycket"]["expires_days"],
                    'max_age': config["pycket"]["max_age"]
                }
            },
            default_handler_class=DefaultHandler
        )

        super(Application, self).__init__(handlers,
                                          **settings)  # 用super方法将父类的init方法重新执行一遍，然后将handlers和settings传进去，完成初始化


def main():
    # params
    parser = argparse.ArgumentParser()
    parser.add_argument("--PORT", type=str, default=config["server"]["port"])
    params = parser.parse_args()

    app = Application()
    io_loop = tornado.ioloop.IOLoop.instance()
    app.pc = PikaClient(io_loop)
    app.pc.connect()
    # 单进程启动
    http_server = tornado.httpserver.HTTPServer(app)
    app.listen(params.PORT)

    print(f"tornado running on port {params.PORT}")
    io_loop.start()
    # if DEBUG_MODE:
    #     # 单进程启动
    #     app.listen(PORT)
    # else:
    #     # 多进程启动
    #     server = HTTPServer(app)
    #     server.ssl_options = {"certfile": config["server"]["ssl_key"],
    #                           "keyfile": config["server"]["ssl_cert"]}
    #     # 在Linux系统bind方法不起作用，需要使用listen；在macOS系统listen方法不起作用，需要使用bind
    #     if sys.platform == 'linux':
    #         server.listen(PORT)
    #     else:
    #         server.bind(PORT)
    #     server.start(num_processes=config["server"]["num_processes"])
    # the server will simply run until interrupted
    # with Ctrl-C, but if you want to shut down more gracefully,
    # call shutdown_event.set().
    # shutdown_event = tornado.locks.Event()
    # await shutdown_event.wait()


if __name__ == "__main__":
    # tornado.ioloop.IOLoop.instance().run_sync(main)
    main()
