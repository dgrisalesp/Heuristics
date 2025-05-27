import os
import glob
import time

def mean(lst):
    return sum(lst) / len(lst) if lst else 0
# List of test files (assuming they're in a 'data' directory)
test_files = [
    "Data_40_Salidas_composición_zonas_heterogéneas.xlsx",
    "Data_40_Salidas_composición_zonas_homogéneas.xlsx",
    "Data_60_Salidas_composición_zonas_heterogéneas.xlsx",
    "Data_60_Salidas_composición_zonas_homogéneas.xlsx",
    "Data_80_Salidas_composición_zonas_heterogéneas.xlsx",
    "Data_80_Salidas_composición_zonas_homogéneas.xlsx",
    
    
]

# Or alternatively, you can automatically find all Excel files in your data directory:
# test_files = glob.glob('../data/pedidos_*.xlsx')


# Run the algorithm for each test file

times_simmulated_annealing = []
times_constructive = []

for input_file in test_files:
    
    
    # Print status
    print(f"\nProcessing {input_file}...")
    
    # Run the algorithm
    try:
        # Using subprocess to run the command
        import subprocess
        # start_time = time.time()
        # subprocess.run(['py', 'main.py', input_file], check=True)
        # subprocess.run(['py', 'simmulated_annealing.py', input_file], check=True)
        # times_simmulated_annealing.append(time.time() - start_time)
        # print(times_simmulated_annealing[-1])
        # start_time = time.time()
        # times_constructive.append(time.time() - start_time)
        # print(times_constructive[-1])
        # subprocess.run(['py', 'lo.py', input_file], check=True)
        # subprocess.run(['py', 'ils.py', input_file], check=True)
        subprocess.run(['py', 'genetic_algorithms.py', input_file], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error processing {input_file}: {e}")
    except Exception as e:
        print(f"Unexpected error with {input_file}: {e}")

print("Simmulated Annealing Times:", mean(times_simmulated_annealing))
print("Constructive Times:", mean(times_constructive))
print("\nAll test files processed!")