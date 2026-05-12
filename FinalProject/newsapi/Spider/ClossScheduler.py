# -*- coding：utf-8 -*-
import os

def kill(pid):
    if os.name == 'nt':
        # Windows 环境下的处理
        cmd = 'taskkill /pid ' + str(pid) + ' /f'
        try:
            os.system('chcp 65001')
            os.system(cmd)
            
            # 💡 [新增核心逻辑]：强制静默杀掉所有残留的 chromedriver 进程，防止内存泄漏
            # 加上 2>nul 是为了防止在没有残留进程时终端输出丑陋的报错信息
            os.system('taskkill /im chromedriver.exe /f /t 2>nul')
            
            print(pid, 'killed and chromedriver cleaned')
        except Exception as e:
            print(e)
    elif os.name == 'posix':
        # Linux 环境下的处理
        cmd = 'kill ' + str(pid)
        try:
            os.system(cmd)
            # 💡 [新增核心逻辑]：Linux 下的僵尸进程清理
            os.system('pkill chromedriver')
            print(pid, 'killed and chromedriver cleaned')
        except Exception as e:
            print(e)
    else:
        print('Undefined os.name')


def getpidandkill(filename):
    f1 = open(file=filename + '.txt', mode='r')

    pid = f1.read()
    f1.close()

    # 调用kill函数，终止进程
    kill(pid=pid)
