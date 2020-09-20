import os
import sys
import time
import signal


class Jobs():
    # 什么数据结构来管理？dict，目前先用dict
    frontend_pid = int() # 前台进程pid
    total_job_map = dict() # 所有进程信息
    # pid => {
    #   status
    #   cmd
    # }
    
    # 重载一个getattr，避免获取没有存进来的process
    # TODO 枚举，三种状态：running、stopped、terminated
    #def __getattr__(self, key):
        # diff __get__
    #    pass


    def get_current_jobs(self):
        for pid, process_info in self.total_job_map.iters():
            print("[{status}] {pid}".format({
                'status': process_info['status'],
                'pid': pid
            }))

        
    def get_process(self, pid):
        return os.getpid(pid)

    def append_process(self, pid, status=None, cmd=None):
        self.total_job_map.update({
            pid: {
            'status': 'running',
            'cmd': cmd,
            }
        })
        print(self.total_job_map)
        print('>>> running a child process', pid)

    # status怎么更新状态？也就是waitpid的返回值，返回pid表示当前进程终止，返回0表示什么，返回-1表示什么？
    def update_status(self, pid, status):
        print(self.total_job_map)
        self.total_job_map[pid]['status'] = status
        print('>>> status of child process has changed:', pid, status)

    def set_frontend_pid(self, pid):
        self.frontend_pid = pid

class Shell():
    def __init__(self):
        signal.signal(signal.SIGINT, self.signal_terminal_handler)
        signal.signal(signal.SIGTSTP, self.signal_stop_handler)
        self.jobs = Jobs()

    def loop(self):
        """main loop
        """
        while True:
            command_line = str()
            try:
                sys.stdout.write('tsh > ')
                sys.stdout.flush()
                command_line = sys.stdin.readline()
                
                print('parse a cmd: {}'.format(command_line))
                is_normal_command, argvs = self._parse_cmd(command_line)
                if is_normal_command is False:
                    continue

                if not self._is_builtin_cmd(argvs):
                    is_backend = False
                    if argvs[len(argvs) - 1] == '&':
                        is_backend = True
                        argvs = argvs[:-1]

                    print('create a new process...')
                    newpid = os.fork()
                    newenv = os.environ.copy() # must get it from parent process

                    if newpid == 0:
                        # 业务逻辑
                        #print('A new child ',  os.getpid())
                        #print('》》',  os.getpid())
                        # running
                        self.jobs.append_process(os.getpid(), command_line)
                        os.execve(argvs[0], argvs, newenv) 
                        os._exit(0) # 或者直接在这里？退出时进行一次处理？退出以后，run之前
                    if is_backend is False:
                        #self.jobs.frontend_pid = newpid # 会不会有并发的问题？启动一个前台的时候可能是在等待的
                        self.jobs.set_frontend_pid(newpid)
                        print('>>> frontend process: ',  newpid)
                        os.waitpid(-1, 0)
                        # terminated 
                        #self.jobs.update_status(newpid, 'terminated')
                        print('》》》》》 ',  self.jobs.total_job_map)
                        print("[FRONTEND] parent: %d, child: %d" % (os.getpid(), newpid))
                    else:
                        os.waitpid(-1, os.WNOHANG|os.WCONTINUED)
                        print("[BACKEND] parent: %d, child: %d, run: %s" % (os.getpid(), newpid, " ".join(argvs)))
                else:
                    self._run_builtin_cmd(argvs)
            except EOFError:
                self._ignore_the_cmd()
            except OSError as e:
                print(e)
                self._ignore_the_cmd()

    def _ignore_the_cmd(self):
        """
        _ignore_the_cmd
        """
        sys.stdout.write('\n')
        sys.stdout.flush()

    def _parse_cmd(self, cmd):
        """
        Params:
            cmd(string)
        Return:
            args(list): cmd(argv[0]) + args
        """
        # TODO must more complicate

        # if cmd is 'Enter' or ctrl-D
        if cmd == '\n' or cmd == '':
            return False, False
        argvs = cmd.rstrip('\n').rstrip('').split(' ')
        return True, argvs

    def _is_builtin_cmd(self, argvs):
        """
        Params:
            argvs(list): check argv is builtin command
        """
        if argvs[0] in ['quit', 'sleep']:
            return True
        return False

    def _run_builtin_cmd(self, argvs):
        """
        Params:
            argvs(list): run builtin command
        """
        print('running builtin command.')
        if argvs[0] == 'quit':
            os._exit(0)
        elif argvs[0] == 'sleep':
            if len(argvs) == 2:
                self._sleep(int(argvs[1]))
            else:
                raise Exception("sleep command length must be '2'.")
        else:
            return

    def _sleep(self, seconds):
        """
        Params:
            seconds(int): sleep command
        """
        for i in range(seconds):
            print("sleep {}...".format(i))
            time.sleep(1)
        return
    
    def signal_stop_handler(self, sig, frame):
        # kill
        # 如何挂起一个进程？保存这个进程的状态，之后再处理
        # 先挂起，后重新执行
        # 应该是对子进程起作用，不是对主进程。并且是当前的『前台程序』
        print('will stop a child process')

        print('will continue a child process')

    def signal_terminal_handler(self, sig, frame):
        print('signal_terminal_handler')
        # 通过进程id，获取到当前进程，同时分为1 + n-1，这里就涉及到job管理了
        if self.sub_process and hasattr(self.sub_process, 'pid'):
            os.kill(os.getpid(pid), signal.SIGTERM)
        #os._exit(0) # 我需要杀掉的是前台进程
        # 获取到前台进程，然后kill it
        # 应该是对子进程起作用，不是对主进程。并且是当前的前台程序


shell = Shell()
shell.loop()