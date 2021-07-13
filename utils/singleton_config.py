# coding=utf-8
# @CREATE_TIME: 2021/4/24 下午3:05
# @LAST_MODIFIED: 2021/4/24 下午3:05
# @FILE: singleton_config.py
# @AUTHOR: Ray
from datetime import datetime

import yaml

config = yaml.safe_load(open("config.yml"))
version = datetime.now().timestamp()
users_db = [f"7001_%03d" % i for i in range(1, 6)]
users_db.extend([f"7002_%03d" % i for i in range(1, 27)])
