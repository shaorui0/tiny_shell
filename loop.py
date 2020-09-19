import os
import sys
import time

class Shell():
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
                        print('A new child ',  os.getpid())
                        os.execve(argvs[0], argvs, newenv)
                        os._exit(0)
                    if is_backend is False:
                        os.waitpid(-1, 0)
                        print("[FRONTEND] parent: %d, child: %d" % (os.getpid(), newpid))
                    else:
                        os.waitpid(-1, os.WNOHANG)
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
                self._sleep(argvs[1])
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




shell = Shell()
shell.loop()