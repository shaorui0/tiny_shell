import os
import sys
import time
import signal

from log import with_log
from jobs import Jobs


EXEC_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exec_file')
jobs = Jobs()

@with_log
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
                
                self.log.info('parse a cmd: {}'.format(command_line))
                is_normal_command, argvs = self._parse_cmd(command_line)
                if is_normal_command is False:
                    if command_line == '':
                        sys.stdout.write('\n')
                        sys.stdout.flush()
                    continue

                if not self._is_builtin_cmd(argvs):
                    is_backend = False
                    if argvs[len(argvs) - 1] == '&':
                        is_backend = True
                        argvs = argvs[:-1]

                    self.log.info('create a new process...')
                    newpid = os.fork()
                    newenv = os.environ.copy() # must get it from parent process

                    # block sigchld
                    signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGCHLD])
                    if newpid == 0:
                        # unblock sigchld in child process
                        signal.pthread_sigmask(signal.SIG_UNBLOCK, [signal.SIGCHLD])

                        os.setpgid(0, 0) # 单独成组，用于kill
                        try:
                            os.execve(os.path.join(EXEC_FILE_PATH, argvs[0]), argvs, newenv)
                        except OSError:
                            self.log.error('no such exec file.')
                            os._exit(0)

                    signal.pthread_sigmask(signal.SIG_BLOCK, range(1, signal.NSIG))
                    jobs.new_job(newpid, cmd=command_line)
                    signal.pthread_sigmask(signal.SIG_UNBLOCK, range(1, signal.NSIG))

                    if is_backend is False:
                        jobs.set_frontend_process(newpid)

                        while jobs.get_frontend_process():
                            time.sleep(1) # trivial, use `sigsuspend();` in c language.

                        self.log.info("[FRONTEND] parent: %d, child: %d" % (os.getpid(), newpid))
                    else:
                        self.log.info("[BACKEND] parent: %d, child: %d, run: %s" % (os.getpid(), newpid, " ".join(argvs)))

                    # unblock sigchld in parent process
                    signal.pthread_sigmask(signal.SIG_UNBLOCK, [signal.SIGCHLD])
                else:
                    self._run_builtin_cmd(argvs)
            except EOFError:
                self._ignore_the_cmd()
            except OSError as e:
                self.log.error(e)
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
        if cmd == '\n' or cmd == '':
            return False, False
        argvs = cmd.rstrip('\n').rstrip('').split(' ')
        return True, argvs

    def _is_builtin_cmd(self, argvs):
        """
        Params:
            argvs(list): check argv is builtin command
        """
        if argvs[0] in [
            'quit', 
            #'sleep', # builtin_cmd cannot catch SIGSTOP signal
            'jobs', 
            'bg', 
            'fg', 
            'getgpid'
        ]:
            return True
        return False

    def _run_builtin_cmd(self, argvs):
        """
        Params:
            argvs(list): run builtin command
        """
        self.log.info('running builtin command.')
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
            if len(argvs) != 2:
                self.log.error('USAGE: bg [pid].')
            elif int(argvs[1]) not in jobs.total_job_map.keys():
                self.log.error('no such job!')
            else:
                self.log.info('[bg] pid = %s' % (argvs))
                signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGCHLD])

                signal.signal(signal.SIGCONT, signal.SIG_DFL)
                os.kill(int(argvs[1]), signal.SIGCONT)

                signal.pthread_sigmask(signal.SIG_UNBLOCK, [signal.SIGCHLD])

        elif argvs[0] == 'fg':
            # TODO
            if len(argvs) != 2:
                self.log.error('USAGE: fg [pid].')
            elif int(argvs[1]) not in jobs.total_job_map.keys():
                self.log.error('no such job.')
            else:
                self.log.info('[fg] pid = %s' % (argvs))

                signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGCHLD])

                signal.signal(signal.SIGCONT, signal.SIG_DFL)
                os.kill(int(argvs[1]), signal.SIGCONT)

                jobs.set_frontend_process(int(argvs[1]))
                while jobs.get_frontend_process():
                    time.sleep(1)
                
                signal.pthread_sigmask(signal.SIG_UNBLOCK, [signal.SIGCHLD])

        elif argvs[0] == 'getgpid':
            if len(argvs) != 1:
                self.log.error('USAGE: getgpid. No other parameters.')
            else:
                sys.stdout.write(os.getpgid(int(argvs[1])))
                sys.stdout.flush()
        
        else:
            return

    def _sleep(self, seconds):
        """
        Params:
            seconds(int): sleep command
        """
        for i in range(seconds):
            self.log.info("sleep {}...".format(i))
            time.sleep(1)
        return

    def signal_terminal_handler(self, sig, frame):
        self.log.info('will handle terminal signal')
        if jobs.is_frontend_process(0):
            self.log.info('shell has terminated, {}'.format(str(os.getpid())))
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            os.kill(os.getpid(), signal.SIGINT) # 为什么无法退出？说找不到process？
        else:
            self.log.info('child has terminated, {}'.format(str(os.getpid())))
            os.kill(jobs.get_frontend_process(), signal.SIGINT)

    def signal_stop_handler(self, sig, frame):
        self.log.info('will handle stop signal')
        if jobs.is_frontend_process(0):
            self.log.info('shell has stopped, {}'.format(str(os.getpid())))
            signal.signal(signal.SIGTSTP, signal.SIG_DFL)
            os.kill(os.getpid(), signal.SIGTSTP)
        else:
            self.log.info('child has stopped, {}'.format(str(os.getpid())))
            os.kill(jobs.get_frontend_process(), signal.SIGTSTP)

    def signal_child_handler(self, sig, frame):
        self.log.info('[signal_child_handler] entry signal_child_handler')
        while True:
            pid, status = os.waitpid(-1, os.WNOHANG|os.WUNTRACED|os.WCONTINUED)
            if pid <= 0:
                break

            self.log.info('[signal_child_handler] current pid = {}, status = {}\n'.format(pid, status))

            # normally exit
            if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                signal.pthread_sigmask(signal.SIG_BLOCK, range(1, signal.NSIG))
                if jobs.is_frontend_process(pid):
                    jobs.set_frontend_process(0)

                jobs.del_job_by_pid(pid)
                sys.stdout.write('process [{}] terminated.'.format(pid))
                sys.stdout.flush()
                signal.pthread_sigmask(signal.SIG_UNBLOCK, range(1, signal.NSIG))


            # SIGTSTP
            if os.WIFSTOPPED(status):
                signal.pthread_sigmask(signal.SIG_BLOCK, range(1, signal.NSIG))
                
                if jobs.is_frontend_process(pid):
                    jobs.set_frontend_process(0)

                jobs.update_job_status(pid, jobs.STOPPED)
                sys.stdout.write('process [{}] stopped.'.format(pid))
                sys.stdout.flush()

                signal.pthread_sigmask(signal.SIG_UNBLOCK, range(1, signal.NSIG))

            # sigcont
            if os.WIFCONTINUED(status):
                signal.pthread_sigmask(signal.SIG_BLOCK, range(1, signal.NSIG))
                jobs.update_job_status(pid, jobs.RUNNING)
                signal.pthread_sigmask(signal.SIG_UNBLOCK, range(1, signal.NSIG))
