# coding=utf-8
# @CREATE_TIME: 2021/4/12 下午3:10
# @LAST_MODIFIED: 2021/4/12 下午3:10
# @FILE: rabbitMQ.py
# @AUTHOR: Ray
import pika


def pub(exchange_name, exchange_type, routing_key, message):
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type)

    channel.basic_publish(
        exchange=exchange_name, routing_key=routing_key, body=message)
    print(" [x] Sent %r:%r" % (routing_key, message))
    connection.close()


# def sub():
