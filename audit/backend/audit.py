import re


class AuditLogHandler(object):
    '''分析audit log日志'''

    def __init__(self, log_file):
        self.log_file_obj = self._get_file(log_file)

    def _get_file(self, log_file):
        """打开文件"""
        return open(log_file)

    def parse(self):
        cmd_list = []
        cmd_str = ''
        catch_write5_flag = False #for tab complication
        for line in self.log_file_obj:
            #print(line.split())
            line = line.split()
            try:
                # 默认按空格区分,只拿0:4
                pid, time_clock, io_call, char = line[0:4]
                # 以 read(4 开头
                if io_call.startswith('read(4'):
                    if char == '"\\177",':#回退 就是键盘上的删除按一次
                        char = '[1<-del]'
                    if char == '"\\33OB",': #vim中下箭头
                        char = '[down 1]'
                    if char == '"\\33OA",': #vim中下箭头
                        char = '[up 1]'
                    if char == '"\\33OC",': #vim中右移
                        char = '[->1]'
                    if char == '"\\33OD",': #vim中左移
                        char = '[1<-]'
                    if char == '"\33[2;2R",': #进入vim模式(不同的系统不一样)
                        continue
                    if char == '"\\33[>1;95;0c",':  # 进入vim模式
                        char = '[----enter vim mode-----]'


                    if char == '"\\33[A",': #命令行向上箭头
                        char = '[up 1]'
                        catch_write5_flag = True #取到向上按键拿到的历史命令
                    if char == '"\\33[B",':  # 命令行向上箭头
                        char = '[down 1]'
                        catch_write5_flag = True  # 取到向下按键拿到的历史命令
                    if char == '"\\33[C",':  # 命令行向右移动1位
                        char = '[->1]'
                    if char == '"\\33[D",':  # 命令行向左移动1位
                        char = '[1<-]'

                    # 把所有的命令字符加起来
                    cmd_str += char.strip('"",')

                    # 直到碰到 \\r 再把命令添加到 cmd_list 列表中
                    if char == '"\\t",':
                        catch_write5_flag = True
                        continue
                    if char == '"\\r",':
                        cmd_list.append([time_clock, cmd_str])
                        cmd_str = ''  # 重置
                    if char == '"':#space
                        cmd_str += ' '

                if catch_write5_flag: #to catch tab completion
                    if io_call.startswith('write(5'):
                        if io_call == '"\7",': #空键，不是空格，是回退不了就是这个键
                            pass
                        else:
                            cmd_str += char.strip('"",')
                        catch_write5_flag = False
            except ValueError as e:
                print("\033[031;1mSession log record err,please contact your IT admin,\033[0m",e)

        #print(cmd_list)
        for cmd in cmd_list:
            print(cmd)
        return cmd_list


if __name__ == "__main__":
    #  日志路径
    parser = AuditLogHandler('/home/audit/logs/ssh_audit_15.log')
    parser.parse()
