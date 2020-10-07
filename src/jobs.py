import sys
from log import with_log

@with_log
class Jobs():

    Running = 'Running'
    Stopped = 'Stopped'

    frontend_pid = 0
    total_job_map = dict()

    # 前台进程
    def is_frontend_process(self, pid):
        return pid == self.frontend_pid

    def get_frontend_process(self):
        return self.frontend_pid
    
    def set_frontend_process(self, pid):
        # init status, pid == 0(start, restart)
        self.log.info('set_frontend_process {}'.format(pid))
        self.frontend_pid = pid

    def print_jobs(self):
        """running/stopped/..
        """
        for pid, child_info in self.total_job_map.items():
            if child_info['using'] == 0:
                continue
            sys.stdout.write(str(pid) + '\t' + str(child_info))
            sys.stdout.flush()

    def del_job_by_pid(self, pid):
        self.log.info("[del_job_by_pid] pid={} will be deleted.\n".format(pid))
        if self.total_job_map[pid]['using'] == 1:
            self.total_job_map[pid]['using'] = 0
        else:
            self.log.info("[del_job_by_pid] pid={} not be found.\n".format(pid))

    def get_job(self, pid):
        try:
            if pid in self.total_job_map.keys() and self.total_job_map[pid]['using'] == 1:
                return os.getpid(pid)
        except:
            self.log.info('[get_job] not be found.\n')

    def new_job(self, pid, cmd=None):
        self.log.info('[new_job] running a child process: %d' % (pid))
        self.total_job_map.update({
            pid: {
            'status': self.Running,
            'cmd': cmd,
            'using': 1,
            }
        })
    
    def update_job_status(self, pid, status):
        self.log.info('[update_job_status] status of child process[%d] has changed: %s' % (pid, status))
        self.total_job_map[pid]['status'] = status
