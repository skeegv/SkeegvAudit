import paramiko

try:
    # 建立ssh连接 使用密码连接：
    ssh = paramiko.SSHClient()
    # 这行代码的作用是允许连接不在know_hosts文件中的主机。就是自动填写 yes
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # timeout 设置超时时间
    ssh.connect('39.108.141.220',
                22,
                'root',
                '123345',
                timeout=15)

    stdin, stdout, stderr = ssh.exec_command('df')

    result = stdout.read() + stderr.read()

    ssh.close()
except Exception as e:
    print('error: ', e)
