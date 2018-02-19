# -*- coding: utf-8 -*-
import os
import sys
import json
import paramiko
import multiprocessing  # multiprocessing 是 python 的多进程并行库，可以使用进程池 multiprocessing.pool 来自动管理进程任务。


# 批量执行命令
def cmd_run(tasklog_obj,task_id,task_content):
    # task_content 是 要执行的命令
    try:
        bind_host_obj = tasklog_obj.host_user_bind

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

        stdin, stdout, stderr = ssh.exec_command(task_content)

        result = stdout.read() + stderr.read()

        # 如果没有返回值
        if len(result) > 0:
            result = result.decode('utf8')
            tasklog_obj.result = result
        else:
            tasklog_obj.result = 'cmd has no result.'

        ssh.close()
        tasklog_obj.status = 0
        tasklog_obj.save()
    except Exception as e:
        tasklog_obj.status = 1
        tasklog_obj.result = str(e)
        tasklog_obj.save()


# 批量文件
def file_transfer(tasklog_obj,task_id, task_content):
    # task.content: {"task_type":"file_transfer","selected_host_ids":["5","6"],"file_transfer_type":"send","random_str":"6b2qj3r9","remote_path":"/etc/"}
    try:
        account_id = tasklog_obj.task.account.id
        # 主机对象
        bind_host_obj = tasklog_obj.host_user_bind

        task_data = json.loads(task_content)

        # 连接主机 并 向远程主机发送文件
        t = paramiko.Transport((tasklog_obj.host_user_bind.host.ip_addr, tasklog_obj.host_user_bind.host.port))
        t.connect(
            username=tasklog_obj.host_user_bind.host_user.username,
            password=tasklog_obj.host_user_bind.host_user.password)
        sftp = paramiko.SFTPClient.from_transport(t)

        # 发送文件
        send_file_list = []
        if task_data.get('file_transfer_type') == "send":
            local_path = "%s/%s/%s/" % (settings.FILE_UPLOADS,
                                        account_id,
                                        task_data.get('random_str'))

            upload_file_count = 0
            # 列出本地存放文件的路径下的所有文件并发送
            for file_name in os.listdir(local_path):
                sftp.put('%s/%s' % (local_path, file_name), '%s/%s' % (task_data.get('remote_path'), file_name))

                result = 'Sent from : %s/%s' % (local_path, file_name), 'here to : %s/%s' % (
                task_data.get('remote_path'), file_name)
                send_file_list.append(result)
                upload_file_count += 1

            upload_file_count = "上传文件总数: %s" % upload_file_count
            send_file_list.insert(0, upload_file_count)

        else:
            # 下载本机器上的指定目录下载文件(下载到堡垒机)(这里已经是独立一个进程了,也就是在单台机器上)

            # 创建Task 表的时候,既以 Task id 为文件名的下载目录,这样会更高效(不然的话,之后比如执行1W次任务,每次创建都需要判断这个文件在不在才能执行操作,在这里创建了,以后所有任务要下载直接使用就可以,无需再做额外的判断)
            download_dir = "{download_base_dir}/{task_id}".format(download_base_dir=settings.FILE_DOWNLOADS,
                                                                  task_id=task_id)
            # 从远程路径取到远程的文件名 .os.path.basename(path); 返回path最后的文件名
            remote_filename = os.path.basename(task_data.get('remote_path'))

            # 拼接 本地存放文件格式
            local_path = "%s/%s.%s" % (download_dir,
                                       tasklog_obj.host_user_bind.host.ip_addr,
                                       remote_filename)
            # 从远程下载到本地
            sftp.get(task_data.get('remote_path'), local_path)

            result = 'Get from : ', task_data.get('remote_path'), 'here to : ', local_path
            send_file_list.append(result)

        # 关闭连接
        t.close()

        tasklog_obj.result = send_file_list
        tasklog_obj.status = 0
        tasklog_obj.save()
    except Exception as e:
        tasklog_obj.status = 1
        tasklog_obj.result = str(e)
        tasklog_obj.save()


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

    # 创建进程池(multiprocessing包是Python中的多进程管理包)
    pool = multiprocessing.Pool(
        processes=settings.MaxTaskProcesses)  # Pool类用于需要执行的目标很多，而手动限制进程数量又太繁琐时，如果目标少且不用控制进程数量则可以用Process类。

    if task_obj.task_type == 0:  # 0: cmd ; 1:file_transfer
        task_func = cmd_run
    else:
        task_func = file_transfer

    # task_obj.tasklog_set.all() 是取 task表里的 id 并反向关联到 tasklog 表里,取跟这个 task id 一样的主机信息.
    for tasklog_obj in task_obj.tasklog_set.all():
        # 进程池
        pool.apply_async(task_func, args=(tasklog_obj,task_id, task_obj.content))
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
