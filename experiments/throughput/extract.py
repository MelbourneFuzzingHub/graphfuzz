import os
import re
import numpy as np  

def extract_values_from_log(file_path):
    count = None
    corpus_size = None
    with open(file_path, 'r') as file:
        for line in file:
            # Search for 'count ' and extract the number after it
            count_match = re.match(r'^count\s+(\d+)', line.strip())
            if count_match:
                count = int(count_match.group(1))
            # Search for 'There were X graphs saved in the corpus.'
            corpus_match = re.match(r'^There were\s+(\d+)\s+graphs saved in the corpus.', line.strip())
            if corpus_match:
                corpus_size = int(corpus_match.group(1))
    return count, corpus_size

def main():
     # Get the current directory of this Python file
    base_dir = os.path.dirname(os.path.abspath(__file__))

    setups = ['combination', 'coverage', 'none', 'regular']

    # Iterate over each algorithm folder
    for algorithm in os.listdir(base_dir):
        algorithm_path = os.path.join(base_dir, algorithm)
        if os.path.isdir(algorithm_path):
            # Initialize dictionaries to store counts and corpus sizes for each setup
            counts = {setup: [] for setup in setups}
            corpus_sizes = {setup: [] for setup in setups}

            # Iterate over each run folder
            for run in os.listdir(algorithm_path):
                run_path = os.path.join(algorithm_path, run)
                if os.path.isdir(run_path):
                    # Process log files in the run folder
                    for log_file in os.listdir(run_path):
                        if log_file.endswith('_log.txt'):
                            # Identify the setup from the filename
                            for setup in setups:
                                if f'_{setup}_' in log_file:
                                    log_file_path = os.path.join(run_path, log_file)
                                    count, corpus_size = extract_values_from_log(log_file_path)
                                    if count is not None and corpus_size is not None:
                                        counts[setup].append(count)
                                        corpus_sizes[setup].append(corpus_size)
                                    break  # Stop checking setups if one matches
            # Calculate mean values for each setup
            print(f"Algorithm: {algorithm}")
            for setup in setups:
                if counts[setup] and corpus_sizes[setup]:
                    mean_count = np.mean(counts[setup])
                    mean_corpus_size = np.mean(corpus_sizes[setup])
                    print(f"  Setup: {setup}")
                    print(f"    Mean Count: {mean_count}")
                    print(f"    Mean Corpus Size: {mean_corpus_size}")
                else:
                    print(f"  Setup: {setup} - No data found.")
            print('\n')

if __name__ == "__main__":
    main()
