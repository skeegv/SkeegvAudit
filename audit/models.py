from django.db import models
from django.contrib.auth.models import User

# 先设计所需要的表,再设计所需要的字段.


class IDC(models.Model):
    name = models.CharField(verbose_name=' 机房名称', max_length=64,unique=True)

    def __str__(self):
        return self.name

class Host(models.Model):
    """存储所有主机信息"""
    hostname = models.CharField(verbose_name='昵称', max_length=64,unique=True)
    ip_addr = models.GenericIPAddressField(verbose_name='ip',unique=True)
    port = models.IntegerField(default=22)
    idc = models.ForeignKey("IDC")
    # host_groups = models.ManyToManyField('HostGroup')
    # host_users = models.ManyToManyField("HostUser")

    enabled = models.BooleanField(default=True)

    def __str__(self):
        return "%s-%s" %(self.hostname,self.ip_addr)


class HostGroup(models.Model):
    """主机组"""
    name = models.CharField(verbose_name='组名', max_length=64,unique=True)
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
    username = models.CharField(verbose_name='连接用户名', max_length=32,)
    password = models.CharField(verbose_name='如是密钥无需密码', blank=True, null=True,max_length=128)

    def __str__(self):
        return "%s-%s-%s" %(self.get_auth_type_display(), self.username, self.password)

    class Meta:
        unique_together = ('username', 'password')


class HostUserBind(models.Model):
    """绑定主机和用户"""
    host =models.ForeignKey("Host")
    host_user = models.ForeignKey('HostUser')

    def __str__(self):

        return "%s-%s" %(self.host,self.host_user)

    class Meta:
        unique_together = ('host','host_user')



class AuditLog(models.Model):
    """审计日志"""


class Account(models.Model):
    """堡垒机账户
    两种方式
    1.扩展
    2.继承
    audit_shell.py 拿到的 user 对象是  user = models.OneToOneField(User)
    所以需要反向关联才能找到 host_user_bind
    user.account.host_user_bind
    """
    user = models.OneToOneField(User)
    name = models.CharField(max_length=64)

    host_user_binds = models.ManyToManyField('HostUserBind', blank=True)
    host_groups = models.ManyToManyField('HostGroup', blank=True)




