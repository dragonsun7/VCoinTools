# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'


# 使用云之讯接口发送短信
# http://www.ucpaas.com/


import requests
import uuid
import json


SID = 'd1aa9ecc2187351c13f05000a2de9537'
TOKEN = '0ecedac11e42529ccb24be9bf68c5664'
APP_ID = '6fc93687417f49658fcc4e19af1e44ba'
TEMPLATE_ID = '314842'


def send_sms(mobile: str, params: list)-> dict:
    """
    发送短信
    :param mobile: 手机号码
    :param params: 参数列表，个数取决于短信模板里设置的参数数量
    :return: 短信平台返回的信息
    """
    url = 'https://open.ucpaas.com/ol/sms/sendsms'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json;charset=utf-8'
    }
    params = {
        'sid': SID,
        'token': TOKEN,
        'appid': APP_ID,
        'templateid': TEMPLATE_ID,
        'param': ','.join(params),
        'mobile': mobile,
        'uid': str(uuid.uuid4()).replace('-', '')
    }
    response = requests.post(url, json.dumps(params), headers=headers)
    content = str(response.content, encoding='utf-8')
    return json.loads(content)


if __name__ == '__main__':
    print(send_sms('13980660107', ['OKB_USDT', '拉升']))
