# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.


import socket
import sys
import time
from audit import models
from paramiko.py3compat import u

# windows does not have termios...
try:
    import termios
    import tty
    has_termios = True
except ImportError:
    has_termios = False


# chan 是会话实例/session_obj 是 SessionLog表的对象
def interactive_shell(chan, session_obj):
    # 如果有终端
    if has_termios:
        # Unix 通用协议标准
        posix_shell(chan,session_obj)
    else:
        # Windows PowerShell
        windows_shell(chan,session_obj)


def posix_shell(chan,session_obj):
    import select  # select 用于检测文件句柄

    # sys.stdin(标准输入)、sys.stdout(标准输出)和sys.stderr(错误输出) 。
    oldtty = termios.tcgetattr(sys.stdin)

    try:
        # sys.stdin.fileno() 标准输入通常使用档案描述器0，标准输出是1，标准错误是2，进一步开启的档案则会是3、4、5等数字。对于档案物件，可以使用fileno（）方法来取得.
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        chan.settimeout(0.0)

        # 用于命令拼接
        cmd = ''
        # 写入日志
        f = open('ssh_audit.log','w')
        while True:
            r, w, e = select.select([chan, sys.stdin], [], [])
            if chan in r: # 远程有返回命令结果
                try:
                    # 接收数据：使用recv(max) max参数表示一次最多接收的字节数
                    x = u(chan.recv(1024)) #如果是字节就转换成万国码(如果是 str 那么还是返回 str)

                    # 如果x没有数据了,表示已经断开.
                    if len(x) == 0:
                        # 退出的时候打印
                        sys.stdout.write('\r\n*** EOF\r\n')
                        break

                    # sys.stdout.write（）只能输出字符串/print（）可以输出任何东西：字符串/数字/字典/数列等
                    sys.stdout.write(x)

                    # 在Linux系统下，必须加入sys.stdout.flush()才能一秒输一个结果
                    # 在Windows系统下，加不加sys.stdout.flush()都能一秒输出一个结果
                    sys.stdout.flush()  # -> 这句代码的意思是刷新输出

                # Socket超时
                except socket.timeout:
                    pass
            # 如果键盘有输入
            if sys.stdin in r:
                # 只读一个
                x = sys.stdin.read(1)
                # 读不到
                if len(x) == 0:
                    break
                if x == '\r':
                    print('--->', cmd)

                    # 写入数据库
                    models.AuditLog.objects.create(session=session_obj,cmd=cmd)
                    cmd = ''
                else:
                    cmd += x
                # 读到:发送数据：使用send()
                chan.send(x)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)


# thanks to Mike Looijmans for this code
def windows_shell(chan):
    import threading

    sys.stdout.write("Line-buffered terminal emulation. Press F6 or ^Z to send EOF.\r\n\r\n")

    def writeall(sock):
        while True:
            data = sock.recv(256)
            if not data:
                sys.stdout.write('\r\n*** EOF ***\r\n\r\n')
                sys.stdout.flush()
                break
            sys.stdout.write(data)
            sys.stdout.flush()

    writer = threading.Thread(target=writeall, args=(chan,))
    writer.start()

    try:
        while True:
            d = sys.stdin.read(1)
            if not d:
                break
            chan.send(d)
    except EOFError:
        # user hit ^Z or F6
        pass
