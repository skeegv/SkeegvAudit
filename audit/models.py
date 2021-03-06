from django.db import models
from django.contrib.auth.models import User


# 先设计所需要的表,再设计所需要的字段.


class IDC(models.Model):
    name = models.CharField(verbose_name=' 机房名称', max_length=64, unique=True)

    def __str__(self):
        return self.name


class Host(models.Model):
    """存储所有主机信息"""
    hostname = models.CharField(verbose_name='昵称', max_length=64, unique=True)
    ip_addr = models.GenericIPAddressField(verbose_name='ip', unique=True)
    port = models.IntegerField(default=22)
    idc = models.ForeignKey("IDC")
    # host_groups = models.ManyToManyField('HostGroup')
    # host_users = models.ManyToManyField("HostUser")

    enabled = models.BooleanField(default=True)

    def __str__(self):
        return "%s-%s" % (self.hostname, self.ip_addr)


class HostGroup(models.Model):
    """主机组"""
    name = models.CharField(verbose_name='组名', max_length=64, unique=True)
    host_user_binds = models.ManyToManyField("HostUserBind")

    def __str__(self):
        return self.name


class HostUser(models.Model):
    """
    存储远程主机的用户信息
    如果选择的是密钥,需在指定的配置中读取
    """

    auth_type_choices = ((0, 'ssh-password'), (1, 'ssh-key'))
    auth_type = models.SmallIntegerField(verbose_name="连接方式", choices=auth_type_choices)
    username = models.CharField(verbose_name='连接用户名', max_length=32, )
    password = models.CharField(verbose_name='如是密钥无需密码', blank=True, null=True, max_length=128)

    def __str__(self):
        return "%s-%s-%s" % (self.get_auth_type_display(), self.username, self.password)

    class Meta:
        unique_together = ('username', 'password')


class HostUserBind(models.Model):
    """绑定主机和用户"""
    host = models.ForeignKey("Host")
    host_user = models.ForeignKey('HostUser')

    def __str__(self):
        return "%s-%s" % (self.host, self.host_user)

    class Meta:
        unique_together = ('host', 'host_user')


class SessionLog(models.Model):
    """登录日志"""
    account = models.ForeignKey("Account")
    host_user_bind = models.ForeignKey("HostUserBind")
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "%s-%s" % (self.account, self.host_user_bind)


class AuditLog(models.Model):
    """审计日志"""
    session = models.ForeignKey("SessionLog")
    cmd = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s-%s" % (self.session, self.cmd)


class Account(models.Model):
    """堡垒机账户
    两种方式
    1.扩展
    2.继承
    audit_shell.py 拿到的 user 对象是  user = models.OneToOneField(User)
    所以需要反向关联才能找到 host_user_bind ,反向关联的 ORM (user.account.host_user_bind)
    """
    user = models.OneToOneField(User)
    name = models.CharField(max_length=64)

    host_user_binds = models.ManyToManyField('HostUserBind', blank=True)
    host_groups = models.ManyToManyField('HostGroup', blank=True)

    def __str__(self):
        return self.name


class Token(models.Model):
    """主机 Token"""
    host_user_bind = models.ForeignKey("HostUserBind")
    # 只必须是唯一,因为在5分钟之内可能会有2个用户生成同样的
    val = models.CharField(verbose_name='Token', max_length=128, unique=True)
    account = models.ForeignKey("Account")
    expire = models.IntegerField("超时时间(s)", default=300)
    date = models.DateTimeField("Token 生成时间", auto_now_add=True)

    def __str__(self):
        return "%s-  token:%s" % (self.host_user_bind, self.val)

    """
    这里需要再写一个脚本用于每天清除超时,也就是超过5分钟的记录.不然
    数据库会越来越大.会越来越不好维护.因为 val( 既 token )是唯一的.
    """


class Task(models.Model):
    """存储任务信息"""
    task_type_choices = ((0, 'cmd'), (1, 'file_transfer'))
    task_type = models.SmallIntegerField(choices=task_type_choices)
    content = models.TextField("任务内容")
    timeout = models.IntegerField("任务超时时间(s)", default=300)
    account = models.ForeignKey("Account")
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "taskid:%s - %s - %s" % (self.id, self.get_task_type_display(), self.content)


class TaskLog(models.Model):
    """命令返回的结果"""
    task = models.ForeignKey('Task')
    host_user_bind = models.ForeignKey('HostUserBind')
    result = models.TextField('命令结果', default='init...')
    date = models.DateTimeField(auto_now_add=True)
    # 连接上就算成功,连接不上就算失败(这里只关注连接)
    status_choices = ((0, '成功'), (1, '失败'), (2, '超时'), (3, '初始化'))
    status = models.SmallIntegerField(choices=status_choices)

    class Meta:
        # 一个任务中,一台主机只能有一个返回结果.
        unique_together = ('task', 'host_user_bind')


class Party(models.Model):
    """同学聚会"""
    name = models.CharField('同学姓名',max_length=128)
    Amount_money = models.SmallIntegerField('金额')
    type = models.CharField('种类',max_length=25,default= '[人民币] 元')
    date = models.DateTimeField('日期', auto_now_add=True)


