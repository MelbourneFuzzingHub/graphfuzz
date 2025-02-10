import datetime
import importlib
import io
import json
import re
import sys
import time
import coverage
import networkx as nx
import threading
from multiprocessing import Lock

def get_executed_lines(cov):
    """Retrieve executed lines from coverage data."""
    executed_lines = set()
    for filename in cov.get_data().measured_files():
        lines = cov.get_data().lines(filename)
        if lines:
            for line in lines:
                executed_lines.add((filename, line))
    return executed_lines

def get_executed_branches(cov):
    """Retrieve executed branches (arcs) from coverage data."""
    executed_branches = set()
    for filename in cov.get_data().measured_files():
        file_arcs = cov.get_data().arcs(filename)  # Arcs represent branches
        if file_arcs:
            for arc in file_arcs:
                executed_branches.add((filename, arc))
    return executed_branches

def get_branch_coverage(cov):
    """Retrieve and count the coverage of each branch (arc) in the code. Does not natively provide hit counts for branches """
    branch_coverage = {}
    for filename in cov.get_data().measured_files():
        file_arcs = cov.get_data().arcs(filename)  # Arcs represent branches
        print(f"File: {filename}, Arcs: {file_arcs}")
        if file_arcs:
            for arc in file_arcs:
                from_line, to_line = arc
                if (filename, from_line, to_line) in branch_coverage:
                    branch_coverage[(filename, from_line, to_line)] += 1  # Increment hit count
                else:
                    branch_coverage[(filename, from_line, to_line)] = 1  # Initialize hit count
    return branch_coverage

def track_branch_coverage(algorithm, graph):
    """Run the algorithm on the graph and track branch coverage."""
    cov = coverage.Coverage(branch=True)  # Only focus on branch coverage
    cov.erase()  # Clear any previous coverage data

    # Start coverage measurement
    cov.start()

    # Execute the algorithm
    algorithm(graph)

    # Stop coverage measurement
    cov.stop()

    # Save the data
    cov.save()

    # Get branch coverage (without looking at line coverage)
    branch_coverage = get_branch_coverage(cov)

    # Output the branch coverage information
    for (filename, from_line, to_line), hit_count in branch_coverage.items():
        print(f"Branch from line {from_line} to {to_line} in {filename} was hit {hit_count} time(s)")

    return branch_coverage


