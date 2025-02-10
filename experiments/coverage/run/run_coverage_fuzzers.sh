#!/bin/bash

# Define the path to run_parallel_instances.py relative to this script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fuzzer_script="$script_dir/../../../run_parallel_instances.py"

# Run SCC, STPL, and MaxMatching fuzzers in parallel for 2 hours (7200 seconds)
python3 "$fuzzer_script" SCC scc_log 5 STPL stpl_log 5 MaxMatching maxmatching_log 5 --num_iterations 100 --feedback_check_type coverage --scheduler disk --timeout 7200

# Run the next batch of fuzzers: MST, JaccardSimilarity, and BCC
python3 "$fuzzer_script" MST mst_log 5 JaccardSimilarity jaccardsimilarity_log 5 BCC bcc_log 5 --num_iterations 100 --feedback_check_type coverage --scheduler disk --timeout 7200

# Run the final batch of fuzzers: AdamicAdar, HarmonicCentrality, and MAXFV
python3 "$fuzzer_script" AdamicAdar adamicadar_log 5 HarmonicCentrality harmoniccentrality_log 5 MAXFV maxfv_log 5 --num_iterations 100 --feedback_check_type coverage --scheduler disk --timeout 7200
