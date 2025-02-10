import os
import time
import argparse
import pickle
import coverage
import re
import networkx as nx


class CoverageCalculator:
    def __init__(self, first_graph_timestamp):
        self.observed_executed_lines = set()
        self.start_time = first_graph_timestamp

    def check_graph_coverage(self, graph, algorithm, cov, graph_timestamp, graph_id):
        cov.erase()

        # Start coverage measurement
        cov.start()

        result = algorithm(graph)

        # Stop coverage measurement
        cov.stop()

        # Save the data collected
        cov.save()

        # Get executed lines from this run
        current_executed_lines = self.get_executed_lines(cov)

        # Determine if there are new executed lines
        new_executed_lines = current_executed_lines - self.observed_executed_lines
        if new_executed_lines:
            self.observed_executed_lines.update(new_executed_lines)
            time_diff = graph_timestamp - self.start_time
            print(f"Number of new lines covered: {len(new_executed_lines)}, Time: {time_diff:.2f} seconds, Graph ID: {graph_id}")

    @staticmethod
    def get_executed_lines(cov):
        """Retrieve executed lines from coverage data."""
        executed_lines = set()
        for filename in cov.get_data().measured_files():
            lines = cov.get_data().lines(filename)
            if lines:
                for line in lines:
                    executed_lines.add((filename, line))
        return executed_lines

    @staticmethod
    def load_graphs_from_folder(folder):
        graphs = []
        for filename in sorted(os.listdir(folder), key=lambda x: int(re.search(r'\d+', x).group())):
            if filename.endswith(".pkl"):
                file_path = os.path.join(folder, filename)
                with open(file_path, 'rb') as file:
                    graph = pickle.load(file)
                    file_stat = os.stat(file_path)
                    timestamp = file_stat.st_mtime
                    graphs.append((graph, filename, timestamp))
        return graphs


    @staticmethod
    def example_algorithm(graph):
        return list(nx.strongly_connected_components(graph))


def main():
    # Start coverage measurement before any imports
    cov = coverage.Coverage(config_file='.coveragerc')
    cov.start()

    parser = argparse.ArgumentParser(description="Calculate line coverage for graphs in a folder and print new coverage lines.")
    parser.add_argument("folder", type=str, help="The folder containing the graph files.")
    args = parser.parse_args()

    graphs = CoverageCalculator.load_graphs_from_folder(args.folder)
    if not graphs:
        print(f"No graphs found in folder: {args.folder}")
        return

    # Use the timestamp of the first graph as the start time
    first_graph_timestamp = graphs[0][2]
    print(f"Start time (based on first graph): {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first_graph_timestamp))}")

    calculator = CoverageCalculator(first_graph_timestamp)

    for graph, graph_id, timestamp in graphs:
        calculator.check_graph_coverage(graph, CoverageCalculator.example_algorithm, cov, timestamp, graph_id)

    cov.stop()
    cov.save()


if __name__ == "__main__":
    main()


## Usage
## python3 Utils/CoverageCalculator.py Parallel_log/graphs_folder_3