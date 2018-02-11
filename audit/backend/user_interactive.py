import getpass
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
                self.user = user
                return True
        else:
            print("too many attempts.")

    def start(self):
        """start Interactive Program"""

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

                                            # 在 paramiko 基础上二次开发
                                            ssh_interactive.ssh_session(selected_host, self.user)

                                            """
                                            # 自己写的登录 Shell 和 命令记录
                                            import string
                                            import random
                                            s = string.ascii_lowercase + string.digits
                                            random_tag = ''.join(random.sample(s, 10))
                                            session_obj = models.SessionLog.objects.create(account=self.user.account,host_user_bind=selected_host)
                                            cmd = "sshpass -p %s /usr/local/openssh/bin/ssh %s@%s -p %s -o StrictHostKeyChecking=no -Z %s" %(selected_host.host_user.password,selected_host.host_user.username, selected_host.host.ip_addr, selected_host.host.port, random_tag)

                                            # start strace, and sleep 1 random_tag,session_obj.id
                                            session_tracker_script = "/bin/sh %s %s %s" %(settings.SESSION_TRACKER_SCRIPT,random_tag,session_obj.id)
                                            # 启动会话检测脚本
                                            session_tracker_obj = subprocess.Popen(session_tracker_script,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                                            # 启动登录程序
                                            ssh_channel = subprocess.run(cmd, shell=True)
                                            # 读取结果
                                            print(session_tracker_obj.stdout.read(), session_tracker_obj.stderr.read())
                                            """
                                    elif choice2 == 'b':
                                        break
            # 捕获 control + c (Crtl+c) 异常
            except KeyboardInterrupt as e:
                pass

