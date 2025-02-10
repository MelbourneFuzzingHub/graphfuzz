import argparse
import importlib
import os
import sys
import time
import uuid
import multiprocessing
import signal
from multiprocessing import Lock

from Scheduler.RandomDiskScheduler import RandomDiskScheduler
from Scheduler.RandomMemScheduler import RandomMemScheduler

from Feedback.FeedbackTools import FeedbackTools

def get_fuzzer_class(fuzzer_name):
    module_name = f"Fuzzer.{fuzzer_name}Fuzzer"
    class_name = f"{fuzzer_name}Fuzzer"
    try:
        module = importlib.import_module(module_name)
        fuzzer_class = getattr(module, class_name)
        return fuzzer_class
    except (ModuleNotFoundError, AttributeError) as e:
        print(f"Error: Could not find fuzzer class {class_name} in module {module_name}")
        print(e)
        return None


def run_fuzzer(fuzzer, log_file):
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    sys.stdout = log_file
    sys.stderr = log_file

    try:
        fuzzer.run()
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr


def run_instance(fuzzer_name, output_folder, num_iterations, use_multiple_graphs, feedback_check_type, scheduler_type, instance_index, shared_lock):
    fuzzer_class = get_fuzzer_class(fuzzer_name)
    if fuzzer_class is None:
        print(f"Error: Fuzzer {fuzzer_name} could not be found.")
        return

    instance_folder = os.path.join(output_folder, f"graphs_folder_{instance_index}")
    os.makedirs(instance_folder, exist_ok=True)

    feedback_tool = FeedbackTools(start_time=time.time(), lock=shared_lock)

    if scheduler_type == "mem":
        scheduler = RandomMemScheduler(start_time=time.time())
    elif scheduler_type == "disk":
        scheduler = RandomDiskScheduler(instance_folder)
    else:
        print(f"Error: Unknown scheduler type {scheduler_type}")
        return

    # Instantiate the fuzzer without the feedback_tool argument
    fuzzer = fuzzer_class(num_iterations=num_iterations,
                          use_multiple_graphs=use_multiple_graphs,
                          feedback_check_type=feedback_check_type,
                          scheduler=scheduler)

    # Set the feedback tool with the shared lock
    fuzzer.feedback_tool = feedback_tool

    instance_log_file_path = os.path.join(output_folder, f"{fuzzer_name.lower()}_{instance_index}_log.txt")
    with open(instance_log_file_path, "a", buffering=1) as log_file:
        run_fuzzer(fuzzer, log_file)


def main():
    parser = argparse.ArgumentParser(description="Run specified fuzzers with given parameters in multiple instances.")
    parser.add_argument("fuzzers", type=str, nargs='+',
                        help="The names of the fuzzers to run, followed by their respective output folders and number of instances. Example: SCC scc_log 5 STPL stpl_log 5.")
    parser.add_argument("--num_iterations", type=int, default=60,
                        help="The number of iterations the fuzzers should run.")
    parser.add_argument("--use_multiple_graphs", action="store_true", help="Use multiple graphs for the fuzzers.")
    parser.add_argument("--feedback_check_type", type=str, choices=["regular", "coverage", "combination", "none"],
                        default="regular", help="The type of feedback check to use: "
                                                "'regular' for standard checks, "
                                                "'coverage' for coverage-based checks, "
                                                "'combination' for both, "
                                                "'none' to disable feedback checks.")
    parser.add_argument("--scheduler", type=str, default="mem", choices=["mem", "disk"],
                        help="Scheduler type: 'mem' for RandomMemScheduler, 'disk' for RandomDiskScheduler.")
    parser.add_argument("--timeout", type=int, default=None, help="Timeout in seconds for each instance.")

    args = parser.parse_args()

    # Ensure that fuzzers, output folders, and instance numbers are in correct groups
    if len(args.fuzzers) % 3 != 0:
        print("Error: Each fuzzer should have an associated output folder and number of instances.")
        return

    # Parse the fuzzer configurations
    fuzzer_configs = []
    for i in range(0, len(args.fuzzers), 3):
        fuzzer_name = args.fuzzers[i]
        output_folder = args.fuzzers[i+1]
        num_instances = int(args.fuzzers[i+2])
        fuzzer_configs.append((fuzzer_name, output_folder, num_instances))

    # Create a shared lock for all fuzzers
    shared_lock = Lock()

    # Run multiple fuzzers in parallel with their respective instances
    processes = []
    for fuzzer_name, output_folder, num_instances in fuzzer_configs:
        os.makedirs(output_folder, exist_ok=True)
        for i in range(1, num_instances + 1):
            p = multiprocessing.Process(target=run_instance, args=(
                fuzzer_name, output_folder, args.num_iterations, args.use_multiple_graphs,
                args.feedback_check_type, args.scheduler, i, shared_lock))
            processes.append(p)
            p.start()

    if args.timeout:
        # Allow processes to run for the given timeout, then send SIGINT to each
        time.sleep(args.timeout)
        for p in processes:
            if p.is_alive():
                os.kill(p.pid, signal.SIGINT)

    for p in processes:
        p.join()


if __name__ == "__main__":
    main()



## Usage
## python3 run_parallel_instances.py SCC scc_log 5 --num_iterations 100 --feedback_check_type coverage --scheduler disk --timeout 20
## python3 run_parallel_instances.py SCC scc_log 5 STPL stpl_log 5 --num_iterations 100 --feedback_check_type coverage --scheduler disk --timeout 20
