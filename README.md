# GraphFuzz

## Configuration Details

- **Operating System:** Compatible with Ubuntu 22.04.
- **Python Version:** Requires Python 3.10.

## Codebase Architecture

### Standard Directory Structure

    .
    ├── Generator                  # Responsible for the initial generation of corpus graphs.
    │   ├── SmokeGenerator         # Facilitates the generation of various graph types.
    │   └── CustomGenerator        # Crafts specific graph types tailored to the Algorithm Under Test.
    ├── Scheduler                  # Selects graphs from the corpus for mutation.
    │   ├── RandomMemScheduler     # Randomly selects, keeping the corpus in memory.
    │   ├── RandomDiskScheduler    # Randomly selects, storing the corpus on disk.
    ├── Mutator                    # Implements graph mutations.
    │   ├── SimpleMutator          # Executes fundamental mutations.
    │   └── ExtendedMutator        # Conducts complex mutation strategies.
    ├── Feedback                   # Accumulates information to facilitate the storage of test cases.
    ├── Tester                     # Carries out the graph testing process.
    ├── Fuzzer                     # Coordinates the interactions between the various components above.
    ├── Log                        # Stores detailed logs and captures bug-triggering graph instances.
    ├── Main.py                    # Script to initialize and execute the fuzzer.
    ├── BaseFuzzer.py              # Abstract base class for all fuzzers.
    ├── run_multiple_fuzzers.py    # Script to run multiple fuzzers with different feedback types in parallel.
    ├── run_parallel_instances.py  # Script to run multiple instances of fuzzers concurrently with various configurations.
    ├── requirements.txt           # Lists dependencies for project setup.
    └── README.md                  # Provides project documentation and usage instructions.

## Running the Fuzzer

### Installation

Before running the fuzzer, you need to install the necessary dependencies. These are listed in the `requirements.txt` file. To install them, run the following command in your terminal:

```bash
pip install -r requirements.txt
```

### Executing the Fuzzer

```bash
python3 main.py <fuzzer_name> --num_iterations <num_iterations> --use_multiple_graphs --feedback_check_type <feedback_check_type> --scheduler <disk/memory> --output <output_mode>
```

In this command, replace `<fuzzer_name>` with one of the available fuzzer names, for instance: `AdamicAdar`, `BCC`, `HarmonicCentrality`, `JaccardSimilarity`, `MAXFV`, `MaxMatching`, `MST`, `SCC`, `STPL`.

Optional arguments:
- `--num_iterations <iterations>`: Set the number of iterations (default: 100).
- `--use_multiple_graphs`: Use multiple graphs for the fuzzer. If excluded, the fuzzer will start with one graph containing a single node.
- `--feedback_check_type <feedback_type>`: Specify the type of feedback to use:
  - `regular`: Algorithm-Specific checks.
  - `coverage`: Line coverage-based checks.
  - `combination`: Both `regular` and `coverage` checks.
  - `branch`: Branch coverage-based checks.
  - `none`: Disable feedback checks.
- `--scheduler <disk/mem>`: Choose the scheduler type:
  - `mem`: Use RandomMemScheduler to keep graphs in memory.
  - `disk`: Use RandomDiskScheduler to save graphs to disk.
- `--folder <folder>`: Specify the folder to save graphs when using disk scheduler (default: `graphs_folder`).
- `--output <output_mode>`: Choose the output mode:
  - `file`: Save logs to a file.
  - `console`: Print logs to the console (default: `console`).
- `--timeout <timeout>`: Set a timeout for each operation in seconds (default: 20 seconds).

Additionally, you can execute `python3 main.py -h` to view more details and options available for running the fuzzers.

Example usage:
```bash
python3 main.py SCC --num_iterations 100 --feedback_check_type regular --output file

python3 main.py SCC --num_iterations 100 --feedback_check_type coverage --output console --scheduler disk --folder ./graphs_folder
```

### Logging

The fuzzer will produce a diverse set of graphs stored in a `.pkl` file within the `Corpus` directory. The `Log` directory will contain the detailed execution logs, as well as any graphs that may exhibit bugs if any are discovered.

### Experiment Details

For instructions on conducting experiments, please refer to the [experiments README](experiments/README.md).