class FeedbackTools:
    def __init__(self, start_time=None, line_counts=None, lock=None):
        self.observed_outputs = set()
        self.networkx_exceptions = set()
        self.other_exceptions = set()
        self.exception_graphs = {}  # Dictionary to store graphs and their corresponding exceptions
        self.line_counts = line_counts
        self.total_lines = set()
        self.start_time = start_time
        self.observed_executed_lines = set()  # Tracks executed lines of code
        self.observed_branches = set()  # Tracks branches that have been covered
        self.lock = lock or Lock()  # Use a shared lock or create a new one for single instance

    def is_new_and_interesting(self, graph, algorithm, check_func):
        try:
            # Run the algorithm on the graph
            result = algorithm(graph)
            
            # Check if the result is interesting
            interesting_result = check_func(result)
            
            # If it's new and hasn't been observed yet
            if interesting_result not in self.observed_outputs:
                self.observed_outputs.add(interesting_result)
                return True
            
            return False
        
        except nx.NetworkXException as e:
            # Handle NetworkX-specific exceptions
            exception_message = "NetworkX Error: " + str(e)
            if exception_message not in self.networkx_exceptions:
                self.networkx_exceptions.add(exception_message)
                self.exception_graphs[graph] = exception_message
                return True  # Treat this as a new "interesting" result by returning True
        
        except Exception as e:
            # Handle any other general exceptions
            exception_message = "Error: " + str(e)
            if exception_message not in self.other_exceptions:
                self.other_exceptions.add(exception_message)
                self.exception_graphs[graph] = exception_message
                return True  # Treat this as a new "interesting" result by returning True
        
        return False

    def parse_missing_lines(self, report_content):
        missing_lines = set()
        current_file_index = 0
        total_lines_previous_files = 0
        for line in report_content.split('\n'):
            match = re.search(r'\b\d+%.*?(\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?)*)', line)
            if match:
                ranges = match.group(1).split(',')
                for r in ranges:
                    if '-' in r:
                        start, end = map(int, r.split('-'))
                        missing_lines.update(
                            range(start + total_lines_previous_files, end + total_lines_previous_files + 1))
                    else:
                        missing_lines.add(int(r) + total_lines_previous_files)
                current_file_index += 1
                total_lines_previous_files = sum(self.line_counts[:current_file_index])
        return missing_lines

    def check_coverage(self, report_content):
        # Extract total coverage rate
        coverage_data_match = re.search(r'TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%', report_content)
        if coverage_data_match:
            total_statements = int(coverage_data_match.group(1))
            missed_statements = int(coverage_data_match.group(2))
            total_coverage_rate = int(coverage_data_match.group(3))

            covered_statements = total_statements - missed_statements
            missing_lines = self.parse_missing_lines(report_content)

            return total_coverage_rate, covered_statements, missing_lines
        else:
            print("Total coverage rate not found.")
            return None, None, None

    def load_coverage_data(self, file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

    def compare_coverage(self, old_coverage, new_coverage):
        new_lines_covered = {}

        for filename in new_coverage['files']:
            old_lines = old_coverage['files'].get(filename, {}).get('executed_lines', [])
            new_lines = new_coverage['files'][filename]['executed_lines']

            # Find the difference
            newly_covered = list(set(new_lines) - set(old_lines))

            if newly_covered:
                new_lines_covered[filename] = newly_covered

        return new_lines_covered

    def is_new_and_interesting_coverage_updated(self, graph, algorithm):
        with self.lock:  # Acquire the lock
            # Create a Coverage object with the instance-specific coverage file
            cov = coverage.Coverage(config_file='.coveragerc')
            cov.erase()

            # Start coverage measurement
            cov.start()

            try:
                # Now import networkx
                # import networkx as nx
                # nx = importlib.reload(nx)

                algorithm(graph)

            except nx.NetworkXError as e:
                exception_message = str(e)
                if exception_message not in self.networkx_exceptions:
                    self.networkx_exceptions.add(exception_message)
                    self.exception_graphs[graph] = exception_message

            except Exception as e:
                exception_message = str(e)
                if exception_message not in self.other_exceptions:
                    self.other_exceptions.add(exception_message)
                    self.exception_graphs[graph] = exception_message

            finally:
                # Stop coverage measurement
                cov.stop()

                # Save the data collected
                cov.save()

                # Get executed lines from this run
                current_executed_lines = get_executed_lines(cov)

                # Determine if there are new executed lines
                new_executed_lines = current_executed_lines - self.observed_executed_lines
                if new_executed_lines:
                    self.observed_executed_lines.update(new_executed_lines)
                    print(f"{len(new_executed_lines)}, {time.time() - self.start_time}")
                    # print(f"New lines executed: {new_executed_lines}")
                    return True  # New lines are executed

            return False

    def is_new_and_interesting_coverage(self, graph, algorithm):
        try:
            # Create a Coverage object with configurations from .coveragerc
            cov = coverage.Coverage(config_file='.coveragerc')
            cov.erase()

            # Start coverage measurement
            cov.start()

            # Now import networkx
            import networkx as nx
            nx = importlib.reload(nx)

            result = algorithm(graph)

            # Stop coverage measurement
            cov.stop()

            # Save the data collected
            cov.save()

            # cov.report(show_missing=True)
            # cov.html_report()
            # Generate JSON report
            # timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            # json_report_filename = f"coverage_{timestamp}.json"
            # cov.json_report(outfile=json_report_filename)

            # Create and display the report
            buffer = io.StringIO()
            cov.report(show_missing=True, file=buffer)
            buffer.seek(0)
            report_content = buffer.getvalue()
            total_coverage_rate, _, current_missing_lines = self.check_coverage(report_content)

            # Calculate currently covered lines
            all_possible_lines = set(range(1, sum(self.line_counts) + 1))
            current_covered_lines = all_possible_lines - current_missing_lines
            # print(current_covered_lines)

            # Check if there are new lines covered
            new_covered_lines = current_covered_lines - self.observed_outputs
            if new_covered_lines:
                self.observed_outputs.update(new_covered_lines)
                print(f"{len(new_covered_lines)}, {time.time() - self.start_time}")
                # print(new_covered_lines)
                return True  # New lines are covered

            return False
        except nx.NetworkXError as e:
            exception_message = str(e)
            if exception_message not in self.networkx_exceptions:
                self.networkx_exceptions.add(exception_message)
                self.exception_graphs[graph] = exception_message
            return False
        except Exception as e:
            exception_message = str(e)
            if exception_message not in self.other_exceptions:
                self.other_exceptions.add(exception_message)
                self.exception_graphs[graph] = exception_message
            return False


    def is_new_branch_triggered(self, graph, algorithm):
        """Track branch coverage and check if any new branches are triggered."""
        with self.lock:  # Acquire the lock
            # Create a Coverage object to track branch coverage
            cov = coverage.Coverage(branch=True)
            cov.erase()  # Clear previous coverage data

            # Start coverage measurement
            cov.start()

            try:
                # Execute the algorithm
                algorithm(graph)

            except nx.NetworkXError as e:
                exception_message = str(e)
                if exception_message not in self.networkx_exceptions:
                    self.networkx_exceptions.add(exception_message)
                    self.exception_graphs[graph] = exception_message

            except Exception as e:
                exception_message = str(e)
                if exception_message not in self.other_exceptions:
                    self.other_exceptions.add(exception_message)
                    self.exception_graphs[graph] = exception_message

            finally:
                # Stop coverage measurement
                cov.stop()

                # Save the data collected
                cov.save()

                # Get the executed branches from the current run
                current_executed_branches = get_executed_branches(cov)

                # Find new branches that were triggered
                new_branches = current_executed_branches - self.observed_branches
                if new_branches:
                    # Update the observed branches
                    self.observed_branches.update(new_branches)

                    # Print and log new branches triggered
                    print(f"Total new branches executed: {len(new_branches)}, Time: {time.time() - self.start_time}")
                    return True  # New branches are triggered

            return False  # No new branches were triggered



# Example function that runs the algorithm
def example_algorithm(graph):
    # Use strongly connected components algorithm
    scc = list(nx.strongly_connected_components(graph))
    print(f"Strongly connected components: {scc}")


if __name__ == "__main__":
    # Create a simple directed graph
    graph = nx.DiGraph()
    graph.add_edges_from([(1, 2), (2, 3), (3, 1), (3, 4)])

    # Example of running the branch coverage tracker
    branch_coverage_info = track_branch_coverage(example_algorithm, graph)