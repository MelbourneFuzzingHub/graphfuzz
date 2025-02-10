import networkx as nx
from BaseFuzzer import BaseFuzzer
from Generator.SmokeGenerator import SmokeGenerator
from Tester.MSTTester import MSTTester
from Utils.FileUtils import create_single_node_graph, save_graphs, load_graphs
import math


class MSTFuzzer(BaseFuzzer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the custom interesting check for MST weight
        self.set_interesting_check(self.mst_weight_interesting_check)
        self.observed_buckets = set()  # Track unique weight buckets

    def get_corpus_name(self):
        return "mst_corpus"

    def executor(self, G):
        return nx.minimum_spanning_tree(G)

    def get_tester(self):
        return MSTTester(self.corpus_path)

    def create_single_graph(self):
        return [create_single_node_graph()]

    def create_multiple_graphs(self):
        generator = SmokeGenerator(self.executor, n=30, m=2, directed=True, weighted=True,
                                   negative_weights=True, negative_cycle=True, parallel_edges=False)
        generated_graphs = generator.generate()
        save_graphs(generated_graphs, "mst_corpus")
        return load_graphs("mst_corpus")

    def mst_weight_interesting_check(self, result):
        """Custom feedback to check if MST weight is in a new bucket based on powers of 2, differentiated by num_nodes."""
        # Calculate total weight and the number of nodes in the MST
        total_weight = sum(data.get('weight', 1) for u, v, data in result.edges(data=True))
        num_nodes = result.number_of_nodes()
        
        # Special case for zero weight
        if total_weight == 0:
            bucket = f"{num_nodes}_0"
        else:
            # Determine the power of 2 bucket for total weight
            abs_weight = abs(total_weight)
            exponent = math.floor(math.log2(abs_weight))
            bucket = f"{num_nodes}_{'-' if total_weight < 0 else ''}2^{exponent}"
        
        # Use a tuple of (num_nodes, bucket) to check uniqueness
        unique_bucket = (num_nodes, bucket)
        
        # Check if this bucket has been observed before
        if unique_bucket not in self.observed_buckets:
            self.observed_buckets.add(unique_bucket)
            # print(f"New bucket triggered: {bucket} for total weight: {total_weight} with {num_nodes} nodes")
            return unique_bucket  # New, interesting bucket detected

        return None  # No new bucket found

    def process_test_results(self, mutated_graph, tester, first_occurrence_times, total_bug_counts, timestamp):
        discrepancy_msg, _ = tester.test_single_graph(mutated_graph)
        if discrepancy_msg:
            if discrepancy_msg not in first_occurrence_times:
                first_occurrence_times[discrepancy_msg] = timestamp
                print(f"Recorded first occurrence of '{discrepancy_msg}' at {first_occurrence_times[discrepancy_msg]} seconds since start.")
            total_bug_counts[discrepancy_msg] = total_bug_counts.get(discrepancy_msg, 0) + 1


if __name__ == "__main__":
    mst_fuzzer = MSTFuzzer(num_iterations=100, use_multiple_graphs=True, feedback_check_type="regular")
    mst_fuzzer.run()
