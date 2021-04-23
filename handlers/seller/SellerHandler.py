# coding=utf-8
# @CREATE_TIME: 2021/4/20 下午2:09
# @LAST_MODIFIED: 2021/4/20 下午2:09
# @FILE: AdminHandler.py
# @AUTHOR: Ray
import traceback
from datetime import datetime

import aiofiles

from handlers.BaseHandler import BaseHandler
from lib.common.common_util import logging
from utils.async_authenticated import async_authenticated


class LoginHandler(BaseHandler):
    """
    登录
    """

    async def get(self, *args, **kwargs):
        if self.current_user and self.session.get("user_type") == 'seller':  # 若用户已登录
            self.redirect('/seller')  # 那么直接跳转到主页
        else:
            # nextname = self.get_argument('next', '')  # 将原来的路由赋值给nextname
            await self.render('login.html', msg='')  # 否则去登录界面

    async def post(self, *args, **kwargs):
        user_id = self.get_argument('user_id', None)
        res = await self.queryone("SELECT COUNT(id) FROM seller where id=%s", user_id)
        if res['COUNT(id)']:
            self.session.set('seller_id', user_id)  # 将前面设置的cookie设置为username，保存用户登录信息
            self.redirect('/')
        else:
            await self.render('login.html', title="michimura", msg='ユーザが存在しません')  # 不通过，有问题


class AccountRegisterHandler(BaseHandler):
    """
    注册
    """

    async def get(self, *args, **kwargs):
        await self.render('account_register.html', msg='')

    async def post(self, *args, **kwargs):
        mode = self.get_argument('mode', None)
        id = self.get_argument('user_id', None)

        if mode == 'check':
            self.write({'id_exist': (await self.queryone("SELECT COUNT(id) FROM seller where id=%s", id))['COUNT(id)']})

        else:
            pwd = self.get_argument('user_password', None)
            company_name = self.get_argument('company_name', None)
            tel1 = self.get_argument('tel1', None)

            try:
                await self.execute(
                    "INSERT INTO seller (id,pwd)"
                    "VALUES (%s,%s)",
                    id,
                    pwd,
                )
            except Exception:
                logging(
                    f"[RegisterHandler][{datetime.now().strftime('%Y-%m-%d_%I:%M:%S')}]:{traceback.format_exc()}",
                    f"logs/error/{datetime.now().strftime('%Y-%m-%d')}")
            self.write('ok')

        return await self.finish()


class HouseRegisterHandler(BaseHandler):
    """
    房产登录
    """
    @async_authenticated(required_user_type="seller")
    async def get(self, *args, **kwargs):
        await self.render('house_register.html', msg='')

    @async_authenticated(required_user_type="seller")
    async def post(self, *args, **kwargs):
        # seller_id = self.current_user
        type = self.get_argument('type', None)
        area = self.get_argument('area', None)
        price = self.get_argument('price', None)
        street = self.get_argument('street', None)
        county_id = self.get_argument('county_id', None)
        city_id = self.get_argument('city_id', None)
        floors = self.get_argument('floors', None)
        layout_id = self.get_argument('layout_id', None)
        nearby_station_id = self.get_argument('nearby_station_id', None)

        try:
            await self.execute(
                "INSERT INTO house (`seller_id`,`type`,`price`,`price`,`street`,`city_id`,`floors`,`price`,)"
                "VALUES (%s,%s)",
                id,
                pwd,
            )
        except Exception:
            logging(
                f"[HouseRegisterHandler][{datetime.now().strftime('%Y-%m-%d_%I:%M:%S')}]:{traceback.format_exc()}",
                f"logs/error/{datetime.now().strftime('%Y-%m-%d')}")
        self.write('ok')

        return await self.finish()


class LogoutHandler(BaseHandler):
    """
    登出
    """

    @async_authenticated(required_user_type="seller")
    async def get(self, *args, **kwargs):
        # self.session.set('user_info','') #将用户的cookie清除
        self.clear_all_cookies()
        self.session.delete('seller_id')
        self.redirect('/login')


class UploadHandler(BaseHandler):
    """
    上传
    """

    @async_authenticated(required_user_type="seller")
    async def post(self):
        ret_data = {}

        files_meta = self.request.files.get("house_image", None)
        if not files_meta:
            self.set_status(400)
            ret_data["front_image"] = "请上传图片"
        else:
            for meta in files_meta:
                filename = meta["filename"]
                new_filename = "{uuid}_{filename}".format(uuid=uuid.uuid1(), filename=filename)
                file_path = os.path.join(self.settings["MEDIA_ROOT"], new_filename)

                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(meta["body"])

                ret_data['file_path'] = file_path

        return self.finish(ret_data)
