import argparse
import importlib
import os
import sys
import time
import multiprocessing
import signal
from multiprocessing import Lock
import networkx as nx
import igraph

from Scheduler.RandomDiskScheduler import RandomDiskScheduler
from Scheduler.RandomMemScheduler import RandomMemScheduler
from Feedback.FeedbackTools import FeedbackTools


class RunMultipleFuzzers:
    def __init__(self, fuzzer_configs, num_iterations=60, use_multiple_graphs=False, scheduler_type="mem", timeout=None, enable_none=False):
        self.fuzzer_configs = fuzzer_configs
        self.num_iterations = num_iterations
        self.use_multiple_graphs = use_multiple_graphs
        self.scheduler_type = scheduler_type
        self.timeout = timeout
        self.enable_none = enable_none
        self.shared_lock = Lock()

    def get_fuzzer_class(self, fuzzer_name):
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

    def run_fuzzer(self, fuzzer, log_file):
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        sys.stdout = log_file
        sys.stderr = log_file

        try:
            fuzzer.run()
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    def run_instance(self, fuzzer_name, output_folder, feedback_check_type):
        fuzzer_class = self.get_fuzzer_class(fuzzer_name)
        if fuzzer_class is None:
            print(f"Error: Fuzzer {fuzzer_name} could not be found.")
            return

        # Determine the scheduler and instance folder based on the feedback type
        if feedback_check_type == "none":
            scheduler = RandomMemScheduler(start_time=time.time())
            instance_folder = None  # No folder needed for 'none' feedback check
        else:
            instance_folder = os.path.join(output_folder, f"graphs_folder_{feedback_check_type}")
            os.makedirs(instance_folder, exist_ok=True)
            if self.scheduler_type == "mem":
                scheduler = RandomMemScheduler(start_time=time.time())
            elif self.scheduler_type == "disk":
                scheduler = RandomDiskScheduler(instance_folder)
            else:
                print(f"Error: Unknown scheduler type {self.scheduler_type}")
                return

        feedback_tool = FeedbackTools(start_time=time.time(), lock=self.shared_lock)

        # Instantiate the fuzzer with the feedback_tool
        fuzzer = fuzzer_class(num_iterations=self.num_iterations,
                              use_multiple_graphs=self.use_multiple_graphs,
                              feedback_check_type=feedback_check_type,
                              scheduler=scheduler)

        # Set the feedback tool with the shared lock
        fuzzer.feedback_tool = feedback_tool

        # Determine the log file path based on feedback type
        instance_log_file_path = os.path.join(output_folder, f"{fuzzer_name.lower()}_{feedback_check_type}_log.txt")
        with open(instance_log_file_path, "a", buffering=1) as log_file:
            self.run_fuzzer(fuzzer, log_file)

    def start(self):
        print(f"Running fuzzers with networkx version: {nx.__version__}")  # Print networkx version
        print(f"igraph version: {igraph.__version__}")  # Print igraph version

        processes = []
        feedback_types = ["regular", "coverage", "combination"]

        if self.enable_none:
            feedback_types.append("none")

        for fuzzer_name, output_folder in self.fuzzer_configs:
            os.makedirs(output_folder, exist_ok=True)
            for feedback_type in feedback_types:
                p = multiprocessing.Process(target=self.run_instance, args=(
                    fuzzer_name, output_folder, feedback_type))
                processes.append(p)
                p.start()

        if self.timeout:
            time.sleep(self.timeout)
            for p in processes:
                if p.is_alive():
                    os.kill(p.pid, signal.SIGINT)

        for p in processes:
            p.join()


def main():
    parser = argparse.ArgumentParser(description="Run multiple fuzzers with different feedback types in parallel.")
    parser.add_argument("fuzzers", type=str, nargs='+', help="The names of the fuzzers to run and their respective output folders.")
    parser.add_argument("--num_iterations", type=int, default=60, help="The number of iterations the fuzzers should run.")
    parser.add_argument("--use_multiple_graphs", action="store_true", help="Use multiple graphs for the fuzzers.")
    parser.add_argument("--scheduler", type=str, default="mem", choices=["mem", "disk"], help="Scheduler type: 'mem' or 'disk'.")
    parser.add_argument("--timeout", type=int, default=None, help="Timeout in seconds for each instance.")
    parser.add_argument("--enable_none", action="store_true", help="Enable running with --feedback_check_type none using mem scheduler.")

    args = parser.parse_args()

    if len(args.fuzzers) % 2 != 0:
        print("Error: Each fuzzer should have an associated output folder.")
        return

    fuzzer_configs = [(args.fuzzers[i], args.fuzzers[i + 1]) for i in range(0, len(args.fuzzers), 2)]

    runner = RunMultipleFuzzers(
        fuzzer_configs=fuzzer_configs,
        num_iterations=args.num_iterations,
        use_multiple_graphs=args.use_multiple_graphs,
        scheduler_type=args.scheduler,
        timeout=args.timeout,
        enable_none=args.enable_none
    )
    runner.start()


if __name__ == "__main__":
    main()


## Usage
## python3 run_multiple_fuzzers.py SCC scc_log STPL stpl_log --num_iterations 100 --scheduler disk --timeout 7200
## python3 run_multiple_fuzzers.py SCC scc_log STPL stpl_log MaxMatching maxmatching_log --num_iterations 100 --scheduler disk --timeout 7200 --enable_none
