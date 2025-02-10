# GraphFuzz Experiment Guide

This guide provides steps to run experiments for evaluating code coverage achievements, throughput, and bug discovery efficiency with the GraphFuzz fuzzing framework. Each experiment launches multiple fuzzers with different configurations.

## Code Coverage Experiment

To conduct experiments for code coverage achievements, navigate to the `GraphFuzz/experiments/coverage/run` directory and run the `run_coverage_fuzzers.sh` script as follows:

```bash
cd GraphFuzz/experiments/coverage/run  
./run_coverage_fuzzers.sh
```

### Description
- This experiment runs **9 different algorithm fuzzers** with **coverage feedback** in parallel.
- Each fuzzer has **5 trials** to ensure diverse coverage analysis.
- **Requirements**:
  - **15 CPU cores** to support parallel execution.
  - **Runtime**: Approximately **6 hours**.
  - **Output**: All output will be stored in the `GraphFuzz/experiments/coverage/run` directory.

### Summary of `run_coverage_fuzzers.sh`
The `run_coverage_fuzzers.sh` script initializes the following:
1. Runs **SCC**, **STPL**, and **MaxMatching** fuzzers in parallel for 2 hours each.
2. Runs the next batch of fuzzers: **MST**, **JaccardSimilarity**, and **BCC** in parallel for 2 hours.
3. Runs the final batch: **AdamicAdar**, **HarmonicCentrality**, and **MAXFV** in parallel for 2 hours.

Each fuzzer uses a disk scheduler and coverage-based feedback.

---

## Throughput Experiment

To conduct experiments focused on throughput, navigate to the `GraphFuzz/experiments/throughput/run` directory and run the `run.sh` script as follows:

```bash
cd GraphFuzz/experiments/throughput/run  
./run_throughput.sh
```

### Description
- This experiment runs **9 different algorithm fuzzers** with varying configurations, similar to the code coverage experiment.
- Each fuzzer has **5 trials**.
- Each algorithm fuzzer is configured to test **no feedback**, **algorithm-specific feedback**, **line coverage feedback**, and a **combination of algorithm-specific feedback and line coverage feedback**.
- **Requirements**:
  - **12 CPU cores** are required to handle parallel execution.
  - **Runtime**: Approximately **30 hours**.
  - **Output**: Results and logs will be stored in the `GraphFuzz/experiments/throughput/run` directory.

### Summary of `run_throughput.sh`
The `run_throughput.sh` script executes the following steps for each fuzzer, with configurations for four types of feedback: no feedback, algorithm-specific feedback, line coverage feedback, and a combination of algorithm-specific and line coverage feedback.

1. Runs **SCC**, **STPL**, and **MaxMatching** fuzzers in parallel, each for 2 hours. The output is stored in unique log folders for each trial (e.g., `scc_log_1`, `scc_log_2`, etc.).
2. Runs the next batch: **MST**, **JaccardSimilarity**, and **MAXFV** in parallel for 2 hours, repeating for each trial.
3. Runs the final batch: **AdamicAdar**, **HarmonicCentrality**, and **BCC** in parallel for 2 hours across all trials.

---

## Bug Analysis

After running the experiments, bug-related information can be found in the log files generated in the respective `coverage` and `throughput` directories as `.txt` files. Please note:
- Bug data will not be automatically clustered or categorized. You will need to manually review the log files and the specific bug-triggering data files for detailed analysis.

---

## Bug Report

For details, please see the [bug report](bug_report/Bug_Finding_Result.pdf).

---
