import json


def encode_msg(usr, msg, pwd):
    msg_dict = {'usr': usr, 'msg': msg, 'pwd': pwd}
    msg = json.dumps(msg_dict).encode()
    return msg


def decode_msg(msg):
    msg = msg.decode()
    # temp
    msg_dict = json.loads(msg)
    usr = msg_dict.get('usr')
    msg = msg_dict.get('msg')
    pwd = msg_dict.get('pwd')
    return usr, msg, pwd
