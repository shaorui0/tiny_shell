import os
import sys
import time
import signal

from jobs import Jobs


jobs = Jobs()

class Shell():
    def __init__(self):
        signal.signal(signal.SIGINT, self.signal_terminal_handler)
        signal.signal(signal.SIGTSTP, self.signal_stop_handler)
        signal.signal(signal.SIGCHLD, self.signal_child_handler)
        print(self.__class__.__module__ + '.' + self.__class__.__name__)

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
                        # TODO 如果不是个正常的命令，直接退出就行了，也不用更新jobs

                        try:
                            os.execve('../exec_file/' + argvs[0], argvs, newenv)
                        except OSError:
                            print('**********')
                            #print('stat={}'.format(stat))
                            os._exit(0) # 或者直接在这里？退出时进行一次处理？退出以后，run之前
                    
                    # parent process
                    # add job to jobs
                    jobs.new_job(newpid, cmd=command_line)
                    if is_backend is False:
                        jobs.set_frontend_process(newpid)
                        print('>>> frontend process: ',  newpid)
                        # TODO 需要阻塞在这里，suspend
                        # 什么意思？前台不为0，阻塞
                        # 前台为0，表示退出（stop/terminate）了进程

                        # run frontend process
                        while jobs.get_frontend_process():
                            #sigsuspend(&prev_one);
                            time.sleep(1)

                        #jobs.update_job_status(newpid, 'terminated')
                        jobs.print_jobs()
                        print("[FRONTEND] parent: %d, child: %d" % (os.getpid(), newpid))
                    else:
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
        if argvs[0] in ['quit', 'sleep', 'jobs', 'bg', 'fg', 'getgpid']:
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
        elif argvs[0] == 'bg':
            # TODO
            if len(argvs) != 2:
                print('no such job')
            elif int(argvs[1]) not in jobs.total_job_map.keys():
                print('no such job!')
            else:
                print('[bg]\n')
                signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGCHLD])

                signal.signal(signal.SIGCONT, signal.SIG_DFL)
                os.kill(int(argvs[1]), signal.SIGCONT) # 继续执行

                signal.pthread_sigmask(signal.SIG_UNBLOCK, [signal.SIGCHLD])

        elif argvs[0] == 'fg':
            # TODO
            if len(argvs) != 2:
                print('no such job')
            elif int(argvs[1]) not in jobs.total_job_map.keys():
                print('no such job!')
            else:
                print('[fg]\n{}\n'.format(str(argvs)))
                signal.signal(signal.SIGCONT, signal.SIG_DFL)
                os.kill(int(argvs[1]), signal.SIGCONT) # 继续执行
                jobs.set_frontend_process(int(argvs[1]))
                # 这里就直接执行了，但是后面还是有问题
                while jobs.get_frontend_process(): # 这里是为了避免空转，但也不够精确
                    time.sleep(1)
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
        print('[signal_child_handler] entry signal_child_handler')
        while True:
            pid, status = os.waitpid(-1, os.WNOHANG|os.WUNTRACED|os.WCONTINUED)
            if pid <= 0:
                break
            print('[signal_child_handler] current pid = {}, status = {}\n'.format(pid, status))
            # TODO lock

            # if terminate signal, normally exit
            if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                # reap child process ==> while, reap as much as passible
                # if fg process
                if jobs.is_fg_process(pid):
                    jobs.set_frontend_process(0)
                
                sys.stdout.write('process [{}] terminated.'.format(pid))
                sys.stdout.flush()

                # else parent process
                #jobs.update_job_status(pid, 'terminated')
                # delete job info in jobs 

                # # TODO lock of signal
                jobs.del_job_by_pid(pid)


            # if stop signal
            if os.WIFSTOPPED(status):
                if jobs.is_fg_process(pid):
                    jobs.set_frontend_process(0)
                #JobPtr jp = find_job_by_pid(pid);

                # # TODO lock of signal
                # set job status stopped
                jobs.update_job_status(pid, 'Stopped')
                sys.stdout.write('process [{}] stopped.'.format(pid))
                sys.stdout.flush()

                # 如何在将来得以重新执行起来？

            # TODO sigcontinue
            # 如何通过bg or fg触发这个信号？
            if os.WIFCONTINUED(status):
                print('[continue]')
                # TODO check bg or fg? or only support fg?
                signal.pthread_sigmask(signal.SIG_BLOCK, range(1, signal.NSIG))
                jobs.update_job_status(pid, 'Running')
                signal.pthread_sigmask(signal.SIG_UNBLOCK, range(1, signal.NSIG))

            # TODO if bg / fg，continue
            print('[signal_child_handler] signal_child_handler over!\n')
shell = Shell()
shell.loop()