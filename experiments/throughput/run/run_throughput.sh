#!/bin/bash

# Number of repetitions
num_runs=5

# Define the path to run_multiple_fuzzers.py relative to this script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fuzzer_script="$script_dir/../../../run_multiple_fuzzers.py"

# Loop through each run
for i in $(seq 1 $num_runs); do
    echo "Starting run $i..."

    # Run SCC, STPL, and MaxMatching fuzzers in parallel
    python3 "$fuzzer_script" SCC scc_log_$i STPL stpl_log_$i MaxMatching maxmatching_log_$i --num_iterations 100 --scheduler disk --timeout 7200 --enable_none

    # Run the next batch of fuzzers: MST, JaccardSimilarity, and MAXFV
    python3 "$fuzzer_script" MST mst_log_$i JaccardSimilarity jaccardsimilarity_log_$i MAXFV maxfv_log_$i --num_iterations 100 --scheduler disk --timeout 7200 --enable_none

    # Run the final batch of fuzzers: AdamicAdar, HarmonicCentrality, and BCC
    python3 "$fuzzer_script" AdamicAdar adamicadar_log_$i HarmonicCentrality harmoniccentrality_log_$i BCC bcc_log_$i --num_iterations 100 --scheduler disk --timeout 7200 --enable_none

    echo "Completed run $i."
done
