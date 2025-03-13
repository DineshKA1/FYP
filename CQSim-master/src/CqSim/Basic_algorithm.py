__metaclass__ = type

import time

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
        print("scores:", self.scoreList)
        return self.scoreList
            
    def log_analysis(self):
        if self.debug:
            self.debug.debug(f"* {self.myInfo} -- log_analysis", 5)
        return 1
            
    def alg_adapt(self, para_in):
        if self.debug:
            self.debug.debug(f"* {self.myInfo} -- alg_adapt", 5)
        return 1


# Fixed GavelScheduling
class GavelScheduling(Basic_algorithm):
    def __init__(self, workload_data=None, ad_mode=0, element=None, debug=None, para_list=None, ad_para_list=None, time_quantum=1):
        super().__init__(ad_mode, element, debug, para_list, ad_para_list)
        self.time_quantum = time_quantum
        self.workload_data = workload_data
        self.algStr = "wait_time / (reqProc + 1)"  # Simplified formula
        self.hybrid_scheduler = HybridScheduling(workload_data=workload_data, ad_mode=ad_mode, element=element, debug=debug)

    def set_workload_data(self, workload_data):
        self.workload_data = workload_data

    def get_score(self, wait_job, currentTime, para_list=None):
        """Calculates scores based on the Gavel formula."""
        self.scoreList = []
        if not wait_job:
            return []

        for job in wait_job:
            
            if job['submit'] < 0:
                print(f"Warning: Job {job['id']} has negative submit time: {job['submit']}. Resetting to 0.")
                job['submit'] = 0  # Fix negative submission time

            waited_time = max(0, currentTime - job['submit'])
            remaining_time = max(1, job['reqProc'])
        
            # Incorporate GPU consideration in the score calculation
            gpu_weight = 2 if job.get('gpu_required', 0) > 0 else 1  # Example: give higher weight to GPU jobs
            score = (waited_time / (remaining_time + 1)) * gpu_weight  # Adjusted score formula
            self.scoreList.append(score)

        print("scores:", self.scoreList)

        for job in wait_job:

            if job['submit'] < 0:
                print(f"error: Job {job['id']} has a negative submission time: {job['submit']}")
                job['submit'] = 0

            print(f"Job {job['id']} - Submit: {job['submit']}, Required Time: {job['reqProc']}, Current Time: {currentTime}")

        return self.scoreList


    def schedule(self, wait_job, currentTime):
        if not wait_job:
            return


        # Sanitize current time
        if currentTime < 0:
            print(f"Warning: Negative current time detected: {currentTime}. Resetting to 0.")
            currentTime = 0

        self.hybrid_scheduler.hybrid_schedule(wait_job, currentTime)
        
        scores = self.get_score(wait_job, currentTime)
        wait_job = [job for job in wait_job if job['submit'] >= 0]
        #sorted_jobs = sorted(zip(wait_job, scores), key=lambda x: x[1], reverse=True)
        #sorted_jobs = sorted(zip(wait_job, scores), key=lambda x: x[0]['submit'])
        sorted_jobs = sorted(zip(wait_job, scores), key=lambda x: max(0, x[0]['submit']))


        for job, _ in sorted_jobs:
            # Check if the node has enough resources
            # Debug: Check available resources before scheduling
            print(f"Trying to schedule job {job['id']} at time {currentTime} with {self.available_procs} CPUs, {self.available_gpus} GPUs")
            
            if job['reqProc'] < 0:
                print(f"error: Job {job['id']} has negative processing time: {job['reqProc']}")
                job['reqProc'] = abs(job['reqProc'])
            
            if (self.available_procs >= job['reqProc'] and 
                self.available_mem >= job['reqMem'] and 
                self.available_gpus >= job.get('gpu_required', 0)):  # GPU check
                
                # Allocate resources
                self.available_procs -= job['reqProc']
                self.available_mem -= job['reqMem']
                self.available_gpus -= job.get('gpu_required', 0)

                #run_time = min(job['reqProc'], self.time_quantum)
                run_time = max(1, min(job['reqProc'], self.time_quantum))
                job['reqProc'] -= run_time

                print(f"Before update: Current Time = {currentTime}")
                currentTime = max(0, currentTime + run_time)
                print(f"After update: Current Time = {currentTime}")
                #currentTime += run_time

                if currentTime < 0:
                    print(f"error: Negative time detected! Job {job['id']} caused Current Time = {currentTime}")
                    exit()  # Stop execution when the first negative time appears


                #Set proper completion time
                job['completion_time'] = max(job['submit'], currentTime + job['reqProc'])
                print(f"Job {job['id']} scheduled to complete at {job['completion_time']}")
                
                # Debugging: Job successfully started
                print(f"Job {job['id']} started at {currentTime}")

                if job['reqProc'] <= 0:
                    self.release_resources(job)
                    self.job_finish(job['id'], currentTime)

    def release_resources(self, job):
        """Release resources including GPUs."""
        self.available_procs += job['reqProc']
        self.available_mem += job['reqMem']
        self.available_gpus += job.get('gpu_required', 0)


    def job_finish(self, job_id, finish_time):
        # Debugging: Job completion tracking
        print(f"Job {job_id} finished at {finish_time}")
        if self.debug:
            self.debug.debug(f"Job {job_id} finished at time {finish_time}", 1)

