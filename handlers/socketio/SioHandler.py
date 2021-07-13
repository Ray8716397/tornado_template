# coding=utf-8
# @CREATE_TIME: 2021/4/8 上午10:08
# @LAST_MODIFIED: 2021/4/8 上午10:08
# @FILE: SioHandler.py
# @AUTHOR: Ray
import datetime
import os
import traceback
import aiofiles
import socketio
from urllib import parse

# load config.ini
from lib.common.common_util import logging, mkdir
from utils.singleton_config import users_db, config

sio = socketio.AsyncServer(async_mode='tornado', cors_allowed_origins="*")


class RecordVideoNamespace(socketio.AsyncNamespace):
    namespace = '/img_ocr'
    connections = {}
    redis_db3 = None

    async def on_connect(self, sid, environ):
        try:
            self.redis_db3 = environ['tornado.handler'].application.redis_db3

            dict_qs = parse.parse_qs(environ['QUERY_STRING'])
            if 'uid' in dict_qs.keys():
                user_id = dict_qs['uid'][0]

                if user_id in users_db:
                    await sio.save_session(sid, {'user_id': user_id, 'file_type': dict_qs['ft'][0]},
                                           self.namespace)

                else:
                    if user_id == '_pserver':
                        await sio.save_session(sid, {'user_id': user_id}, self.namespace)
                    else:
                        await sio.disconnect(sid)

        except Exception as e:
            logging(f"[websocket|connect][user_id{user_id}][{datetime.datetime.now().strftime('%Y-%m-%d_%I:%M:%S')}]:"
                    f"{traceback.format_exc()}",
                    f"logs/error.log")

    async def on_disconnect(self, sid):
        try:
            session = await sio.get_session(sid, self.namespace)
            user_id = session['user_id']

            # online_sid = await self.redis_db2.get(user_id)
            # if online_sid is not None and online_sid == sid:
            #     self.redis_db2.delete(user_id)
            await sio.disconnect(sid)

            del self.connections[user_id]

        except Exception as e:
            logging(
                f"[websocket|disconnect][user_id{user_id}][{datetime.datetime.now().strftime('%Y-%m-%d_%I:%M:%S')}]:"
                f"{traceback.format_exc()}",
                f"logs/error.log")

    async def on_recv(self, sid, data):
        """"监听发送来的消息,并使用socketio向所有客户端发送消息"""
        session = await sio.get_session(sid, self.namespace)
        user_id = session.get('user_id')
        file_type = session.get('file_type', None)

        print(f"recv data")
        if data is not None:
            try:
                start_record_time = data[0]
                video_data = data[1]

                mkdir(os.path.join(config['storage'].get('user_dir'), user_id, 'upload'))
                mkdir(os.path.join(config['storage'].get('user_dir'), user_id, 'json'))
                user_fp = os.path.join(config['storage'].get('user_dir'), user_id, 'upload',
                                       f"{sid}.{start_record_time}.{user_id}.{file_type}")

                async with aiofiles.open(user_fp, 'wb') as f:
                    await f.write(video_data)

                self.redis_db3.lpush('task_list', user_fp)

            except Exception as e:
                logging(f"[websocket|recv][user_id|{user_id}][{datetime.datetime.now().strftime('%Y-%m-%d_%I:%M:%S')}]:"
                        f"{traceback.format_exc()}",
                        f"logs/error.log")

    async def on_server_presult(self, sid, res):
        try:
            session = await sio.get_session(sid, self.namespace)
            user_id = session['user_id']
            print(res)
            if user_id == '_pserver':
                await self.emit('show_res', [res[1], res[2]], room=res[0],
                                namespace=self.namespace)

        except Exception as e:
            logging(
                f"[websocket|on_server_presult][user_id{user_id}][{datetime.datetime.now().strftime('%Y-%m-%d_%I:%M:%S')}]:"
                f"{traceback.format_exc()}",
                f"logs/error.log")


sio.register_namespace(RecordVideoNamespace(RecordVideoNamespace.namespace))
