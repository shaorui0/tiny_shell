import os
import sys
import time

def child():
   print('\nA new child ',  os.getpid())
   os._exit(0)  


def echo(line):
    if line == '\n':
        return
    sys.stdout.write(line)
    sys.stdout.flush()
    return

def task():
    pass

def handle_eof_signal():
    # 这里最好能获取到信号
    print()
    cmdline = '\n'

def parse_cmd(cmd):
    """
    Args:
        cmd(string)
    Return:
        args(list): cmd(argv[0]) + args
    """
    # TODO must more complicate
    argvs = cmd.rstrip('\n').rstrip('').split(' ')
    return argvs

def is_builtin_cmd(argvs):
    """
    """
    if argvs[0] in ['quit', 'echo', 'sleep']:
        return True
    return False
    
def _sleep(run_time):
    for i in range(run_time):
        print("sleep {}...".format(i))
        time.sleep(1)
    return

while True:
    cmdline = str()
    try:
        sys.stdout.write('tsh > ')
        sys.stdout.flush()
        #cmdline = str(sys.stdin.readline())
        #cmdline = input("Enter a book cmdline: ")
        cmdline = input() + '\n' # read a line
        print('parse a cmd: {}'.format(cmdline))
        argvs = parse_cmd(cmdline)
        is_backend = False
        # if command is builtin cmd:
        if not is_builtin_cmd(argvs):
            # run exec file
            # check backend
            index = argvs[len(argvs) - 1]
            if index == '&':
                print('Current child process should run in backend.')
                is_backend = True
            
            # create a child process
            print('create a new process...')
            newpid = os.fork()
            if newpid == 0:
                # 子进程执行一些业务逻辑
                _sleep(100)
                print('A new child ',  os.getpid())
                # test sleep and test zombee
                # run something
                os._exit(0) # 执行完退出
            #import pdb; pdb.set_trace() # 直接运行的时候就能使用pdb
            if is_backend is False:
                # 前台执行，也就是等待子程序终止
                # TODO check ruturn, at lease return a pid...(, ) ???
                os.waitpid(-1, 0) # parent wait，这个则是完全不等，直接返回，执行后台时更方便
                print("[FRONTEND] parent: %d, child: %d" % (os.getpid(), newpid))
            else:
                # 不等了，直接返回，那么谁来回收？
                # os.WNOHANG == -1
                os.waitpid(-1, os.WNOHANG) # parent wait，这个则是完全不等，直接返回，执行后台时更方便
                print("[BACKEND] parent: %d, child: %d, run: %s" % (os.getpid(), newpid, " ".join(argvs)))
                # check waitpid. may be error
        else:
            # 内置命令
            if argvs[0] == 'quit':
                os._exit(0)
            if argvs[0] == 'echo':
                echo(' '.join(argvs[1:]))
    except EOFError as e:
        handle_eof_signal()
    finally:
        # 业务逻辑
        #print('finally >>>')
        #echo(cmdline)
        pass

#现在需要拆解一下了