'''
class GavelScheduling(Basic_algorithm):
    def __init__(self, workload_data=None, ad_mode=0, element=None, debug=None, para_list=None, ad_para_list=None, time_quantum=1):
        super().__init__(ad_mode, element, debug, para_list, ad_para_list)
        self.time_quantum = time_quantum
        self.workload_data = workload_data
        self.algStr = "wait_time / (reqProc + 1)"  # Simplified formula
        self.hybrid_scheduler = HybridScheduling(workload_data=workload_data, ad_mode=ad_mode, element=element, debug=debug)
        self.running_jobs = []  # Track currently running jobs

        self.available_gpus = element[0].get("gpu", 0) if element and isinstance(element[0], dict) else 0

    def set_workload_data(self, workload_data):
        self.workload_data = workload_data


    def get_score(self, wait_job, currentTime):
        """Calculates scores based on the Gavel formula."""
        self.scoreList = []
        if not wait_job:
            return []

        for job in wait_job:
            waited_time = max(0, currentTime - job['submit'])
            remaining_time = max(1, job['reqProc'])
        
            # Dynamic GPU prioritization
            gpu_weight = 1 + job.get('gpu_required', 0) / max(1, self.available_gpus)
            score = (waited_time / (remaining_time + 1)) * gpu_weight
            self.scoreList.append((job, score))

        # Sort jobs by highest score
        self.scoreList.sort(key=lambda x: x[1], reverse=True)
        return self.scoreList

    def preempt_jobs(self, currentTime):
        """Check if a waiting job should preempt a running job."""
        if not self.running_jobs:
            return  # No running jobs to preempt

        # Get waiting jobs sorted by Gavel scores
        waiting_jobs = self.get_score(self.workload_data, currentTime)
        if not waiting_jobs:
            return
        
        highest_waiting_job, highest_waiting_score = waiting_jobs[0]

        # Check if any running job has a lower score than the waiting job
        for running_job in self.running_jobs:
            running_score = (currentTime - running_job['start_time']) / max(1, running_job['reqProc'])
            
            if highest_waiting_score > running_score:
                # Preempt running job
                print(f"Preempting Job {running_job['id']} for Job {highest_waiting_job['id']}")

                # Release its resources
                self.release_resources(running_job)
                running_job['submit'] = currentTime  # Reset submission time for requeue
                self.workload_data.append(running_job)  # Re-add to waiting queue

                # Remove from running jobs
                self.running_jobs.remove(running_job)

                # Schedule new job
                self.schedule([highest_waiting_job], currentTime)
                return  # Only preempt one job at a time

    def schedule(self, wait_job, currentTime):
        if not wait_job:
            return

        self.hybrid_scheduler.hybrid_schedule(wait_job, currentTime)

        # Preempt if needed
        self.preempt_jobs(currentTime)

        sorted_jobs = self.get_score(wait_job, currentTime)

        for job, _ in sorted_jobs:
            # Check if enough resources are available
            if (self.available_procs >= job['reqProc'] and 
                self.available_mem >= job['reqMem'] and 
                self.available_gpus >= job.get('gpu_required', 0)):  # GPU check
                
                # Allocate resources
                self.available_procs -= job['reqProc']
                self.available_mem -= job['reqMem']
                self.available_gpus -= job.get('gpu_required', 0)

                # Start job execution
                job['start_time'] = currentTime
                execution_time = max(1, job['reqProc'])
                job['completion_time'] = currentTime + execution_time
                currentTime = job['completion_time']

                # Track running jobs
                self.running_jobs.append(job)

                # Release resources when done
                self.release_resources(job)
                self.job_finish(job, job['completion_time'])

    def release_resources(self, job):
        """Release CPU, memory, and GPUs when a job finishes."""
        self.available_procs += max(0, job['reqProc'])
        self.available_mem += max(0, job['reqMem'])
        self.available_gpus += max(0, job.get('gpu_required', 0))

    def job_finish(self, job, finish_time):
        """Log job completion and remove from running list."""
        print(f"Job {job['id']} finished at {finish_time}")
        if job in self.running_jobs:
            self.running_jobs.remove(job)
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)
'''

