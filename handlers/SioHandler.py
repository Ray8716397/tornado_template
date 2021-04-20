# coding=utf-8
# @CREATE_TIME: 2021/4/8 上午10:08
# @LAST_MODIFIED: 2021/4/8 上午10:08
# @FILE: SioHandler.py
# @AUTHOR: Ray
import datetime
import numpy as np
import glob
import os
import yaml
import traceback

import socketio
import redis
from urllib import parse

# load config.ini
from lib.common.common_util import logging
from services.rabbitMQ import pub

config = yaml.safe_load(open("config.yml"))

sio = socketio.AsyncServer(async_mode='tornado')
redis_pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True, db=2)
redis.Redis(connection_pool=redis_pool).flushdb()

users_db = [f"7001_%03d" % i for i in range(1, 6)]
users_db.extend([f"7002_%03d" % i for i in range(1, 27)])


class RecordVideoNamespace(socketio.AsyncNamespace):
    namespace = '/record_video'

    async def on_connect(self, sid, environ):
        try:
            dict_qs = parse.parse_qs(environ['QUERY_STRING'])
            if 'uid' in dict_qs.keys():
                user_id = dict_qs['uid'][0]

                if user_id in users_db:
                    await sio.save_session(sid, {'user_id': user_id}, self.namespace)

                    rc = redis.Redis(connection_pool=redis_pool)
                    if rc.get(user_id) is not None:
                        await self.emit('warning', {"msg": "already have one recording", "gohome": False}, room=sid,
                                        namespace=self.namespace)
                    else:
                        rc.set(user_id, sid)
                        await self.emit('connect_succeed', None, room=sid,
                                        namespace=self.namespace)
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
            rc = redis.Redis(connection_pool=redis_pool)

            online_sid = rc.get(user_id)
            if online_sid is not None and online_sid == sid:
                rc.delete(session['user_id'])
            await sio.disconnect(sid)

            for f in glob.glob(os.path.join(config['video_format'].get('input_dir'), f"{sid}.*")):
                os.remove(f)

        except Exception as e:
            logging(
                f"[websocket|disconnect][user_id{user_id}][{datetime.datetime.now().strftime('%Y-%m-%d_%I:%M:%S')}]:"
                f"{traceback.format_exc()}",
                f"logs/error.log")

    async def on_recv(self, sid, data):
        chunk_num = config["h5record_video"].getint("chunk_num")
        """"监听发送来的消息,并使用socketio向所有客户端发送消息"""
        session = await sio.get_session(sid, self.namespace)
        rc = redis.Redis(connection_pool=redis_pool)
        user_id = session.get('user_id')

        print(f"{user_id} recv data length: {len(data[2])}")
        if data is not None:
            try:
                if user_id not in rc.keys():
                    return

                start_record_time = data[0]
                cur_count = int(data[1])
                video_data = data[2]

                with open(os.path.join(config['video_format'].get('input_dir'),
                                       f"{sid}.{start_record_time}_%03d.{user_id}") % cur_count, 'wb') as f:
                    f.write(video_data)

                if cur_count == chunk_num:
                    pub("prediction", 'topic', 'predict.start', f"{user_id}*{start_record_time}")
                    # redis_db0.set(f"{user_id}*{start_record_time}",
                    #               "{session.get('fps')}")

            except Exception as e:
                logging(f"[websocket|recv][user_id|{user_id}][{datetime.datetime.now().strftime('%Y-%m-%d_%I:%M:%S')}]:"
                        f"{traceback.format_exc()}",
                        f"logs/error.log")

    async def on_server_presult(self, sid, res):
        try:
            session = await sio.get_session(sid, self.namespace)
            user_id = session['user_id']

            rc = redis.Redis(connection_pool=redis_pool)
            record_time, score = res.split('*')
            if user_id == '_pserver':
                await self.emit('show_min_res', {"record_time": record_time, "score": score}, room=rc.get(res[0]),
                                namespace=self.namespace)

        except Exception as e:
            logging(
                f"[websocket|on_server_presult][user_id{user_id}][{datetime.datetime.now().strftime('%Y-%m-%d_%I:%M:%S')}]:"
                f"{traceback.format_exc()}",
                f"logs/error.log")

    async def on_get_hour_score(self, sid, last_hour_time):
        try:
            session = await sio.get_session(sid, self.namespace)
            user_id = session['user_id']

            """
                客户端获取每小时得分的平均值
                :param last_hour_time: 上小时时间字符串
                :return:
                """
            force_flag = 'force' in last_hour_time
            if force_flag:
                last_hour_time = last_hour_time.replace('force', '')
            last_hour = last_hour_time[-2:]
            results = sorted(glob.glob(f"logs/{session.get('id')}/{last_hour_time}:*"))
            means = []

            if results[-1][-5:-3] != last_hour or force_flag:
                cur_hour = (datetime.datetime.strptime(last_hour_time, "%Y-%m-%d_%H") + datetime.timedelta(
                    hours=1)).strftime('%Y-%m-%d_%H')
                for i in results:
                    with open(i, 'r') as f:
                        lines = f.readlines()
                        mean_str = float(lines[1].replace('mean - ', '').replace('\n', ''))
                        if mean_str != 0.0:
                            means.append(mean_str)
                if len(means) > 0:
                    await self.emit('show_hour_res', {"record_time": f"{last_hour_time}:00 ~ {cur_hour}:00",
                                                      "score": f"{format(np.array(means).mean(), '.4f')}"}, room=sid)
                else:
                    await self.emit('show_hour_res',
                                    {"record_time": f"{last_hour_time}:00 ~ {cur_hour}:00", "score": f"0"}, room=sid)
            else:
                await self.emit('client_get_hour_score', None, room=sid)

        except Exception as e:
            logging(
                f"[websocket|on_server_presult][user_id{user_id}][{datetime.datetime.now().strftime('%Y-%m-%d_%I:%M:%S')}]:"
                f"{traceback.format_exc()}",
                f"logs/error.log")


sio.register_namespace(RecordVideoNamespace(RecordVideoNamespace.namespace))
