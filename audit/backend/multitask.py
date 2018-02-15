# -*- coding: utf-8 -*-
import os
import sys
import paramiko
import multiprocessing  # multiprocessing 是 python 的多进程并行库，可以使用进程池 multiprocessing.pool 来自动管理进程任务。


# 批量执行命令
def cmd_run(tasklog_obj, cmd_str):

    try:
        bind_host_obj = tasklog_obj.host_user_bind

        # print('run cmd:', bind_host_obj.host.ip_addr, cmd_str)
        print('run cmd:', bind_host_obj, cmd_str)

        # 建立ssh连接 使用密码连接：
        ssh = paramiko.SSHClient()
        # 这行代码的作用是允许连接不在know_hosts文件中的主机。就是自动填写 yes
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # timeout 设置超时时间
        ssh.connect(bind_host_obj.host.ip_addr,
                    bind_host_obj.host.port,
                    bind_host_obj.host_user.username,
                    bind_host_obj.host_user.password,
                    timeout=15)

        stdin, stdout, stderr = ssh.exec_command(cmd_str)

        result = stdout.read() + stderr.read()

        # 如果没有返回值
        if len(result) > 0:
            result = result.decode('utf8')
            print(result)
            tasklog_obj.result = result or 'cmd has no result.'
        else:
            tasklog_obj.result = 'cmd has no result.'

        ssh.close()
        tasklog_obj.status = 0
        tasklog_obj.save()
    except Exception as e:
        print('error: ', e)


# 批量文件
def file_transfer(bind_host_obj):
    pass


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, BASE_DIR)
    import django
    # 1.set path Django.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SkeegvAudit.settings")
    # 2.手动注册 Django 所有 app
    django.setup()
    # 放在这里是因为我们执行文件的时候的 路径原因,我们把当前目录的路径放在第一位,所以导入的时候,不放在这里会找不到.
    from audit import models
    from SkeegvAudit import settings

    # sys.argv:是从程序外部获取参数的桥梁,从外部取得的参数可以是多个，所以获得的是一个列表（list)，也就是说sys.argv其实可以看作是一个列表，所以才能用[]提取其中的元素。其第一个元素是程序本身，随后才依次是外部给予的参数。
    task_id = sys.argv[1]

    """
        1. 根据 Taskid 拿到任务对象
        2. 拿到任务关联的所有主机
        3.根据任务类型调用多线程,执行不同的方法(CPU 密集型可以用多进程(多进程还可以利用多核),IO 密集型可以使用多线程)如果线程与线程之间不需要进行数据共享,那么也可以改成多进程(这样就可以利用多核来提升效率)
        4.每个子任务执行完毕后,自己把结果写入数据库
    """
    task_obj = models.Task.objects.get(id=task_id)
    print(task_obj)

    # 创建进程池(multiprocessing包是Python中的多进程管理包)
    pool =  multiprocessing.Pool(processes=settings.MaxTaskProcesses) # Pool类用于需要执行的目标很多，而手动限制进程数量又太繁琐时，如果目标少且不用控制进程数量则可以用Process类。

    if task_obj.task_type == 0: # cmd
        task_func = cmd_run
    else:
        task_func = file_transfer

    # task_obj.tasklog_set.all() 是取 task表里的 id 并反向关联到 tasklog 表里,取跟这个 task id 一样的主机信息.
    for tasklog_obj in task_obj.tasklog_set.all():
        # 进程池
        pool.apply_async(task_func, args=(tasklog_obj, task_obj.content))
    pool.close()
    """
    报错信息:
    pool.join()
    File "/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/multiprocessing/pool.py", line 545, in join
    assert self._state in (CLOSE, TERMINATE)
    AssertionError
    解决方法: join 之前 必须先把  pool.close() 关闭掉.
    """
    pool.join()