'''
# Fixed FCFS
class FCFS(Basic_algorithm): 
    def __init__(self):
        super().__init__()
        self.completed_jobs = []
        self.myInfo = "FCFS"
        self.algStr = "0"
        self.hybrid_scheduler = HybridScheduling()
        
    def schedule_jobs(self, jobs, currentTime):
        self.hybrid_scheduler.hybrid_schedule(jobs, currentTime)
        jobs.sort(key=lambda x: x['submit'])  # Sort jobs by submission time
        
    
        # Separate GPU and CPU-only jobs
        gpu_jobs = [job for job in jobs if job.get('gpu_required', 0) > 0]
        cpu_jobs = [job for job in jobs if job.get('gpu_required', 0) == 0]
    
        # Prioritize GPU jobs first
        for job in gpu_jobs + cpu_jobs:
            if job['submit'] > currentTime:
                currentTime = job['submit']  # Wait until job arrival

            # Check if resources are available (including GPUs)
            if (self.available_procs >= job['reqProc'] and 
                self.available_mem >= job['reqMem'] and 
                self.available_gpus >= job.get('gpu_required', 0)):  # GPU check
        
                # Allocate resources
                self.available_procs -= job['reqProc']
                self.available_mem -= job['reqMem']
                self.available_gpus -= job.get('gpu_required', 0)

                self.completed_jobs.append(job)
                currentTime += job['reqProc']
        
                # Release resources after execution
                self.release_resources(job)
                self.job_finish(job, currentTime)


    def release_resources(self, job):
        """Release CPU, memory, and GPUs when a job finishes."""
        self.available_procs += job['reqProc']
        self.available_mem += job['reqMem']            
        self.available_gpus += job.get('gpu_required', 0)


    def get_score(self, jobs, currentTime):
        """Assigns scores based on job arrival order."""
        self.scoreList = []
        if not jobs:
            return []
        
        sorted_jobs = sorted(jobs, key=lambda x: x['submit'])  # Sort jobs by submission time
        print("job submission times:", [job['submit'] for job in sorted_jobs])
        
        for i, job in enumerate(sorted_jobs):
            self.scoreList.append(len(jobs) - i)  # Earlier jobs get higher priority
        
        print("scores:", self.scoreList)
        return self.scoreList

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)
'''


