# coding=utf-8
# @CREATE_TIME: 2021/4/20 下午2:09
# @LAST_MODIFIED: 2021/4/20 下午2:09
# @FILE: async_authenticated.py
# @AUTHOR: Ray
import datetime
from functools import wraps

import jwt


def async_authenticated(required_user_type="seller"):
    @wraps(required_user_type)
    def decorator(method):
        @wraps(method)
        async def wrapper(self, *args, **kwargs):
            user_id = self.session.get(f"{required_user_type}_id")
            if user_id:
                return await method(self, *args, **kwargs)
            else:
                self.redirect(f"/{required_user_type}/login")

        return wrapper

    return decorator


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
