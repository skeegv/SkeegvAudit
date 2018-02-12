from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout


# 首页
def index(request):
    return render(request, 'index.html')


# 登录页
def acc_login(request):
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

        # login将django user 对象写入到 Session.前端 通过 request.user 可以取到.(只要一登录 request.user 就自动封装到整个请求会话里了)
        login(request, user)

        if user:
            return redirect('/')

    return render(request, 'login.html')


# 登出页
def acc_logout(request):
    logout(request)
    return redirect('/login/')
