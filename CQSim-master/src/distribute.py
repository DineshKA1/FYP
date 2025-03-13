import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def redistribute_job_arrivals(input_file, output_file, distribution='poisson', time_scale=None, plot=True):
    """
    Redistribute job arrival times in the provided workload format.
    
    Parameters:
    -----------
    input_file : str
        Path to the original workload file
    output_file : str
        Path to save the modified workload file
    distribution : str
        Type of distribution ('uniform', 'poisson', 'normal', 'exponential')
    time_scale : int or None
        Maximum time for the new distribution. If None, will use the range of original submissions.
    plot : bool
        Whether to create comparison plots
    """
    # Read the header lines
    header_lines = []
    with open(input_file, 'r') as f:
        for line in f:
            if line.startswith(';'):
                header_lines.append(line)
            else:
                break
    
    # Read the job data
    jobs = []
    with open(input_file, 'r') as f:
        for line in f:
            if not line.startswith(';'):
                fields = line.strip().split()
                if len(fields) > 2:  # Ensure we have at least job ID and submission time
                    jobs.append(fields)
    
    # Extract submission times and sort jobs
    submit_times = [int(job[1]) for job in jobs]
    min_time = min(submit_times)
    max_time = max(submit_times)
    
    # If time_scale not provided, use the original range
    if time_scale is None:
        time_scale = max_time - min_time
    
    # Generate new arrival times based on chosen distribution
    num_jobs = len(jobs)
    
    if distribution == 'uniform':
        # Uniform distribution - evenly spaced
        new_arrivals = np.linspace(0, time_scale, num_jobs)
        
    elif distribution == 'poisson':
        # Poisson process - exponentially distributed inter-arrival times
        mean_interval = time_scale / num_jobs
        intervals = np.random.exponential(mean_interval, num_jobs)
        new_arrivals = np.cumsum(intervals)
        
    elif distribution == 'normal':
        # Normal distribution centered in the middle
        new_arrivals = np.random.normal(time_scale/2, time_scale/6, num_jobs)
        new_arrivals = np.sort(np.maximum(new_arrivals, 0))
        
    elif distribution == 'exponential':
        # Exponential distribution - more jobs early, fewer later
        new_arrivals = np.random.exponential(time_scale/3, num_jobs)
        new_arrivals = np.sort(new_arrivals)
        
    else:
        raise ValueError(f"Unknown distribution: {distribution}")
    
    # Create mapping of old jobs to new arrival times
    # Use the original job order to replace the submission times
    sorted_indices = np.argsort(submit_times)
    
    # Replace submission times in jobs data
    for i, idx in enumerate(sorted_indices):
        jobs[idx][1] = str(int(new_arrivals[i]))
    
    # Write modified workload to output file
    with open(output_file, 'w') as f:
        # Write header lines
        for header in header_lines:
            f.write(header)
        
        # Write job entries
        for job in jobs:
            f.write(' '.join(job) + '\n')
    
    if plot:
        # Plot comparison of original vs new arrival distributions
        plt.figure(figsize=(12, 6))
        
        plt.subplot(1, 2, 1)
        plt.hist(submit_times, bins=50, color='blue', alpha=0.7)
        plt.title('Original Job Submission Times')
        plt.xlabel('Time')
        plt.ylabel('Number of Jobs')
        
        plt.subplot(1, 2, 2)
        plt.hist([int(job[1]) for job in jobs], bins=50, color='green', alpha=0.7)
        plt.title(f'Modified Job Submission Times ({distribution.capitalize()})')
        plt.xlabel('Time')
        
        plt.tight_layout()
        plt.savefig(f'{output_file}_comparison.png')
        plt.close()
        
        print(f"Modified workload saved to {output_file}")
        print(f"Comparison plot saved to {output_file}_comparison.png")

# Example usage
# redistribute_job_arrivals('your_workload.swf', 'modified_workload.swf', 'poisson')