import os
import sys
import time
import signal


class Jobs():
    # 什么数据结构来管理？dict，目前先用dict
    frontend_pid = 0 # 前台进程pid
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

    # 前台进程
    def is_fg_process(self, pid):
        return pid == self.frontend_pid

    def get_frontend_process(self):
        return self.frontend_pid
    
    def set_frontend_process(self, pid):
        print('set_frontend_process {}'.format(pid))
        self.frontend_pid = pid

    def get_total_running_jobs(self):
        for pid, process_info in self.total_job_map.iters():
            print("[{status}] {pid}".format({
                'status': process_info['status'],
                'pid': pid
            }))
    def print_jobs(self):
        """running/stopped/..
        """
        print(self.total_job_map)
        return

    def init_jobs():
        pass


    def del_job_by_pid(self, pid):
        print("del_job_by_pid")
        jobs.total_job_map[pid]['using'] = 0

    def get_job(self, pid):
        return os.getpid(pid)

    def new_job(self, pid, cmd=None):
        self.total_job_map.update({
            pid: {
            'status': 'running',
            'cmd': cmd,
            'using': 1,
            }
        })
        print('>>> running a child process', pid)
    
    # status怎么更新状态？也就是waitpid的返回值，返回pid表示当前进程终止，返回0表示什么，返回-1表示什么？
    def update_job_status(self, pid, status):
        print(self.total_job_map)
        self.total_job_map[pid]['status'] = status
        print('>>> status of child process has changed:', pid, status)


jobs = Jobs()

class Shell():
    def __init__(self):
        signal.signal(signal.SIGINT, self.signal_terminal_handler)
        signal.signal(signal.SIGTSTP, self.signal_stop_handler)
        signal.signal(signal.SIGCHLD, self.signal_child_handler)

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
                        # child process
                        # 业务逻辑

                        os.setpgid(0, 0) # 单独成组
                        #print('A new child ',  os.getpid())
                        #print('》》',  os.getpid())
                        # running
                        os.execve(argvs[0], argvs, newenv) 
                        #os._exit(0) # 或者直接在这里？退出时进行一次处理？退出以后，run之前
                    
                    # parent process
                    # add job to jobs
                    jobs.new_job(newpid, cmd=command_line)
                    if is_backend is False:
                        jobs.set_frontend_process(newpid)
                        print('>>> frontend process: ',  newpid)
                        # TODO 需要阻塞在这里，suspend
                        # 什么意思？前台不为0，阻塞
                        # 前台为0，表示退出（stop/terminate）了进程
                        while jobs.get_frontend_process():
                            import time
                            time.sleep(1)
                            #sigsuspend(&prev_one);
                        #os.waitpid(-1, 0)
                        # terminated 
                        #jobs.update_job_status(newpid, 'terminated')
                        print('>>>>> ',  jobs.total_job_map)
                        print("[FRONTEND] parent: %d, child: %d" % (os.getpid(), newpid))
                    else:
                        #os.waitpid(-1, os.WNOHANG|os.WCONTINUED)
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
        if argvs[0] in ['quit', 'sleep', 'jobs', 'getgpid']:
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
            if len(argvs) != 2:
                raise Exception("sleep command length must be '2'.")
            self._sleep(int(argvs[1]))
        elif argvs[0] == 'jobs':
            if len(argvs) != 1:
                raise Exception("sleep command length must be '1'.")
            jobs.print_jobs()
        elif argvs[0] == 'getgpid':
            # check len argvs
            print(os.getpgid(int(argvs[1])))
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

    def signal_terminal_handler(self, sig, frame):
        print('will handle terminal signal')
        # if it fg process
        if jobs.is_fg_process(0):# TODO 判断0，这里有问题，执行了一条命令以后，就不为0了，所以何时set为0很重要，这是处理sigchld时的任务
            print('shell has terminated, {}'.format(str(os.getpid())))
            # 设置为default
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            # kill shell
            os.kill(os.getpid(), signal.SIGINT) # 为什么无法退出？说找不到process？

            # stop it 
        else:
            print('child has terminated, {}'.format(str(os.getpid())))
            os.kill(jobs.get_frontend_process(), signal.SIGINT)

    def signal_stop_handler(self, sig, frame):
        # kill
        # 如何挂起一个进程？保存这个进程的状态，之后再处理
        # 先挂起，后重新执行
        # 应该是对子进程起作用，不是对主进程。并且是当前的『前台程序』
        print('will handle stop signal')
        # if it fg process
        if jobs.is_fg_process(0):
            print('shell has stopped, {}'.format(str(os.getpid())))
            # 设置为default
            signal.signal(signal.SIGTSTP, signal.SIG_DFL)
            # kill shell
            os.kill(os.getpid(), signal.SIGTSTP)
            # stop it 
        else:
            print('child has stopped, {}'.format(str(os.getpid())))
            os.kill(jobs.get_frontend_process(), signal.SIGTSTP)

    def signal_child_handler(self, sig, frame):
        # 这里的工作有很多了
        # how to check status? how to status?
        # waitpid?
        print('entry signal_child_handler')
        while True:
            pid, status = os.waitpid(-1, os.WNOHANG|os.WUNTRACED|os.WCONTINUED)
            if pid <= 0:
                break

            # TODO lock

            # if terminate signal, normally exit
            if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                sys.stdout.write('>>> process [{}] terminated.'.format(pid))
                sys.stdout.flush()
                # reap child process ==> while, reap as much as passible
                # if fg process
                if jobs.is_fg_process(pid):
                    jobs.set_frontend_process(0) # 表示已经执行完了
                else:
                    sys.stdout.write('process [{}] terminated.'.format(pid))
                    sys.stdout.flush()
                # else parent process
                #jobs.update_job_status(pid, 'terminated')
                # delete job info in jobs # TODO lock of signal
                jobs.del_job_by_pid(pid)


            # if stop signal
            if os.WIFSTOPPED(status):
                if jobs.is_fg_process(pid):
                    jobs.set_frontend_process(0)
                #JobPtr jp = find_job_by_pid(pid);
                jobs.update_job_status(pid, 'Stopped')
                sys.stdout.write('process [{}] stopped.'.format(pid))
                sys.stdout.flush()
                # set current fg process status
                # set fg process 0
                # 如何在将来得以重新执行起来？
                # print stopped
            # TODO sigcontinue
            
            # TODO if bg / fg，continue
shell = Shell()
shell.loop()