import argparse
import importlib
import os
import sys
import time
import uuid

from Scheduler.RandomDiskScheduler import RandomDiskScheduler
from Scheduler.RandomMemScheduler import RandomMemScheduler


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


def run_fuzzer(fuzzer, output_mode):
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    if output_mode == "file":
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(script_dir, "Log")
        log_id = uuid.uuid4().hex[:6]
        print(f"Log ID: {log_id}")

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file_path = os.path.join(log_dir, f"{fuzzer.__class__.__name__.lower()}_{log_id}_log.txt")
        log_file = open(log_file_path, "w", buffering=1)
        sys.stdout = log_file
        sys.stderr = log_file

    try:
        fuzzer.run()
    finally:
        if output_mode == "file":
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            log_file.close()
            print(f"Log saved to: {log_file_path}")


def main():
    parser = argparse.ArgumentParser(description="Run a specified fuzzer with given parameters.")
    parser.add_argument("fuzzer", type=str, choices=[
        "AdamicAdar", "BCC", "HarmonicCentrality", "JaccardSimilarity",
        "MAXFV", "MaxMatching", "MST", "SCC", "STPL"
    ], help="The name of the fuzzer to run.")
    parser.add_argument("--num_iterations", type=int, default=60,
                        help="The number of iterations the fuzzer should run.")
    parser.add_argument("--use_multiple_graphs", action="store_true", help="Use multiple graphs for the fuzzer.")
    parser.add_argument("--feedback_check_type", type=str, choices=["regular", "coverage", "combination", "branch", "none"],
                        default="regular", help="The type of feedback check to use: "
                                                "'regular' for standard checks, "
                                                "'coverage' for line coverage-based checks, "
                                                "'combination' for both regular and coverage, "
                                                "'branch' for branch coverage-based checks, "
                                                "'none' to disable feedback checks.")
    parser.add_argument("--output", type=str, default="console", choices=["file", "console"],
                        help="Output mode: 'file' to save the log to a file, 'console' to print to the console.")
    parser.add_argument("--scheduler", type=str, default="mem", choices=["mem", "disk"],
                        help="Scheduler type: 'mem' for RandomMemScheduler, 'disk' for RandomDiskScheduler.")
    parser.add_argument("--folder", type=str, default="graphs_folder",
                        help="Folder name for saving graphs when using RandomDiskScheduler.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout for each operation in seconds (default: 20).")

    args = parser.parse_args()

    fuzzer_class = get_fuzzer_class(args.fuzzer)
    if fuzzer_class is None:
        print(f"Error: Fuzzer {args.fuzzer} could not be found.")
        return

    if args.scheduler == "mem":
        scheduler = RandomMemScheduler(start_time=time.time())
    elif args.scheduler == "disk":
        scheduler = RandomDiskScheduler(args.folder)
    else:
        print(f"Error: Unknown scheduler type {args.scheduler}")
        return

    # Pass the timeout argument to the fuzzer instance
    fuzzer = fuzzer_class(num_iterations=args.num_iterations,
                          use_multiple_graphs=args.use_multiple_graphs,
                          feedback_check_type=args.feedback_check_type,
                          scheduler=scheduler,
                          timeout_duration=args.timeout) 

    run_fuzzer(fuzzer, args.output)


if __name__ == "__main__":
    main()
