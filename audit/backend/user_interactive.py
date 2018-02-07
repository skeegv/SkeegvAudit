import getpass
from django.contrib.auth import authenticate


class UserShell(object):
    """Shell after the user login audit """

    def __init__(self,sys_argv):
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
            # user object,认证对象,user.name
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
            print("self.user", self.user)
            print("self.user_type", type(self.user))
            print("self.user.password",self.user.password)

            print("self.account.host_user_binds",self.user.account.host_user_binds.select_related())
            # print("self.account.host_user_binds",self.user.account.host_user_binds.all()) .select_related()等同于 .all()

            # 显示 User 能访问的HostGroups
            while True:
                host_group = self.user.account.host_groups.select_related()
                for index,group in enumerate(host_group):
                    print("%s.\t%s[%s]"%(index, group,group.host_user_binds.count()))
                print("%s.\t%s[%s]"%(len(host_group), "未分组机器", self.user.account.host_user_binds.count()))

                # 选中的组
                choice = input("select group>: ").strip()
                if choice.isdigit():
                    choice = int(choice)
                    host_bind_list = None
                    if choice >= 0 and choice < len(host_group):
                        selected_group = host_group[choice]
                        host_bind_list = selected_group.host_user_binds.all()
                    elif choice == len(host_group): # 选择的未分组机器
                        host_bind_list = self.user.account.host_user_binds.all()
                    if host_bind_list:
                        # 停留在主机层
                        while True:
                            for index, host in enumerate(host_bind_list):
                                print("%s\t%s" %(index, host))
                            # 选中的主机
                            choice2 = input("select group>: ").strip()
                            if choice2.isdigit():
                                choice2 = int(choice)
                                if choice2 >= 0 and choice2 < len(host_bind_list):
                                    selected_host = host_bind_list[choice2]
                                    print("select host", selected_host)
                            elif choice2 == 'b':
                                break







