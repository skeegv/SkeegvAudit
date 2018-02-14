import json
from audit import models


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
        task_data = self.request.POST.get('task_data')
        if task_data:
            self.task_data = json.loads(task_data)
            """
            前后端都需要验证,前端验证只是为了减轻 Server 端的压力,
            后端验证是为了验证数据是否合法,用户可能会直接 Post请求过来.
            
            // 前端提交到后台的数据格式
            var task_data = {
                'task_type': task_type,
                'selected_host_ids': selected_host_ids, #hsot_user_binds(用户和主机)
                'cmd': cmd_text
            };
            """

            # 判断文件类型
            if self.task_data.get('task_type') == 'cmd':
                if self.task_data.get('cmd') and self.task_data.get('selected_host_ids'):
                    return True
                self.errors.append({'invalid_argument': 'cmd or host_list is empty!'})
            elif self.task_data.get('task_type') == "file_transfer":
                self.errors.append({'invalid_argument': 'cmd or host_list is empty!'})
            else:
                self.errors.append({'invalid_argument': 'task_type is invalid!'})
        self.errors.append({'invalid_data': 'task_data is not exist'})

    def run(self):
        """
        start task,and return task id
        :return: task_id
        """
        # 反射
        task_func = getattr(self,self.task_data.get('task_type'))
        res = task_func()

        return "task_id"

    def cmd(self):
        """批量任务"""
        print('run multi cmd')
        """
        # 数据库表
        class Task(models.Model):
            task_type_choices = ((0, 'cmd'), (1, 'file_transfer'))
            task_type = models.SmallIntegerField(choices=task_type_choices)
            host_user_binds = models.ManyToManyField("HostUserBind")
            content = models.TextField("任务内容")
            timeout = models.IntegerField("任务超时时间(s)", default=300)
            account = models.ForeignKey("Account")
            date = models.DateTimeField(auto_now_add=True)
        """

        task_obj = models.Task.objects.create(
            # task_type=self.task_data.get('task_type'),  0对应数据库里 task_choices 的 cmd
            task_type=0,
            account=self.request.user.account,
            content=self.task_data.get('cmd'),
            #host_user_binds=多对多需要直接对象添加
        )
        #task_obj.host_user_binds.add(1,2,3) 原本是这样传进去,
        # 但是我们前端返回的是一个列表,所以这里要加一个 *
        task_obj.host_user_binds.add(*self.task_data.get('selected_host_ids'))

        # 保存obj时要调用obj.save().
        task_obj.save()

    def file_transfer(self):
        """批量任务"""
        print('run multi file_transfer')
