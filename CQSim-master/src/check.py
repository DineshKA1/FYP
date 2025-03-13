import pandas as pd

# Load file with flexible whitespace handling
workload_df = pd.read_csv("/Users/dinesh/Desktop/new/CQFYP/CQSim-master/src/new.swf", 
                          delim_whitespace=True, header=None, dtype=str)

# Print the first few lines to check structure
print(workload_df.head())
