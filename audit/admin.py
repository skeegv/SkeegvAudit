from django.contrib import admin
from audit import models


class AuditLogAdmin(admin.ModelAdmin):
    # 要显示的字段
    list_display = ['session', 'cmd', 'date']
    # 按哪一些字段来过滤
    list_filter = ['date', 'session']


class SessionLogAdmin(admin.ModelAdmin):
    # 要显示的字段
    list_display = ['id', 'account', 'host_user_bind', 'start_date', 'end_date']
    # 按哪一些字段来过滤
    list_filter = ['start_date', 'account']


class TaskLogAdmin(admin.ModelAdmin):
    list_display = ['task_id', 'host_user_bind', 'result', 'date']

    list_filter = ['result', ]


admin.site.register(models.Host)
admin.site.register(models.HostGroup)
admin.site.register(models.HostUser)
admin.site.register(models.HostUserBind)
admin.site.register(models.Account)
admin.site.register(models.IDC)
admin.site.register(models.AuditLog, AuditLogAdmin)
admin.site.register(models.SessionLog, SessionLogAdmin)
admin.site.register(models.Token)
admin.site.register(models.Task)
admin.site.register(models.TaskLog, TaskLogAdmin)
