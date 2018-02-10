import getpass
import datetime
import subprocess
from audit import models
from django.conf import settings
from audit.backend import ssh_interactive
from django.contrib.auth import authenticate


class UserShell(object):
    """Shell after the user login audit """

    def __init__(self, sys_argv):
        self.sys_argv = sys_argv
        self.user = None

    def auth(self):
        """auth function"""

        count = 0
        while count < 3:
            username = input("username: ").strip()
            password = getpass.getpass("password: ").strip()
            user = authenticate(username=username, password=password)
            # None 代表不成功
            # user object,Django的认证对象,我们要拿到Account 里的name 需要 user.name
            if not user:
                count += 1
                print("Invalid username of password!")
            else:
                # 把 Django 的  user 对象 赋值给 self.user
                self.user = user
                return True
        else:
            print("too many attempts.")

    def token_auth(self):
        count = 0
        while count < 3:
            user_input = input("Input your access token,press Enter if doesn't have: ")
            # token 的位数的8位
            if len(user_input) == 0:
                return
            if len(user_input) != 8:
                print('token length is 8')
            else:
                # 获取当前时间 - 300 秒(既5分钟) 做超时时间的验证
                time_obj = datetime.datetime.now() - datetime.timedelta(seconds=300)
                # token_obj 可能会取到多个(几乎不可能,因为在写入数据库的时候已经限制了必须是唯一的),我们要取的是5分钟之内最新的才算是合法的 token
                token_obj = models.Token.objects.filter(val=user_input, date__gt=time_obj).first()

                if token_obj:
                    if token_obj.val == user_input:  # 表示口令对上了
                        # 将要登录的主机对象返回
                        return token_obj

            count += 1

    def start(self):
        """start Interactive Program"""

        token_obj = self.token_auth()
        if token_obj:
            """
            在 paramiko 基础上二次开发
            把 Django 的  user 对象 赋值给 self.user.要拿到Account 里的name 需要 user.name
            因为 django 的 user 关联  account 表
            selected_host 是主机对象,既用于登录那一台主机所需要的信息
            self.user 主要用于日志的记录
            """
            # self.user 是 Django 认证成功之后的对象.
            self.user = token_obj.account.user
            ssh_interactive.ssh_session(token_obj.host_user_bind, self.user)
            # 不需要往下走了,退出程序即可
            exit()

        if self.auth():
            # print("self.account.host_user_binds",self.user.account.host_user_binds.all()) .select_related()等同于 .all()
            try:
                # 显示 User 能访问的HostGroups
                while True:
                    host_group = self.user.account.host_groups.select_related()
                    for index, group in enumerate(host_group):
                        print("%s.\t%s[%s]" % (index, group, group.host_user_binds.count()))
                    print("%s.\t%s[%s]" % (len(host_group), "未分组机器", self.user.account.host_user_binds.count()))
                    # 选中的组
                    choice = input("select group>: ").strip()
                    if choice.isdigit():
                        choice = int(choice)
                        host_bind_list = None
                        if choice >= 0 and choice < len(host_group):
                            selected_group = host_group[choice]
                            host_bind_list = selected_group.host_user_binds.all()
                        elif choice == len(host_group):  # 选择的未分组机器
                            # host_bind_list 是所有绑定主机和用户的记录
                            host_bind_list = self.user.account.host_user_binds.all()
                        elif choice == 'b':
                            break

                        if host_bind_list:
                            # 停留在主机层
                            while True:
                                for index, host in enumerate(host_bind_list):
                                    print("%s\t%s" % (index, host))
                                # 选中的主机
                                choice2 = input("select group>: ").strip()
                                if choice2.isdigit():
                                    choice2 = int(choice2)
                                    if choice2 >= 0 and choice2 < len(host_bind_list):
                                        # selected_host 是(HostUserBind表) 主机绑定用户中的 其中一条数据对象
                                        selected_host = host_bind_list[choice2]
                                        """
                                        在 paramiko 基础上二次开发
                                        把 Django 的  user 对象 赋值给 self.user.要拿到Account 里的name 需要 user.name
                                        因为 django 的 user 关联  account 表
                                        selected_host 是主机对象,既用于登录那一台主机所需要的信息
                                        self.user 主要用于日志的记录
                                        """
                                        ssh_interactive.ssh_session(selected_host, self.user)
                                    elif choice2 == 'b':
                                        break
            # 捕获 control + c (Crtl+c) 异常
            except KeyboardInterrupt as e:
                pass
