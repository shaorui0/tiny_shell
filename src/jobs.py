import sys
from log import with_log

@with_log
class Jobs():

    RUNNING = 'Running'
    STOPPED = 'Stopped'
    
    TERMINATED = 0
    UNTERMINATED = 1

    frontend_pid = 0
    total_job_map = dict()

    def _is_frontend_process(self, pid):
        return pid == self.frontend_pid

    def _get_frontend_process(self):
        return self.frontend_pid
    
    def _set_frontend_process(self, pid):
        self.log.info('_set_frontend_process {}'.format(pid))
        self.frontend_pid = pid

    def _print_jobs(self):
        """running/stopped/..
        """
        for pid, child_info in self.total_job_map.items():
            if child_info['using'] == self.TERMINATED:
                continue
            sys.stdout.write(str(pid) + '\t' + str(child_info))
            sys.stdout.flush()

    def _del_job_by_pid(self, pid):
        self.log.info("[_del_job_by_pid] pid={} will be deleted.\n".format(pid))
        if self.total_job_map[pid]['using'] == self.UNTERMINATED:
            self.total_job_map[pid]['using'] = self.TERMINATED
        else:
            self.log.info("[_del_job_by_pid] pid={} not be found.\n".format(pid))

    def _get_job(self, pid):
        try:
            if pid in self.total_job_map.keys() and self.total_job_map[pid]['using'] == self.UNTERMINATED:
                return os.getpid(pid)
        except:
            self.log.info('[_get_job] not be found.\n')

    def _new_job(self, pid, cmd=None):
        self.log.info('[_new_job] running a child process: %d' % (pid))
        self.total_job_map.update({
            pid: {
            'status': self.RUNNING,
            'cmd': cmd,
            'using': self.UNTERMINATED,
            }
        })
    
    def _update_job_status(self, pid, status):
        self.log.info('[_update_job_status] status of child process[%d] has changed: %s' % (pid, status))
        self.total_job_map[pid]['status'] = status
