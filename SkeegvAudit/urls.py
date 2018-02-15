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
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.index),
    url(r'^login/$', views.acc_login),
    url(r'^text/$', views.text),
    url(r'^logout/$', views.acc_logout),
    url(r'^hostlist/$', views.host_list, name="host_list"),
    # multitask 多任务
    url(r'^multitask/$', views.multitask, name='multitask'),
    url(r'^multitask/result/$', views.multitask_result, name='get_task_result'),
    url(r'^multitask/cmd/$', views.multi_cmd, name='multi_cmd'),
    url(r'^api/hostlist/$', views.get_host_list,name='get_host_list'),
    url(r'^api/token/$', views.get_token,name='get_token'),
]
