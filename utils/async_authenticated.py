# coding=utf-8
# @CREATE_TIME: 2021/4/20 下午2:09
# @LAST_MODIFIED: 2021/4/20 下午2:09
# @FILE: async_authenticated.py
# @AUTHOR: Ray
import datetime
import functools

import jwt


def async_authenticated(method):
    @functools.wraps(method)
    async def wrapper(self, *args, **kwargs):
        res_data = {}
        user_id = self.session.get("user_id")
        user_type = self.session.get("user_type")
        if user_id and user_type == 'seller':
            return await method(self, *args, **kwargs)
        else:
            self.redirect('/seller/login')

    return wrapper


def admin_async_authenticated(method):
    @functools.wraps(method)
    async def wrapper(self, *args, **kwargs):
        res_data = {}
        user_id = self.session.get("user_id")
        if user_id:
            return await method(self, *args, **kwargs)
        else:
            self.redirect('/login')

    return wrapper


def create_token(payload, salt, timeout=1):
    """
    创建token
    :param payload:  例如：{'user_id':1,'username':'xxx@xxx.xx'}用户信息
    :param salt:  secret_key
    :param timeout: token的过期时间，默认20分钟
    :return:
    """
    headers = {
        'typ': 'jwt',
        'alg': 'HS256'
    }
    payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(days=timeout)
    result = jwt.encode(payload=payload, key=salt, algorithm="HS256", headers=headers)
    return result