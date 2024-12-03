__metaclass__ = type

class Basic_algorithm:
    def __init__(self, ad_mode=0, element=None, debug=None, para_list=None, ad_para_list=None):
        self.myInfo = "Basic Algorithm"
        self.ad_mode = ad_mode
        self.element = element
        self.debug = debug
        self.paralist = para_list
        self.ad_paralist = ad_para_list
        
        if self.debug:
            self.debug.line(4, " ")
            self.debug.line(4, "#")
            self.debug.debug(f"# {self.myInfo}", 1)
            self.debug.line(4, "#")
        
        self.algStr = ""
        self.scoreList = []
        i = 0
        temp_num = len(self.element[0]) if self.element else 0
        while i < temp_num:
            self.algStr += self.element[0][i]
            i += 1
    
    def reset(self, ad_mode=None, element=None, debug=None, para_list=None, ad_para_list=None):
        if ad_mode:
            self.ad_mode = ad_mode 
        if element:
            self.element = element
        if debug:
            self.debug = debug
        if para_list:
            self.paralist = para_list
            
        self.algStr = ""
        self.scoreList = []
        i = 0
        temp_num = len(self.element[0]) if self.element else 0
        while i < temp_num:
            self.algStr += self.element[0][i]
            i += 1
            
    def get_score(self, wait_job, currentTime, para_list=None):
        self.scoreList = []
        waitNum = len(wait_job)
        if waitNum <= 0:
            return []
        else:
            i = 0
            z = currentTime - wait_job[0]['submit']
            l = wait_job[0]['reqTime']
            while i < waitNum:
                temp_w = currentTime - wait_job[i]['submit']
                if temp_w > z:
                    z = temp_w
                if wait_job[i]['reqTime'] < l:
                    l = wait_job[i]['reqTime']
                i += 1
            i = 0
            if z == 0:
                z = 1
            while i < waitNum:
                s = float(wait_job[i]['submit'])
                t = float(wait_job[i]['reqTime'])
                n = float(wait_job[i]['reqProc'])
                w = int(currentTime - s)
                self.scoreList.append(float(eval(self.algStr)))
                i += 1
        return self.scoreList
            
    def log_analysis(self):
        if self.debug:
            self.debug.debug(f"* {self.myInfo} -- log_analysis", 5)
        return 1
            
    def alg_adapt(self, para_in):
        if self.debug:
            self.debug.debug(f"* {self.myInfo} -- alg_adapt", 5)
        return 1


class GavelScheduling(Basic_algorithm):
    def __init__(self, ad_mode=0, element=None, debug=None, para_list=None, ad_para_list=None, time_quantum=1):
        super().__init__(ad_mode, element, debug, para_list, ad_para_list)
        self.time_quantum = time_quantum
        self.workload_data = None  #init placeholder for the workload data

    def set_workload_data(self, workload_data):
        self.workload_data = workload_data  #set the workload data


    def get_score(self, wait_job, currentTime, para_list=None):
        self.scoreList = []
        waitNum = len(wait_job)
        if waitNum <= 0:
            return []

        for i in range(waitNum):
            submit_time = wait_job[i]['submit']
            run_time = wait_job[i]['reqProc']  
            waited_time = currentTime - submit_time

            remaining_time = max(0, run_time - waited_time)
            score = waited_time / (remaining_time + 1)
            self.scoreList.append(score)

        return self.scoreList
    
    def schedule(self, wait_job, currentTime):
        self.schedule_jobs(wait_job, currentTime)

    def schedule_jobs(self, wait_job, currentTime):
        scores = self.get_score(wait_job, currentTime)
        sorted_jobs = sorted(zip(wait_job, scores), key=lambda x: x[1])

        for job, score in sorted_jobs:
            run_time = min(job['reqProc'], self.time_quantum)
            job['reqProc'] -= run_time
            currentTime += run_time

            if job['reqProc'] <= 0:
                self.job_finish(job['id'], currentTime)

    def job_finish(self, job_id, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job_id} finished at time {finish_time}", 1)


class FCFS(Basic_algorithm):
    def __init__(self):
        self.completed_jobs = []
        self.myInfo = "FCFS"
        self.algStr = "0"
        
    def schedule_jobs(self, jobs, currentTime):
        
        jobs = sorted(jobs, key=lambda x: x['submit'])
        i = 0
        while i < len(jobs):
            job = jobs[i]
            if job['submit'] <= currentTime:
                self.completed_jobs.append(job)
                currentTime += job['reqProc']
                jobs.remove(job)  #remove completed job
            i += 1

    def job_finish(self, job, finish_time):
        return 0


# Round Robin (RR) Scheduling
class RoundRobin(Basic_algorithm):
    def __init__(self, time_quantum):
        self.time_quantum = time_quantum

    def schedule_jobs(self, jobs, currentTime):
        queue = jobs[:]
        while queue:
            job = queue.pop(0)
            if job['reqProc'] > self.time_quantum:
                job['reqProc'] -= self.time_quantum
                currentTime += self.time_quantum
                queue.append(job)
            else:
                currentTime += job['reqProc']
                self.job_finish(job, currentTime)

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)


# Shortest Job First (SJF) Scheduling
class SJF(Basic_algorithm):
    def schedule_jobs(self, jobs, currentTime):
        sorted_jobs = sorted(jobs, key=lambda x: x['reqProc'])
        for job in sorted_jobs:
            if job['submit'] <= currentTime:
                self.job_finish(job, currentTime)
                currentTime += job['reqProc']

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)


# Shortest Remaining Time First (SRTF) Scheduling
class SRTF(Basic_algorithm):
    def schedule_jobs(self, jobs, currentTime):
        while jobs:
            job = min(jobs, key=lambda x: x['reqProc'])
            if job['submit'] <= currentTime:
                if job['reqProc'] > 0:
                    currentTime += job['reqProc']
                    job['reqProc'] = 0
                    self.job_finish(job, currentTime)
                jobs.remove(job)

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)


# Priority Scheduling
class PriorityScheduling(Basic_algorithm):
    def schedule_jobs(self, jobs, currentTime):
        sorted_jobs = sorted(jobs, key=lambda x: x['priority'], reverse=True)
        for job in sorted_jobs:
            if job['submit'] <= currentTime:
                currentTime += job['reqProc']
                self.job_finish(job, currentTime)

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)


# Multilevel Feedback Queue Scheduling
class MultilevelFeedbackQueue(Basic_algorithm):
    def __init__(self, queues):
        self.queues = queues

    def schedule_jobs(self, jobs, currentTime):
        for queue in self.queues:
            queue_jobs = [job for job in jobs if job['priority'] == queue]
            RoundRobin(time_quantum=2).schedule_jobs(queue_jobs, currentTime)

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)


# Earliest Deadline First (EDF) Scheduling
class EDF(Basic_algorithm):
    def schedule_jobs(self, jobs, currentTime):
        sorted_jobs = sorted(jobs, key=lambda x: x['deadline'])
        for job in sorted_jobs:
            if job['submit'] <= currentTime:
                currentTime += job['reqProc']
                self.job_finish(job, currentTime)

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)
