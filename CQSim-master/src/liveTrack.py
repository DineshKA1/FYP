import csv
import re
import matplotlib.pyplot as plt

LOG_FILE = "cqsim_job_allocation.csv"
GAVEL_LOG_FILE = "gavelNew2.txt"

TOTAL_CPUS = 128  # Total available CPU cores in the simulation
TOTAL_GPUS = 16   # Total available GPUs in the simulation

# Dictionaries to store data
job_allocations = {}
time_series = []  # Stores (sim_time, cpu_alloc, gpu_alloc)

def parse_gavel_log():
    
    try:
        with open(GAVEL_LOG_FILE, "r") as file:
            lines = file.readlines()

        cpu_alloc = 0  # Default CPU allocation
        latest_time = 0  # Track latest simulation time

        for line in lines:
            # Extract simulation time
            time_match = re.search(r"Time: (\d+\.?\d*)", line)
            if time_match:
                latest_time = float(time_match.group(1))

            # Extract GPU allocation
            gpu_match = re.search(r"Job (\d+): GPUs Required = (\d+)", line)
            if gpu_match:
                job_id = int(gpu_match.group(1))
                gpu_alloc = int(gpu_match.group(2))
                job_allocations[job_id] = {"start_time": latest_time, "cpu_alloc": cpu_alloc, "gpu_alloc": gpu_alloc, "end_time": None}

            # Extract job finish times
            finish_match = re.search(r"\[Finish\] (\d+)", line)
            if finish_match:
                job_id = int(finish_match.group(1))
                if job_id in job_allocations:
                    job_allocations[job_id]["end_time"] = latest_time  # Record completion time

            # Extract CPU allocation from system state
            cpu_match = re.search(r"Tot:(\d+) Idle:(\d+) Avail:(\d+)", line)
            if cpu_match:
                total_procs = int(cpu_match.group(1))
                available_procs = int(cpu_match.group(3))
                cpu_alloc = total_procs - available_procs  # Updated CPU allocation

                # Assign the latest CPU allocation to jobs
                for job_id in job_allocations:
                    if job_allocations[job_id]["end_time"] is None:  # If job is still running
                        job_allocations[job_id]["cpu_alloc"] = cpu_alloc

                # Track time-series CPU & GPU usage
                total_gpu_alloc = sum(job["gpu_alloc"] for job in job_allocations.values())
                time_series.append((latest_time, cpu_alloc, total_gpu_alloc))

        # Compute job resource allocation ratios
        for job_id, data in job_allocations.items():
            data["cpu_ratio"] = data["cpu_alloc"] / TOTAL_CPUS if TOTAL_CPUS > 0 else 0
            data["gpu_ratio"] = data["gpu_alloc"] / TOTAL_GPUS if TOTAL_GPUS > 0 else 0

    except FileNotFoundError:
        print(f"Error: `{GAVEL_LOG_FILE}` not found.")
        return

def save_to_csv():
    
    with open(LOG_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Job_ID", "Start_Time", "End_Time", "CPU_Allocated", "GPU_Allocated", "CPU_Ratio", "GPU_Ratio"])  # Header
        '''
        job_count = 0
        for job_id, data in sorted(job_allocations.items()):  #sort by Job_ID
            if job_count >= 100:  #stop after processing the first 100 jobs
                break
            writer.writerow([
                job_id, data["start_time"], data["end_time"], 
                data["cpu_alloc"], data["gpu_alloc"], f"{data['cpu_ratio']:.4f}", f"{data['gpu_ratio']:.4f}"
            ])
            job_count += 1 '''
        
        for job_id, data in sorted(job_allocations.items()):  # Sort by Job_ID
            writer.writerow([
                job_id, data["start_time"], data["end_time"], 
                data["cpu_alloc"], data["gpu_alloc"], f"{data['cpu_ratio']:.4f}", f"{data['gpu_ratio']:.4f}"
            ])
            

    print(f"Job allocations & resource usage saved to `{LOG_FILE}`")

def plot_time_series():
    """Generates time-series plots of CPU/GPU allocation over simulation time."""
    sim_times = [t[0] for t in time_series]
    cpu_allocs = [t[1] for t in time_series]
    gpu_allocs = [t[2] for t in time_series]

    plt.figure(figsize=(12, 6))
    plt.plot(sim_times, cpu_allocs, label="CPU Allocated", color='blue', marker='o', linestyle='dashed')
    plt.plot(sim_times, gpu_allocs, label="GPU Allocated", color='green', marker='x', linestyle='dashed')

    plt.xlabel("Simulation Time")
    plt.ylabel("Resources Allocated")
    plt.title("Time-Series of CPU & GPU Allocations")
    plt.legend()
    plt.grid()
    plt.show()

if __name__ == "__main__":
    print("Parsing `gavelNew.txt` for job allocations")
    parse_gavel_log()
    save_to_csv()
    print("Generating time-series graphs")
    plot_time_series()
