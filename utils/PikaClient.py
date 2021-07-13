# coding=utf-8
# @CREATE_TIME: 2021/7/8 下午5:12
# @LAST_MODIFIED: 2021/7/8 下午5:12
# @FILE: RpcClient.py
# @AUTHOR: Ray
import uuid
import pika
from pika.adapters import tornado_connection


class PikaClient(object):
    def __init__(self, io_loop):
        self.io_loop = io_loop
        self.connected = False
        self.connecting = False
        self.connection = None
        self.channel = None
        self.callback_queue = None
        self.message_count = 9
        self.corr_id = {}

    def connect(self):
        if self.connecting:
            return
        self.connecting = True
        cred = pika.PlainCredentials('guest', 'guest')
        param = pika.ConnectionParameters(host="0.0.0.0", credentials=cred)
        self.connection = tornado_connection.TornadoConnection(param, custom_ioloop=self.io_loop,
                                                               on_open_callback=self.on_connected)
        self.connection.add_on_open_error_callback(self.err)
        self.connection.add_on_close_callback(self.on_closed)

    def err(self, conn):
        print('err')
        pass

    def on_connected(self, conn):
        self.connected = True
        self.connection = conn
        self.connection.channel(channel_number=1, on_open_callback=self.on_channel_open)

    def on_message(self, channel, method, properties, body):
        if properties.correlation_id in self.corr_id.keys():
            self.corr_id[properties.correlation_id] = body

    def on_channel_open(self, channel):
        self.channel = channel
        self.callback_queue = str(uuid.uuid4()).replace('-', '')
        self.channel.queue_declare(queue=self.callback_queue, exclusive=True)
        channel.basic_consume(on_message_callback=self.on_message, queue=self.callback_queue, auto_ack=True)

        return

    def on_closed(self, conn, c):
        print('close')
        self.io_loop.stop()
        pass

