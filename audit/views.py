import json
import random
import string
import os
from audit import models
from audit import task_handler
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import authenticate, login, logout  # 用于用户检测,用户登录,退出
from django.contrib.auth.decorators import login_required  # 用于检测用户是否已登录
from django.views.decorators.csrf import csrf_exempt    # 免除csrf_token 验证
from django.conf import settings

# json 扩展:支持时间格式化
class JsonCustomEncoder(json.JSONEncoder):
    """
        使用方法
        data = json.dumps(result, cls=JsonCustomEncoder)
        return HttpResponse(data)
    """
    # 我们有 default 方法 就会优先执行我们自己写的
    def default(self, value):
        from datetime import date
        from datetime import datetime
        # 如果是 datetime 类型
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        # 如果是 date 类型
        elif isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        # 不是时间就是用他默认的
        else:
            return json.JSONEncoder.default(self, value)


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
    import datetime
    # 当前时间 -300秒(既5分钟)
    time_obj = datetime.datetime.now() - datetime.timedelta(seconds=300)

    # 查询当前 DJango 登录用户是否在5分种之内已经生成,如果是(那么继续返回已经生的那个)
    exist_token_obj = models.Token.objects.filter(account_id=request.user.account.id,
                                                  host_user_bind=bind_host_id,
                                                  date__gt=time_obj)  # __gt 大于

    if exist_token_obj:  # has token already
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
        <QuerySet [{'id': 18, 'host_user_bind_id': 1, 'val': 'oa4bf75k', 'account_id': 1, 'expire': 300, 'date': datetime(2018, 2, 13, 2, 2, 47, 24882, tzinfo=<UTC>)}]>
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


# multitask 多任务 命令
@login_required
def multi_cmd(request):
    return render(request, 'multi_cmd.html')


# 批量执行 命令 和 文件
@login_required
def multitask(request):
    # 生成一个对象
    task_obj = task_handler.Task(request)

    # 使用对象里的验证方法
    if task_obj.is_valid():
        # 验证通过
        task_id = task_obj.run()
        return HttpResponse(json.dumps({'task_id': task_id}))

    # 认证不通过,既发送错误信息给前端
    return HttpResponse(json.dumps(task_obj.errors))


# 获取批量执行的结果
@login_required
def multitask_result(request):
    task_id = request.GET.get('id')
    task_obj = models.Task.objects.get(id=task_id)

    """
    [{
        'task_log_id:,
        'hostname'
        'ipaddr',
        'status',
        'username'
    }]
    """
    result = list(task_obj.tasklog_set.values('id', 'status',
                                              'host_user_bind__host__hostname',
                                              'host_user_bind__host__ip_addr',
                                              'result',
                                              ))

    return HttpResponse(json.dumps(result))


# multitask 多任务 文件
@login_required
def multi_file_transfer(request):
    # 生成8位随机token
    random_str = ''.join((random.sample(string.ascii_lowercase + string.digits, 8)))

    # Python 的内建函数 locals() 。它返回的字典对所有局部变量的名称与值进行映射，
    return render(request,'multi_file_transfer.html', locals())


@login_required
@csrf_exempt    #免除 cdrf_token 验证
def task_file_upload(request):
    # 随机字符串
    random_str = request.GET.get("random_str")

    # 文件上传暂存路径 格式:文件路径/当前登录用户名/随机字符串
    upload_to = "%s/%s/%s" % (settings.FILE_UPLOADS, request.user.account.id, random_str)

    # 如果文件上传暂存路径不存在 既 创建
    if not os.path.isdir(upload_to):
        # 递归创建 如不需要可以  os.mkdir() os.makedirs 函数还有第三个参数 exist_ok，该参数为真时执行mkdir -p，但如果给出了mode参数，目标目录已经存在并且与即将创建的目录权限不一致时，会抛出OSError异常。
        os.makedirs(upload_to,exist_ok=True)

    # 获取上传的文件对象
    file_obj = request.FILES.get('file')

    # 打开文件
    f = open("%s/%s" % (upload_to, file_obj.name), 'wb')

    # 分块写入文件;
    for chunk in file_obj.chunks():
        f.write(chunk)

    # 关闭文件
    f.close()
    """
        f = request.FILES
        print(f)
        <MultiValueDict: {'file': [<InMemoryUploadedFile: 26073028_165757184038577_8143277732885692416_n.jpg (image/jpeg)>]}>
    """
    return HttpResponse('ok')
