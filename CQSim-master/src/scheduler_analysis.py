import matplotlib.pyplot as plt

def parse_gavel_log(file_path, default_runtime=100):
    """
    Parses the Gavel log file to extract job submission, start, and finish times.
    Adds a default runtime for missing finish times.
    """
    job_details = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
        current_time = None

        for i, line in enumerate(lines):
            #extract current simulation time
            if "Time:" in line:
                try:
                    current_time = float(line.split(":")[-1].strip())
                except ValueError:
                    current_time = None
            
            #detect job submission
            if "[Submit]" in line:
                job_id = int(line.split()[-1])
                submission_time = current_time
                start_time = None
                finish_time = None

                #look ahead to find start and finish times
                for j in range(i + 1, len(lines)):
                    if "[Start]" in lines[j] and str(job_id) in lines[j]:
                        try:
                            start_time = float(lines[j - 3].split(":")[-1].strip())
                        except ValueError:
                            start_time = None
                    if "[Finish]" in lines[j] and str(job_id) in lines[j]:
                        try:
                            finish_time = float(lines[j - 3].split(":")[-1].strip())
                        except ValueError:
                            finish_time = None
                        break

                #assign default finish time if missing
                if finish_time is None and start_time is not None:
                    finish_time = start_time + default_runtime

                job_details.append({
                    "job_id": job_id,
                    "submission_time": submission_time,
                    "start_time": start_time,
                    "finish_time": finish_time,
                })

    #log parsed details for debugging
    print(f"Parsed {len(job_details)} jobs from {file_path}. Sample: {job_details[:5]}")
    return job_details




def plot_gantt_chart(job_details, algorithm_name):
    """
    Generates a Gantt chart for job execution.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    for job in job_details:
        start = job["start_time"]
        end = job["finish_time"]
        if start is not None and end is not None:
            ax.barh(job["job_id"], end - start, left=start, color='skyblue', edgecolor='black')

    ax.set_xlabel("Time")
    ax.set_ylabel("Jobs")
    ax.set_title(f"Gantt Chart for {algorithm_name}")
    plt.show()

def calculate_average_turnaround_time(job_details):
    """
    Calculates the average turnaround time for the given jobs.
    """
    turnaround_times = [
        job["finish_time"] - job["submission_time"]
        for job in job_details
        if job["finish_time"] is not None and job["submission_time"] is not None
    ]
    if not turnaround_times:
        print("No valid turnaround times found! Check the input data.")
    else:
        print("Turnaround times:", turnaround_times)
    
    return sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0


def plot_average_turnaround(fcfs_file, gavel_file):
    """
    Plots a bar chart comparing average turnaround time between FCFS and GavelScheduling.
    """
    fcfs_jobs = parse_gavel_log(fcfs_file)
    gavel_jobs = parse_gavel_log(gavel_file)

    avg_turnaround_fcfs = calculate_average_turnaround_time(fcfs_jobs)
    avg_turnaround_gavel = calculate_average_turnaround_time(gavel_jobs)

    if avg_turnaround_fcfs == 0 or avg_turnaround_gavel == 0:
        print("Warning: One or both algorithms have no valid turnaround times. Skipping plot.")
        return

    algorithms = ["FCFS", "GavelScheduling"]
    avg_turnarounds = [avg_turnaround_fcfs, avg_turnaround_gavel]

    plt.figure(figsize=(8, 5))
    plt.bar(algorithms, avg_turnarounds, color=['skyblue', 'orange'], edgecolor='black')
    plt.xlabel("Algorithms")
    plt.ylabel("Average Turnaround Time")
    plt.title("Comparison of Average Turnaround Time")
    plt.show()


#paths to algo log files
fcfs_file_path = "C:\Users\Dino\Documents\GitHub\CQFYP\CQSim-master\src\FCFS.txt"
gavel_file_path = "C:\Users\Dino\Documents\GitHub\CQFYP\CQSim-master\src\Gavel.txt"

#generate the Gantt chart for GavelScheduling
gavel_jobs = parse_gavel_log(gavel_file_path)
plot_gantt_chart(gavel_jobs, "GavelScheduling")

#compare average turnaround times for FCFS and GavelScheduling
plot_average_turnaround(fcfs_file_path, gavel_file_path)