#FCFS with GPU considerations
class FCFS(Basic_algorithm): 
    def __init__(self, workload_data=None, ad_mode=0, element=None, debug=None, para_list=None, ad_para_list=None):
        super().__init__(ad_mode, element, debug, para_list, ad_para_list)
        self.completed_jobs = []
        self.myInfo = "FCFS"
        self.algStr = "0"
        self.workload_data = workload_data
        self.available_procs = 0  # Initialize available processors
        self.available_mem = 0    # Initialize available memory
        self.available_gpus = 0   # Initialize available GPUs
        
    def set_resources(self, procs, mem, gpus):
        """Set available resources."""
        self.available_procs = procs
        self.available_mem = mem
        self.available_gpus = gpus

    def schedule_jobs(self, jobs, currentTime):
        if not jobs:
            return currentTime
        
        # Sanitize job submission times
        for job in jobs:
            if job['submit'] < 0:
                print(f"Warning: Job {job['id']} has negative submit time: {job['submit']}. Resetting to 0.")
                job['submit'] = 0
        
        # Sort jobs with GPU priority while preserving FCFS order
        sorted_jobs = sorted(jobs, key=lambda x: (x.get('gpu_required', 0) == 0, x['submit']))
        
        while sorted_jobs:
            job = sorted_jobs[0]  # Pick the first job in line
            
            if job['submit'] > currentTime:
                currentTime = job['submit']  # Advance time to job submission
                
            if (self.available_procs >= job['reqProc'] and 
                self.available_mem >= job['reqMem'] and 
                self.available_gpus >= job.get('gpu_required', 0)):
                
                # Allocate resources
                self.available_procs -= job['reqProc']
                self.available_mem -= job['reqMem']
                self.available_gpus -= job.get('gpu_required', 0)
                
                # Execute job
                job['start_time'] = currentTime
                execution_time = max(1, job['reqProc'])
                job['completion_time'] = currentTime + execution_time
                currentTime = job['completion_time']
                
                # Track completed jobs
                self.completed_jobs.append(job)
                
                # Release resources after execution
                self.release_resources(job)
                
                # Log job completion
                self.job_finish(job, job['completion_time'])
                
                sorted_jobs.pop(0)  # Remove the executed job
            else:
                # Attempt backfilling: Find a smaller job that can fit
                backfilled = False
                for i in range(1, len(sorted_jobs)):
                    candidate = sorted_jobs[i]
                    if (self.available_procs >= candidate['reqProc'] and 
                        self.available_mem >= candidate['reqMem'] and 
                        self.available_gpus >= candidate.get('gpu_required', 0)):
                        
                        # Swap and process the backfilled job
                        sorted_jobs[0], sorted_jobs[i] = sorted_jobs[i], sorted_jobs[0]
                        backfilled = True
                        break
                
                if not backfilled:
                    break  # No job could be scheduled, wait for resources
        
        return currentTime

    def release_resources(self, job):
        """Release CPU, memory, and GPUs when a job finishes."""
        self.available_procs += job['reqProc']
        self.available_mem += job['reqMem']            
        self.available_gpus += job.get('gpu_required', 0)
        
        if self.debug:
            self.debug.debug(f"Resources released - Procs: {job['reqProc']}, Mem: {job['reqMem']}, GPUs: {job.get('gpu_required', 0)}", 2)

    def get_score(self, jobs, currentTime):
        """Assigns scores based on job arrival order with GPU awareness."""
        self.scoreList = []
        if not jobs:
            return []
        
        # Basic FCFS - earlier submission gets higher priority
        #sorted_jobs = sorted(jobs, key=lambda x: x['submit'])

        #ensures GPU jobs are scheduled first while preserving FCFS order
        sorted_jobs = sorted(jobs, key=lambda x: (x.get('gpu_required', 0) == 0, x['submit']))

        
        for i, job in enumerate(sorted_jobs):
            # Optional: Could add GPU weight here if you want to bias toward GPU jobs
            #gpu_factor = 2 if job.get('gpu_required', 0) > 0 else 1
            #self.scoreList.append((len(jobs) - i) * gpu_factor)
            
            # Pure FCFS
            self.scoreList.append(len(jobs) - i)  # Earlier jobs get higher priority
            
        print("scores:", self.scoreList)
        return self.scoreList

    def job_finish(self, job, finish_time):
        """Log job completion."""
        print(f"Job {job['id']} finished at {finish_time}")
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)

class HybridScheduling(Basic_algorithm):
    def __init__(self, workload_data=None, ad_mode=0, element=None, debug=None, para_list=None, ad_para_list=None, time_quantum=1):
        super().__init__(ad_mode, element, debug, para_list, ad_para_list)
        self.time_quantum = time_quantum
        self.workload_data = workload_data
        self.algStr = "Hybrid Scheduling"
    
    def hybrid_schedule(self, jobs, currentTime):
        # Separate jobs based on GPU requirements
        cpu_jobs = [job for job in jobs if job.get('gpu_required', 0) == 0]
        gpu_jobs = [job for job in jobs if job.get('gpu_required', 0) > 0]
        
        # Sort jobs based on Gavel or FCFS logic
        cpu_jobs = self.sort_jobs(cpu_jobs, currentTime)
        gpu_jobs = self.sort_jobs(gpu_jobs, currentTime)
        
        # Prioritize GPU jobs first
        self.schedule_jobs(gpu_jobs, currentTime)
        self.schedule_jobs(cpu_jobs, currentTime)
        
    def sort_jobs(self, jobs, currentTime):
        # Sort jobs by the scheduling policy: Gavel (wait time) or FCFS (submission time)
        if isinstance(self, GavelScheduling):
            return sorted(jobs, key=lambda job: (currentTime - job['submit']) / (job['reqProc'] + 1), reverse=True)
        elif isinstance(self, FCFS):
            return sorted(jobs, key=lambda job: job['submit'])
        return jobs  # Default: no sorting

    def schedule_jobs(self, jobs, currentTime):
        for job in jobs:
            if job['submit'] < 0:
                print(f"Warning: Job {job['id']} has negative submit time: {job['submit']}. Resetting to 0.")
                job['submit'] = 0
            
            if job['submit'] > currentTime:
                currentTime = job['submit']  # Wait until job arrival
            
            # Ensure req times are positive
            if job['reqProc'] <= 0:
                print(f"Warning: Job {job['id']} has invalid required time: {job['reqProc']}. Setting to minimum time.")
                job['reqProc'] = 1  # Set to minimum processing time
            '''
            if job['submit'] > currentTime:
                currentTime = job['submit']  # Wait until job arrival
                if self.debug:
                    self.debug.debug(f"Waiting for job {job['id']} to arrive at time {job['submit']}", 1)
            '''
            # Log resource availability
            if self.debug:
                self.debug.debug(f"Available resources - Procs: {self.available_procs}, Mem: {self.available_mem}, GPUs: {self.available_gpus}", 1)

            # Check if resources are available (including GPUs)
            if (self.available_procs >= job['reqProc'] and 
                self.available_mem >= job['reqMem'] and 
                self.available_gpus >= job.get('gpu_required', 0)):
            
                # Allocate resources
                self.available_procs -= job['reqProc']
                self.available_mem -= job['reqMem']
                self.available_gpus -= job.get('gpu_required', 0)

                self.completed_jobs.append(job)
                currentTime = max(currentTime, currentTime + job['reqProc'])
            
                # Log job allocation
                if self.debug:
                    self.debug.debug(f"Allocating resources to job {job['id']}: Procs: {job['reqProc']}, Mem: {job['reqMem']}, GPUs: {job.get('gpu_required', 0)}", 1)

                # Release resources after execution
                self.release_resources(job)
                self.job_finish(job, currentTime)


    def release_resources(self, job):
        """Release resources including CPUs, memory, and GPUs."""
        self.available_procs += job['reqProc']
        self.available_mem += job['reqMem']
        self.available_gpus += job.get('gpu_required', 0)

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)



