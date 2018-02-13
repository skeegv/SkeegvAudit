import json
import random, string
import datetime
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import authenticate, login, logout  # 用于用户检测,用户登录,退出
from django.contrib.auth.decorators import login_required  # 用于检测用户是否已登录
from audit import models


# 首页
# @login_required(login_url='/login/')
@login_required  # 在 settings.py 里我们已经写了 LOGIN_URl='/lognin/' 所以这里就不用写了
def index(request):
    return render(request, 'index.html')


# 登录页
def acc_login(request):
    error = ''
    if request.method == "POST":
        # 获取用户输入的 username and password
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 验证用户输入的 username and password
        user = authenticate(username=username, password=password)
        """
        print(user)
         # skeegv
        print(type(user))  
         #<class 'django.contrib.auth.models.User'>
        """

        if user:
            # login将django user 对象写入到 Session.前端 通过 request.user 可以取到.(只要一登录 request.user 就自动封装到整个请求会话里了)
            login(request, user)
            # 登录成功后也要根据 next 来跳转,因为我们配置了Django 的用户认证 login_url(装饰器会自动帮我们获取上一次request.path 的记录并写在 next 参数里)
            return redirect(request.GET.get('next') or '/')
        else:
            error = "Wrong username or password!"

    return render(request, 'login.html', {'error': error})


# 登出页
@login_required
def acc_logout(request):
    logout(request)
    return redirect('/login/')


# 主机列表页
@login_required
def host_list(request):
    return render(request, 'hostlist.html')


# 获取主机列表
@login_required
def get_host_list(request):
    gid = request.GET.get('gid')
    if gid:
        if gid == '-1':  # 取未分组的主机
            host_list = request.user.account.host_user_binds.all()
        else:
            group_obj = request.user.account.host_groups.get(id=gid)
            host_list = group_obj.host_user_binds.all()

        data = json.dumps(list(host_list.values('id', 'host__hostname',
                                                'host__ip_addr', 'host__port',
                                                'host_user__username',
                                                'host__idc__name')))

        return HttpResponse(data)


# 获取 token
@login_required
def get_token(request):
    """生成 token 并返回"""

    """
    print(request.POST)
    < QueryDict: {'bind_host_id': ['4'],'csrfmiddlewaretoken': ['QDmVoHtzYQq1TiL83Pv7JXlBl8dSvfJaxYrrLJbg2ZnPjd8WrbAvntBClSnxfmSl']} >
    """
    bind_host_id = request.POST.get('bind_host_id')

    # 当前时间 -300秒(既5分钟)
    time_obj = datetime.datetime.now() - datetime.timedelta(seconds=300)

    # 查询当前 DJango 登录用户是否在5分种之内已经生成,如果是(那么继续返回已经生的那个)
    exist_token_obj = models.Token.objects.filter(account_id=request.user.account.id,
                                                  host_user_bind=bind_host_id,
                                                  date__gt=time_obj)    # __gt 大于

    if exist_token_obj: #has token already
        """
        print(exist_token_obj[0].expire)
        300
        
        print(exist_token_obj[0].id)
        18
        
        print(exist_token_obj[0].host_user_bind)
        Slave-10.0.0.5-ssh-password-root-123456

        print(exist_token_obj[0].val)
        oa4bf75k

        print(exist_token_obj.values())
        <QuerySet [{'id': 18, 'host_user_bind_id': 1, 'val': 'oa4bf75k', 'account_id': 1, 'expire': 300, 'date': datetime.datetime(2018, 2, 13, 2, 2, 47, 24882, tzinfo=<UTC>)}]>
        """
        token_data = {'token': exist_token_obj[0].val}
    else:
        # 验证生成的随机token是否已经存在于数据库
        while True:
            # 生成8位随机token
            token_val = ''.join((random.sample(string.ascii_lowercase + string.digits, 8)))
            # 对比数据库中是否已经有一样的 token
            token = models.Token.objects.filter(val=token_val)
            # 如果没有既使用当前生成的 token 进行创建            print('end 数据库里已存在')
            if not token:

                token_obj = models.Token.objects.create(
                    host_user_bind_id=bind_host_id,
                    account=request.user.account,
                    val=token_val,
                )
                token_data = {'token': token_val}

                return HttpResponse(json.dumps(token_data))

    return HttpResponse(json.dumps(token_data))
