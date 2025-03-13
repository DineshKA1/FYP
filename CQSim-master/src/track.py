import re
import time
import matplotlib.pyplot as plt

class ResourceTracker:
    def __init__(self, log_file="gavelNew2.txt", total_procs=128, total_gpus=16):
        self.log_file = log_file
        self.total_procs = total_procs
        self.total_gpus = total_gpus

        self.timestamp = []
        self.cpu_available = []
        self.gpu_available = []
        self.cpu_allocation_ratio = []
        self.gpu_allocation_ratio = []

    def parse_log(self):
        """Reads the scheduler output and extracts CPU/GPU allocation information."""
        with open(self.log_file, "r") as file:
            lines = file.readlines()

        for line in lines:
            # Match time event
            time_match = re.search(r"Time: (\d+\.?\d*)", line)
            if time_match:
                current_time = float(time_match.group(1))
                
                # Match resource availability
                resource_match = re.search(r"Tot:(\d+) Idle:(\d+) Avail:(\d+)", line)
                if resource_match:
                    total_procs = int(resource_match.group(1))
                    idle_procs = int(resource_match.group(2))
                    available_procs = int(resource_match.group(3))

                    allocated_procs = total_procs - available_procs
                    cpu_alloc_ratio = allocated_procs / total_procs if total_procs > 0 else 0
                    
                    # GPU parsing: find "Job X: GPUs Required = Y"
                    gpu_match = re.search(r"Job \d+: GPUs Required = (\d+)", line)
                    allocated_gpus = int(gpu_match.group(1)) if gpu_match else 0
                    gpu_alloc_ratio = allocated_gpus / self.total_gpus if self.total_gpus > 0 else 0
                    
                    # Store values
                    self.timestamp.append(current_time)
                    self.cpu_available.append(available_procs)
                    self.gpu_available.append(self.total_gpus - allocated_gpus)  # Approximate available GPUs
                    self.cpu_allocation_ratio.append(cpu_alloc_ratio)
                    self.gpu_allocation_ratio.append(gpu_alloc_ratio)

    def plot_resource_ratios(self):
        """Plots allocation & utilization ratios over time."""
        plt.figure(figsize=(12, 6))

        # Plot allocation ratios
        plt.subplot(1, 2, 1)
        plt.plot(self.timestamp, self.cpu_allocation_ratio, label="CPU Allocation Ratio", marker='o')
        plt.plot(self.timestamp, self.gpu_allocation_ratio, label="GPU Allocation Ratio", marker='x')
        plt.xlabel("Time")
        plt.ylabel("Allocation Ratio")
        plt.title("CPU & GPU Allocation Ratios Over Time")
        plt.legend()

        # Plot resource availability
        plt.subplot(1, 2, 2)
        plt.plot(self.timestamp, self.cpu_available, label="CPU Available", marker='o', linestyle='dashed')
        plt.plot(self.timestamp, self.gpu_available, label="GPU Available", marker='x', linestyle='dashed')
        plt.xlabel("Time")
        plt.ylabel("Available Resources")
        plt.title("CPU & GPU Availability Over Time")
        plt.legend()

        plt.tight_layout()
        plt.show()

    def run(self):
        """Runs the log parser and plots results."""
        print("Analyzing resource usage from log file...")
        self.parse_log()
        self.plot_resource_ratios()

if __name__ == "__main__":
    tracker = ResourceTracker(log_file="gavelNew.txt", total_procs=128, total_gpus=16)
    tracker.run()