class ResourceTracker:
    def __init__(self, total_procs, total_gpus):
        self.total_procs = total_procs
        self.total_gpus = total_gpus
        self.cpu_usage = []
        self.gpu_usage = []
        self.cpu_allocation_ratio = []
        self.gpu_allocation_ratio = []
        self.cpu_utilization_ratio = []
        self.gpu_utilization_ratio = []
        self.timestamp = []

    def log_usage(self, available_procs, available_gpus, used_procs, used_gpus, currentTime):
        allocated_procs = self.total_procs - available_procs
        allocated_gpus = self.total_gpus - available_gpus

        # Compute ratios
        cpu_alloc_ratio = allocated_procs / self.total_procs if self.total_procs > 0 else 0
        gpu_alloc_ratio = allocated_gpus / self.total_gpus if self.total_gpus > 0 else 0
        cpu_util_ratio = used_procs / allocated_procs if allocated_procs > 0 else 0
        gpu_util_ratio = used_gpus / allocated_gpus if allocated_gpus > 0 else 0

        # Store values
        self.cpu_usage.append(available_procs)
        self.gpu_usage.append(available_gpus)
        self.cpu_allocation_ratio.append(cpu_alloc_ratio)
        self.gpu_allocation_ratio.append(gpu_alloc_ratio)
        self.cpu_utilization_ratio.append(cpu_util_ratio)
        self.gpu_utilization_ratio.append(gpu_util_ratio)
        self.timestamp.append(currentTime)

        print(f"Time {currentTime}: CPUs Available: {available_procs}, GPUs Available: {available_gpus}, "
              f"CPU Allocation Ratio: {cpu_alloc_ratio:.2f}, GPU Allocation Ratio: {gpu_alloc_ratio:.2f}, "
              f"CPU Utilization Ratio: {cpu_util_ratio:.2f}, GPU Utilization Ratio: {gpu_util_ratio:.2f}")




# Round Robin (RR) Scheduling working
class RoundRobin(Basic_algorithm):
    def __init__(self, time_quantum):
        self.time_quantum = time_quantum
        self.myInfo = "RoundRobin Scheduling Algorithm"
        self.algStr = "0"

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
    
    def get_score(self, jobs, currentTime):
        """Override to prevent CQSim from using eval(self.algStr)."""
        return [0] * len(jobs)  # Assign equal priority to all jobs in Round Robin

'''
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
'''

'''
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
'''

# Priority Scheduling working
class PriorityScheduling(Basic_algorithm):
    def __init__(self, priority=None):
        super().__init__()  # Call parent constructor
        self.priority = priority  # Store priority if needed
        self.myInfo = "Priority Scheduling Algorithm"  # Required for CQSim
        self.algStr = "0"  # Default value to avoid eval error


    def schedule_jobs(self, jobs, currentTime):
        sorted_jobs = sorted(jobs, key=lambda x: x['priority'], reverse=True)
        for job in sorted_jobs:
            if job['submit'] <= currentTime:
                currentTime += job['reqProc']
                self.job_finish(job, currentTime)

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)

    def get_score(self, jobs, currentTime):
        """Override to prevent CQSim from using eval(self.algStr)."""
        return [job.get('priority', 0) for job in jobs]  # Assign job priorities


'''
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
'''
'''
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
'''