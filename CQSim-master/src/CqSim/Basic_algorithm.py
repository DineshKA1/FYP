
__metaclass__ = type

class Basic_algorithm:
    def __init__ (self, ad_mode = 0, element = None, debug = None, para_list = None, ad_para_list=None):
        self.myInfo = "Basic Algorithm"
        self.ad_mode = ad_mode
        self.element = element
        self.debug = debug
        self.paralist = para_list
        self.ad_paralist = ad_para_list
        
        self.debug.line(4," ")
        self.debug.line(4,"#")
        self.debug.debug("# "+self.myInfo,1)
        self.debug.line(4,"#")
        
        self.algStr=""
        self.scoreList=[]
        i = 0
        temp_num = len(self.element[0])
        while (i < temp_num):
            self.algStr += self.element[0][i]
            i += 1
    
    def reset (self, ad_mode = None, element = None, debug = None, para_list = None, ad_para_list=None):
        #self.debug.debug("* "+self.myInfo+" -- reset",5)
        if ad_mode :
            self.ad_mode = ad_mode 
        if element:
            self.element = element
        if debug:
            self.debug = debug
        if paralist:
            self.paralist = paralist
            
        self.algStr=""
        self.scoreList=[]
        i = 0
        temp_num = len(self.element[0])
        while (i < temp_num):
            self.algStr += self.element[0][i]
            i += 1
            
    def get_score(self, wait_job, currentTime, para_list = None):
        #self.debug.debug("* "+self.myInfo+" -- get_score",5)
        self.scoreList = []
        waitNum = len(wait_job)
        if (waitNum<=0):
            return []
        else:
            i=0
            z=currentTime - wait_job[0]['submit']
            l=wait_job[0]['reqTime']
            while (i<waitNum):
                temp_w = currentTime - wait_job[i]['submit']
                if (temp_w>z):
                    z=temp_w
                if (wait_job[i]['reqTime']<l):
                    l=wait_job[i]['reqTime']
                i+=1
            i=0
            if (z == 0):
                z = 1
            while (i<waitNum):
                s = float(wait_job[i]['submit'])
                t = float(wait_job[i]['reqTime'])
                n = float(wait_job[i]['reqProc'])
                w = int(currentTime - s)
                self.scoreList.append(float(eval(self.algStr)))
                i += 1
        #self.debug.debug("  Score:"+str(self.scoreList),4)
        return self.scoreList
            
    def log_analysis(self):
        #self.debug.debug("* "+self.myInfo+" -- log_analysis",5)
        return 1
            
    def alg_adapt(self, para_in):
        #self.debug.debug("* "+self.myInfo+" -- alg_adapt",5)
        return 1
            


class GavelScheduling(Basic_algorithm):
    def __init__(self, ad_mode=0, element=None, debug=None, para_list=None, ad_para_list=None, time_quantum=1):
        super().__init__(ad_mode, element, debug, para_list, ad_para_list)
        self.time_quantum = time_quantum

    def get_score(self, wait_job, currentTime, para_list=None):
        self.scoreList = []
        waitNum = len(wait_job)
        if waitNum <= 0:
            return []

        for i in range(waitNum):
            submit_time = wait_job[i]['submit']
            run_time = wait_job[i]['redProc']
            waited_time = currentTime - submit_time

            remaining_time = max(0, run_time-waited_time)
            score = waited_time / (remaining_time+1)
            self.scoreList.append(score)

        return self.scoreList
    
    def schedule_jobs(self, wait_job, current_Time):

        scores = self.get_score(wait_job, current_Time)
        sorted_jobs = sorted(zip(wait_job, scores), key=lambda x: x[1])

        for job, score in sorted_jobs:

            run_time = min(job['reqProc'], self.time_quantum)
            job['reqProc'] -= run_time

            current_Time += run_time

            if job['reqProc'] <= 0:
                self.job_finish(job['id'], current_Time)


    def job_finish(self, job_id, finish_time):
        self.debug.debug(f"Job {job_id} finished at time {finish_time}", 1)



class FCFS:
    def __init__(self):
        self.completed_jobs = []
        
    def schedule_jobs(self, jobs, current_time):
        # Sort jobs by submit time
        jobs = sorted(jobs, key=lambda x: x['submit'])
        for job in jobs:
            if job['submit'] <= current_time:
                # Process job
                self.completed_jobs.append(job)
                current_time += job['reqProc']  # Update current time after job completion
                jobs.remove(job)  # Remove completed job
