import pandas as pd
import os

# File paths
files = ['results_cp.csv', 'results_cp_ver2.csv', 'results_cp_ver3.csv']
output_file = 'merged_results.csv'

# Read all CSV files
dfs = []
for file in files:
    if os.path.exists(file):
        df = pd.read_csv(file)
        dfs.append(df)
    else:
        print(f"Warning: File {file} not found")
        exit(1)

# Combine dataframes
combined_df = pd.concat(dfs, ignore_index=True)

# Group by n and k to calculate statistics
result = combined_df.groupby(['n', 'k']).agg({
    'cost': ['min', 'max', 'mean'],
    'running_time': 'mean'
}).reset_index()

# Flatten column names
result.columns = ['n', 'k', 'cost_min', 'cost_max', 'cost_avg', 'time_avg']

# Round numerical columns to 2 decimal places for readability
result['cost_min'] = result['cost_min'].round(1)
result['cost_max'] = result['cost_max'].round(1)
result['cost_avg'] = result['cost_avg'].round(1)
result['time_avg'] = result['time_avg'].round(8)

# Save to CSV
result.to_csv(output_file, index=False)
print(f"Output saved to {output_file}")