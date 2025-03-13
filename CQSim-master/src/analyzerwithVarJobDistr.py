import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# File paths
gavel_file = "/Users/dinesh/Desktop/new/CQFYP/CQSim-master/src/gavelNew2.txt"
fcfs_file = "/Users/dinesh/Desktop/new/CQFYP/CQSim-master/src/fcfsNew2.txt"
TOTAL_RESOURCES = 128  # Assumed total available resources

def parse_output(file_path, algorithm_name):
    """Extracts job completion times, submission times, and waiting times from CQSim output logs."""
    job_completion = {}
    job_submission = {}
    waiting_times = {}
    job_gpu = {}  # GPU usage per job
    job_gpu_ratio = {}  # GPU/CPU ratio per job
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    print(f"\nProcessing {algorithm_name} Output\n" + "="*30)
    
    for i, line in enumerate(lines):
        if "[Submit]" in line:
            job_id = int(re.findall(r'\d+', line)[0])
            if job_id not in job_submission:  # Prevent duplicate submissions
                for j in range(i, min(i+10, len(lines))):  # Look FORWARD for tempStr
                    if "tempStr" in lines[j]:
                        temp_values = lines[j].strip().split(";")
                        if len(temp_values) >= 19:  # Ensure correct format
                            gpu_count = int(temp_values[-1])  # GPU is last value
                            job_gpu[job_id] = gpu_count
                            print(f"Extracted GPU for Job {job_id}: {gpu_count}")
                        break  # Stop searching once found
                
                for j in range(i-1, max(i-10, 0), -1):  # Look BACKWARD for submit time
                    time_matches = re.findall(r'Time:\s*(\d+\.\d+)', lines[j])
                    if time_matches:
                        time = float(time_matches[0])
                        job_submission[job_id] = time
                        break  # Stop searching once found
                
                # Default GPU value if no info was found
                job_gpu.setdefault(job_id, 0)
 
        
        elif "[Finish]" in line:
            job_id = int(re.findall(r'\d+', line)[0])
            if job_id not in job_completion and job_id in job_submission:  # Ensure valid finish
                for j in range(i-1, max(i-10, 0), -1):
                    time_matches = re.findall(r'Time:\s*(\d+\.\d+)', lines[j])
                    if time_matches:
                        time = float(time_matches[0])
                        job_completion[job_id] = time
                        waiting_times[job_id] = job_completion[job_id] - job_submission[job_id]
                        print(f"Finish Detected: Job {job_id}, Time {time}")
                        break  
        # Ensure all jobs have default GPU values if missing
        for job_id in job_submission:
            job_gpu.setdefault(job_id, 0)  # Default GPU count = 0
            job_gpu_ratio.setdefault(job_id, 0.0)  # Default GPU/CPU ratio = 0.0

    return job_submission, job_completion, waiting_times, job_gpu, job_gpu_ratio


def compute_utilization(submission, completion, job_gpu, job_gpu_ratio, total_resources, time_step=1000):
    """Computes resource utilization over time, including GPU usage with different ratios."""
    time_range = np.arange(0, max(completion.values()), time_step)
    cpu_utilization = []
    gpu_utilization = []
    
    for t in time_range:
        active_jobs = [job for job in submission if job in completion and submission[job] <= t < completion[job]]
        #active_jobs = [job for job in submission if submission[job] <= t < completion[job]]
        active_time = sum(completion[j] - submission[j] for j in active_jobs)
        active_gpu_time = sum(
    (completion[j] - submission[j]) * job_gpu_ratio.get(j, 0.0)  # Use .get() to avoid KeyError
    for j in active_jobs if job_gpu.get(j, 0) > 0  # Use .get() to avoid KeyError
)

        
        cpu_utilization.append(active_time / (total_resources * time_step))
        gpu_utilization.append(active_gpu_time / (total_resources * time_step))
    
    return time_range, cpu_utilization, gpu_utilization

def compute_slowdown(submission, completion):
    """Computes bounded slowdown for jobs."""
    return {job: (completion[job] - submission[job]) / max(completion[job] - submission[job], 10) for job in submission if job in completion}


def identify_starved_jobs(waiting_times):
    """Identifies jobs that waited significantly longer than average."""
    mean_wait = np.mean(list(waiting_times.values()))
    std_wait = np.std(list(waiting_times.values()))
    threshold = mean_wait + 2 * std_wait
    return {job: wait for job, wait in waiting_times.items() if wait > threshold}


# Parse the logs (Now using actual GPU data)
gavel_submission, gavel_completion, gavel_waiting, gavel_gpu, gavel_gpu_ratio = parse_output(gavel_file, "Gavel")
fcfs_submission, fcfs_completion, fcfs_waiting, fcfs_gpu, fcfs_gpu_ratio = parse_output(fcfs_file, "FCFS")

# Compute utilization
gavel_time, gavel_cpu_util, gavel_gpu_util = compute_utilization(gavel_submission, gavel_completion, gavel_gpu, gavel_gpu_ratio, TOTAL_RESOURCES)
fcfs_time, fcfs_cpu_util, fcfs_gpu_util = compute_utilization(fcfs_submission, fcfs_completion, fcfs_gpu, fcfs_gpu_ratio, TOTAL_RESOURCES)

# Compute additional metrics
gavel_slowdown = compute_slowdown(gavel_submission, gavel_completion)
fcfs_slowdown = compute_slowdown(fcfs_submission, fcfs_completion)
gavel_starved = identify_starved_jobs(gavel_waiting)
fcfs_starved = identify_starved_jobs(fcfs_waiting)


# Plot Resource Utilization
plt.figure(figsize=(12, 6))
plt.plot(gavel_time, gavel_cpu_util, label='Gavel CPU Utilization', linestyle='-', marker='o', color='blue')
plt.plot(gavel_time, gavel_gpu_util, label='Gavel GPU Utilization', linestyle='-', marker='s', color='cyan')
plt.plot(fcfs_time, fcfs_cpu_util, label='FCFS CPU Utilization', linestyle='-', marker='x', color='red')
plt.plot(fcfs_time, fcfs_gpu_util, label='FCFS GPU Utilization', linestyle='-', marker='^', color='orange')
plt.xlabel("Time")
plt.ylabel("Resource Utilization")
plt.title("CPU & GPU Resource Utilization Over Time: Gavel vs FCFS")
plt.legend()
plt.grid()
plt.show()

# Print Summary Stats
print("\nGavel Bounded Slowdown Statistics")
print(pd.DataFrame.from_dict(gavel_slowdown, orient='index').describe())
print("\nFCFS Bounded Slowdown Statistics")
print(pd.DataFrame.from_dict(fcfs_slowdown, orient='index').describe())
print("\nGavel Starved Jobs:", gavel_starved)
print("\nFCFS Starved Jobs:", fcfs_starved)
