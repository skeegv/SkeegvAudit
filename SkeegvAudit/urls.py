"""SkeegvAudit URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from audit import views

urlpatterns = [
    # URL
    # 管理页面
    url(r'^admin/', admin.site.urls),
    # 首页
    url(r'^$', views.index),
    # 登录页
    url(r'^login/$', views.acc_login),
    # 登出页
    url(r'^logout/$', views.acc_logout),
    # 主机列表
    url(r'^hostlist/$', views.host_list, name="host_list"),

    # multitask 多任务
    url(r'^multitask/$', views.multitask, name='multitask'),
    # 获取多任务的结果
    url(r'^multitask/result/$', views.multitask_result, name='get_task_result'),
    # 多任务 命令
    url(r'^multitask/cmd/$', views.multi_cmd, name='multi_cmd'),
    # 多任务 文件
    url(r'^multitask/file_transfer/$', views.multi_file_transfer, name='multi_file_transfer'),

    # API
    url(r'^api/hostlist/$', views.get_host_list,name='get_host_list'),
    url(r'^api/token/$', views.get_token,name='get_token'),
    url(r'^api/task/file_upload/$', views.task_file_upload, name='task_file_upload'),

    # 文件
    url(r'^api/task/file_download/$', views.task_file_download, name='task_file_download'),


]
