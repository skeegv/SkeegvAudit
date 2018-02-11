#!/usr/bin/env python

import base64
from binascii import hexlify
import getpass
import os
import select
import socket
import sys
import time
import traceback
from audit import models
from paramiko.py3compat import input

import paramiko
try:
    import interactive
except ImportError:
    from . import interactive

def manual_auth(t,username, password):
    t.auth_password(username, password)

def ssh_session(bind_host_user, user_obj):

    # bind_host_user 是HostUserBind 表对象(主机绑定用户中的 其中一条数据对象)
    hostname = bind_host_user.host.ip_addr
    port = bind_host_user.host.port
    username = bind_host_user.host_user.username
    password = bind_host_user.host_user.password
    # now connect
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((hostname, port))
    except Exception as e:
        print('*** Connect failed: ' + str(e))
        traceback.print_exc()
        sys.exit(1)

    try:
        t = paramiko.Transport(sock)
        try:
            t.start_client()
        except paramiko.SSHException:
            print('*** SSH negotiation failed.')
            sys.exit(1)

        try:
            keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        except IOError:
            try:
                keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
            except IOError:
                print('*** Unable to open host keys file')
                keys = {}

        # check server's host key -- this is important.
        key = t.get_remote_server_key()
        if hostname not in keys:
            print('*** WARNING: Unknown host key!')
        elif key.get_name() not in keys[hostname]:
            print('*** WARNING: Unknown host key!')
        elif keys[hostname][key.get_name()] != key:
            print('*** WARNING: Host key has changed!!!')
            sys.exit(1)
        else:
            print('*** Host key OK.')

        if not t.is_authenticated():
            manual_auth(t, username, password)
        if not t.is_authenticated():
            print('*** Authentication failed. :(')
            t.close()
            sys.exit(1)

        chan = t.open_session() # 打开一个会话
        chan.get_pty()  # terminal 获取终端
        chan.invoke_shell() # 调用终端

        # user_obj 是 Django 提供的用户认证模块,user = models.OneToOneField(User)所以需要反向关联才能找到account.
        # bind_host_user  是(HostUserBind表) 主机绑定用户中的 其中一条数据对象.
        session_obj = models.SessionLog.objects.create(account=user_obj.account, host_user_bind=bind_host_user)
        print('*** Here we go!\n')

        # chan 是会话实例/session_obj 是 SessionLog表的对象
        interactive.interactive_shell(chan, session_obj)
        chan.close()
        t.close()

    except Exception as e:
        print('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
        traceback.print_exc()
        try:
            t.close()
        except:
            pass
        sys.exit(1)


