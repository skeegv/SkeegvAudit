import os
import json  # Json简介：Json，全名 JavaScript Object Notation，是一种轻量级的数据交换格式。
from audit import models
import subprocess  # subprocess模块允许我们创建子进程,连接他们的输入/输出/错误管道，还有获得返回值。
from threading import Thread  # 操作线程的模块(Thread 是threading模块中最重要的类之一，可以使用它来创建线程)
# from SkeegvAudit import settings
from django.conf import settings
from django.db.transaction import atomic  # 数据库事务(atomic块中必须注意try的使用，如果手动捕获了程序错误会导致atomic包装器捕获不到异常，也就不会回滚。要么try内代码不影响事务操作，要么就捕获异常后raise出，让atomic可以正常回滚)


class Task(object):
    """处理批量任务,包括命令和文件传输"""

    def __init__(self, request):
        self.request = request
        self.errors = []
        self.task_data = None

    def is_valid(self):
        """
        1.数据清洗
        2.验证命令,主机列表合法性
        :return:
        """
        # 获取 task_data 里的数据
        task_data = self.request.POST.get('task_data')

        # 判断 task_data 是否有数据
        if task_data:
            # 对task_data 进行反序列化
            self.task_data = json.loads(task_data)
            """
            前后端都需要验证,前端验证只是为了减轻 Server 端的压力,
            后端验证是为了验证数据是否合法,用户可能会直接 Post请求过来.
            
            // 前端提交到后台的数据格式
            var task_data = {
                'task_type': task_type,
                'selected_host_ids': selected_host_ids, #hsot_user_binds(用户和主机)
                'cmd': cmd_text # 或 file_transfer = 文件
            };
            """
            print(task_data)
            # 验证文件类型是否有值
            if self.task_data.get('task_type') == 'cmd':
                if self.task_data.get('cmd') and self.task_data.get('selected_host_ids'):
                    return True
                self.errors.append({'invalid_argument': 'cmd or host_list is empty!'})
            elif self.task_data.get('task_type') == "file_transfer":
                #{"task_type":"file_transfer","selected_host_ids":["5","6"],"file_transfer_type":"send","random_str":"6b2qj3r9","remote_path":"/etc/"}
                if self.task_data.get('task_type') and self.task_data.get('selected_host_ids'):
                    print(task_data)
                    # [{"invalid_argument": "file or host_list is empty!"}, {"invalid_data": "task_data is not exist"}]
                    return True
                self.errors.append({'invalid_argument': 'file or host_list is empty!'})
            else:
                self.errors.append({'invalid_argument': 'task_type is invalid!'})
        self.errors.append({'invalid_data': 'task_data is not exist'})

    def run(self):
        """
        start task,and return task id
        :return: task_id
        """
        # 反射
        task_func = getattr(self, self.task_data.get('task_type'))
        task_id = task_func()

        return task_id

    @atomic  # 在需要进行事务处理的加上 @atomic 装饰器(原子性)
    def cmd(self):
        """批量任务"""

        task_obj = models.Task.objects.create(
            # task_type=self.task_data.get('task_type'),  0对应数据库里 task_choices 的 cmd
            task_type=0,
            account=self.request.user.account,
            content=self.task_data.get('cmd'),
        )


        # 主机会重复,所以要去重 (Python set() 函数Python 内置函数描述set() 函数创建一个无序不重复元素集，可进行关系测试，删除重复数据，还可以计算交集、差集、并集等。)
        host_ids = set(self.task_data.get("selected_host_ids"))

        tasklog_objs = []

        for host_id in host_ids:
            tasklog_objs.append(
                models.TaskLog(task_id=task_obj.id,
                               host_user_bind_id=host_id,
                               status=3)
            )

        """
        由于TaskLog.objects.create()每保存一条就执行一次SQL，而bulk_create()是执行一条SQL存入多条数据，做会快很多！
        当然用列表解析代替 for 循环会更快！！
        """
        models.TaskLog.objects.bulk_create(tasklog_objs, 100)

        # 执行任务
        """
        # 完全独立的进程(脚本)

        subprocess 模块中基本的进程创建和管理由Popen 类来处理.
        subprocess.popen是用来替代os.popen的.
        shell=True (默认是 false)在 unix 下想让与 args 前面添加了 /bin/sh
        PIPE 创建管道
        stdin 输入
        stdout 输出
        stderr 错误信息
        args 字符串或者列表
    
        """

        multitask_obj = subprocess.Popen('python3 %s %s' % (settings.MULTI_TASK_SCRIPT, task_obj.id), shell=True)


        # 返回任务 id 给前端
        return task_obj.id


    @atomic  # 在需要进行事务处理的加上 @atomic 装饰器(原子性)
    def file_transfer(self):
        """批量文件"""
        # task_data: {"task_type":"file_transfer","selected_host_ids":["5","6"],"file_transfer_type":"send","random_str":"6b2qj3r9","remote_path":"/etc/"}

        # 创建 任务记录
        task_obj = models.Task.objects.create(
            # task_type=self.task_data.get('task_type'),  0对应数据库里 task_choices 的 cmd
            task_type=1,    # 1: file_transfer
            account=self.request.user.account,
            content=json.dumps(self.task_data), # 这里直接把前端发来的 data 序列化并写入数据库:{"task_type": "file_transfer", "selected_host_ids": ["1", "2", "3", "4", "5"], "file_transfer_type": "send", "random_str": "4uqv379n"}
        )

        # 主机会重复,所以要去重 (Python set() 函数Python 内置函数描述set() 函数创建一个无序不重复元素集，可进行关系测试，删除重复数据，还可以计算交集、差集、并集等。)
        host_ids = set(self.task_data.get("selected_host_ids"))

        tasklog_objs = []

        # 通过前端发来的主机 id列表,取到每一台主机
        for host_id in host_ids:
            tasklog_objs.append(
                models.TaskLog(task_id=task_obj.id,
                               host_user_bind_id=host_id,
                               status=3)
            )

        """
        由于TaskLog.objects.create()每保存一条就执行一次SQL，而bulk_create()是执行一条SQL存入多条数据，做会快很多！
        当然用列表解析代替 for 循环会更快！！
        """
        models.TaskLog.objects.bulk_create(tasklog_objs, 100)

        # 创建以 Task id 为文件名的下载目录,这样会更高效(不然的话,之后比如执行1W次任务,每次创建都需要判断这个文件在不在才能执行操作,在这里创建了,以后所有任务要下载直接使用就可以,无需再做额外的判断)
        download_dir = "{download_base_dir}/{task_id}".format(download_base_dir=settings.FILE_DOWNLOADS,
                                                              task_id=task_obj.id)
        if not os.path.exists(download_dir):    #  检查某个路径
            os.makedirs(download_dir, exist_ok=True)    # 该参数为真时执行mkdir -p(加上此选项后,系统将自动建立好那些尚不存在的目录,即一次可以建立多个目录;)


        # 执行任务
        """
        # 完全独立的进程(脚本)

        subprocess 模块中基本的进程创建和管理由Popen 类来处理.
        subprocess.popen是用来替代os.popen的.
        shell=True (默认是 false)在 unix 下想让与 args 前面添加了 /bin/sh
        PIPE 创建管道
        stdin 输入
        stdout 输出
        stderr 错误信息
        args 字符串或者列表

        """

        multitask_obj = subprocess.Popen('python3 %s %s' % (settings.MULTI_TASK_SCRIPT, task_obj.id), shell=True)

        # 返回任务 id 给前端
        return task_obj.id
