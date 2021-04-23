# coding=utf-8
# @CREATE_TIME: 2021/4/20 下午2:09
# @LAST_MODIFIED: 2021/4/20 下午2:09
# @FILE: AdminHandler.py
# @AUTHOR: Ray
import aiofiles
import tornado.web

from handlers.BaseHandler import BaseHandler


class LoginHandler(BaseHandler):
    """
    登录
    """

    async def get(self, *args, **kwargs):
        if self.current_user:  # 若用户已登录
            self.redirect('/')  # 那么直接跳转到主页
        else:
            nextname = self.get_argument('next', '')  # 将原来的路由赋值给nextname
            await self.render('login.html', nextname=nextname, msg='')  # 否则去登录界面

    async def post(self, *args, **kwargs):
        username = self.get_argument('user_id', None)

        res = await self.queryone("SELECT COUNT(id) FROM users where email=%s", username)
        if res['COUNT(id)']:
            self.session.set('id', username)  # 将前面设置的cookie设置为username，保存用户登录信息
            self.redirect('/')
        else:
            await self.render('login.html', title="michimura", msg='ユーザが存在しません')  # 不通过，有问题


class RegisterHandler(BaseHandler):
    """
    注册
    """

    async def get(self, *args, **kwargs):
        await self.render('account_register.html', msg='')  # 否则去登录界面

    async def post(self, *args, **kwargs):
        username = self.get_argument('user_id', None)
        pwd = self.get_argument('user_pwd', None)

        # pool = await aiomysql.create_pool(host=self.db["host"], port=self.db["port"],
        #                                   guest=self.db["guest"], password=self.db["password"],
        #                                   db=self.db["db"], charset="utf8")
        # async with pool.acquire() as conn:
        #     async with conn.cursor() as cur:
        #         await cur.execute("SELECT id, name, email, address, message from message")
        #         print(cur.description)
        #         id, name, email, address, message = await cur.fetchone()
        # pool.close()
        # await pool.wait_closed()
        return await self.render('message.html')


class LogoutHandler(BaseHandler):
    """
    登出
    """
    @tornado.web.authenticated
    async def get(self, *args, **kwargs):
        # self.session.set('user_info','') #将用户的cookie清除
        self.clear_all_cookies()
        self.session.delete('id')
        self.redirect('/login')


class UploadHandler(BaseHandler):
    """
    上传
    """
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
