#!/bin/bash

# for loop 30.get process id by  random tag,
# if got the process id , start strace command!

for i in $(seq 1 30);do
    process_id=`ps -ef|grep $1|egrep -v "sshpass|grep|session_tracker.sh"|awk '{print $2}'`
    echo "process:$process_id"
    if [ ! -z "$process_id" ];then
         echo 'start run strace...'
         #  logs/ 目录需要我们在 home/audit/下创建
         sudo strace -ftp $process_id -o logs/ssh_audit_$2.log;
         break;
    fi
    sleep 1
done;

