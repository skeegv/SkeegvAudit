import os
import sys
import django
from audit.backend import user_interactive


if __name__ == "__main__":
    # 1.set path Django.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SkeegvAudit.settings")
    # 2.手动注册 Django 所有 app
    django.setup()
    obj = user_interactive.UserShell(sys.argv)
    obj.start()





