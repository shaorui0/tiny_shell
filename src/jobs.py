
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
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError(name)
        
    # 前台进程
    def is_fg_process(self, pid):
        return pid == self.frontend_pid

    def get_frontend_process(self):
        return self.frontend_pid
    
    def set_frontend_process(self, pid):
        # init status, pid == 0(start, restart)
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
        # TODO 删除using == 0的进程
        # 【注】不能边遍历一个迭代器边删除（或增加）
        for pid, child_info in self.total_job_map.items():
            if child_info['using'] == 0:
                continue
            else:
                print(pid, child_info)

        #print(self.total_job_map) # TODO trivial
        return

    def del_job_by_pid(self, pid):
        print("[del_job_by_pid] pid={} will be deleted.\n".format(pid))
        if self.total_job_map[pid]['using'] == 1:
            self.total_job_map[pid]['using'] = 0
        # 不然我们说，没找到这个pid
        else:
            print("[del_job_by_pid] pid={} not be found.\n".format(pid))

    def get_job(self, pid):
        try:
            if pid in self.total_job_map.keys() and self.total_job_map[pid]['using'] == 1:
                return os.getpid(pid)
        except:
            print('[get_job] not be found.\n')

    def new_job(self, pid, cmd=None):
        print('[new_job] running a child process', pid)
        self.total_job_map.update({
            pid: {
            'status': 'Running',
            'cmd': cmd,
            'using': 1,
            }
        })
    
    # status怎么更新状态？也就是waitpid的返回值，返回pid表示当前进程终止，返回0表示什么，返回-1表示什么？
    def update_job_status(self, pid, status):
        print('[update_job_status] status of child process has changed:', pid, status)
        #print(self.total_job_map)
        self.total_job_map[pid]['status'] = status
