import os
import signal
import sys
import time
import threading
from abc import ABC, abstractmethod

import networkx as nx
from Feedback.FeedbackTools import FeedbackTools
from Mutator.ExtendedMutator import ExtendedMutator
from Scheduler.RandomMemScheduler import RandomMemScheduler
from Utils.FileUtils import save_exception_graphs, update_coveragerc
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError


class BaseFuzzer(ABC):
    def __init__(self, num_iterations=60, use_multiple_graphs=False,
                 feedback_check_type="regular", scheduler=None, timeout_duration=20):
        self.corpus_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Corpus_Data')
        self.corpus_path = os.path.join(self.corpus_dir, f'{self.get_corpus_name()}.pkl')
        if not os.path.exists(self.corpus_dir):
            os.makedirs(self.corpus_dir)
        self.num_iterations = num_iterations
        self.use_multiple_graphs = use_multiple_graphs
        self.feedback_check_type = feedback_check_type
        update_coveragerc()
        self.start_time = time.time()
        self.feedback_tool = FeedbackTools(start_time=self.start_time)
        self.total_bug_counts = {}
        self.num_graphs = 0
        self.count = 0
        self.scheduler = scheduler or RandomMemScheduler(start_time=self.start_time)
        self.timeout_duration = timeout_duration
        self.stop_fuzzing = threading.Event()  # Use a threading event to handle stopping the fuzzing process

    def _timeout_handler(self, signum, frame):
        raise TimeoutError("Test execution exceeded the time limit")

    def process_test_results_with_timeout(self, mutated_graph, tester, first_occurrence_times, total_bug_counts, timestamp):
        """Wrapper method to add a timeout around process_test_results using ThreadPoolExecutor."""
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.process_test_results, mutated_graph, tester, first_occurrence_times, total_bug_counts, timestamp)
            
            try:
                # Wait for the process to complete or raise a timeout
                future.result(timeout=self.timeout_duration)
                return True  # Success, no timeout
            except FutureTimeoutError:  # Catch TimeoutError from futures
                exception_message = f"Timeout Error: Exceeded {self.timeout_duration} seconds."
                if exception_message not in self.feedback_tool.other_exceptions:
                    self.feedback_tool.other_exceptions.add(exception_message)
                    self.feedback_tool.exception_graphs[mutated_graph] = exception_message
                print(f"Timeout occurred while processing graph at {timestamp} seconds.")
                return False  # Timeout occurred
            except Exception as e:
                # Handle other exceptions from the process
                exception_message = f"Error: {str(e)}"
                if exception_message not in self.feedback_tool.other_exceptions:
                    self.feedback_tool.other_exceptions.add(exception_message)
                    self.feedback_tool.exception_graphs[mutated_graph] = exception_message
                print(f"Error occurred while processing graph at {timestamp} seconds.")
                return False  # Some other error occurred


    def regular_feedback_check(self, mutated_graph):
        return self.feedback_tool.is_new_and_interesting(mutated_graph, self.executor, self.interesting_check)

    def coverage_feedback_check(self, mutated_graph):
        return self.feedback_tool.is_new_and_interesting_coverage_updated(mutated_graph, self.executor)

    def combination_feedback_check(self, mutated_graph):
        if self.feedback_tool.is_new_and_interesting(mutated_graph, self.executor, self.interesting_check):
            return True
        elif self.feedback_tool.is_new_and_interesting_coverage_updated(mutated_graph, self.executor):
            return True
        return False

    def no_feedback_check(self, mutated_graph):
        return False  # Always return False to indicate no feedback check is needed

    def branch_coverage_feedback_check(self, mutated_graph):
        return self.feedback_tool.is_new_branch_triggered(mutated_graph, self.executor)

    def perform_feedback_checks(self, mutated_graph):
        if self.feedback_check_type == "regular":
            return self.regular_feedback_check(mutated_graph)
        elif self.feedback_check_type == "coverage":
            return self.coverage_feedback_check(mutated_graph)
        elif self.feedback_check_type == "combination":
            return self.combination_feedback_check(mutated_graph)
        elif self.feedback_check_type == "none":
            return self.no_feedback_check(mutated_graph)
        elif self.feedback_check_type == "branch":
            return self.branch_coverage_feedback_check(mutated_graph)
        else:
            raise ValueError(f"Unknown feedback check type: {self.feedback_check_type}")

    def default_interesting_check(self, result):
        if isinstance(result, int):
            return result
        elif isinstance(result, (list, set)):
            if all(isinstance(x, (set, frozenset)) for x in result):
                sizes = [len(component) for component in result]
                return max(sizes) if sizes else 0
            elif all(isinstance(x, tuple) and len(x) == 3 for x in result):
                return max(result, key=lambda x: x[2])[2] if result else 0
        elif isinstance(result, dict):
            return len(result)
        elif isinstance(result, nx.Graph):  # Check if result is a networkx Graph (MST case)
            total_weight = sum(data.get('weight', 1) for u, v, data in result.edges(data=True))
            num_edges = result.number_of_edges()
            return total_weight, num_edges
        else:
            raise ValueError(f"Unknown result type: {type(result)}")

    def interesting_check(self, result):
        # Check if the user has defined their own interesting_check method
        if hasattr(self, '_user_interesting_check'):
            return self._user_interesting_check(result)
        else:
            return self.default_interesting_check(result)

    def set_interesting_check(self, func):
        self._user_interesting_check = func

    @abstractmethod
    def get_corpus_name(self):
        pass

    @abstractmethod
    def executor(self, G):
        pass

    @abstractmethod
    def get_tester(self):
        pass

    @abstractmethod
    def create_single_graph(self):
        pass

    @abstractmethod
    def create_multiple_graphs(self):
        pass

    @abstractmethod
    def process_test_results(self, mutated_graph, tester, first_occurrence_times, total_bug_counts, timestamp):
        pass

    def signal_handler(self, sig, frame):
        print('Ctrl+C pressed, finalizing...')
        self.stop_fuzzing.set()  # Set the event to stop the fuzzing loop
        self.finalize_process()
        sys.exit(0)

    def finalize_process(self):
        print('Finalizing process...')
        print(f'count {self.count}')
        print(f"There were {self.num_graphs} graphs saved in the corpus.")
        print(f'Time spent: {round((time.time() - self.start_time) / 60, 3)} minutes.')
        print(f'Exception: {self.feedback_tool.exception_graphs}')
        if self.feedback_tool.exception_graphs:
            save_exception_graphs(self.feedback_tool.exception_graphs, self.get_corpus_name())
        print("Total Bugs Found:")
        for category, total in self.total_bug_counts.items():
            print(f"{category}: {total}")
        print("Checking completed.")

    def create_initial_graphs(self):
        if self.use_multiple_graphs:
            return self.create_multiple_graphs()
        else:
            return self.create_single_graph()

    def run(self):
        generated_graphs = self.create_initial_graphs()
        print(f"Loaded {len(generated_graphs)} valid graphs.")

        feedback_tool = self.feedback_tool
        scheduler = self.scheduler
        scheduler.add_to_corpus(generated_graphs)
        mutator = ExtendedMutator(scheduler)
        tester = self.get_tester()

        total_bug_counts = self.total_bug_counts
        first_occurrence_times = {}

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Perform feedback check once at the beginning on the initial graphs
        print("Performing initial feedback checks...")
        for graph in generated_graphs:
            self.num_graphs += 1
            if self.perform_feedback_checks(graph):
                print(f"Initial feedback check passed for graph {self.num_graphs}.")

        while not self.stop_fuzzing.is_set():  # Use the event to check whether to continue
            graph = scheduler.get_graph()

            for i in range(self.num_iterations):
                if self.stop_fuzzing.is_set():  # Check if we need to stop mid-iteration
                    break

                mutated_graph = mutator.stacked_mutate(graph.copy())
                self.count += 1

                timestamp = time.time() - self.start_time
                # Call the timeout-wrapped version of process_test_results
                result_success = self.process_test_results_with_timeout(mutated_graph, tester, first_occurrence_times, total_bug_counts, timestamp)

                # Only perform the feedback check if the process was successful (no timeout or error)
                if result_success:
                    if self.perform_feedback_checks(mutated_graph):
                        self.num_graphs += 1
                        scheduler.add_to_corpus(mutated_graph)
                        graph = mutated_graph

        print("Fuzzing stopped. Good bye!")
        self.finalize_process()
