import networkx as nx
from BaseFuzzer import BaseFuzzer
from Generator.SmokeGenerator import SmokeGenerator
from Tester.MAXFVTester import MAXFVTester
from Utils.FileUtils import create_single_node_graph, save_graphs, load_graphs, save_discrepancy
import uuid


class MAXFVFuzzer(BaseFuzzer):
    def __init__(self, num_iterations=100, use_multiple_graphs=False,
                 feedback_check_type="regular", scheduler=None, timeout_duration=15):
        super().__init__(num_iterations, use_multiple_graphs, feedback_check_type, scheduler, timeout_duration)
        self.uuid = uuid.uuid4().hex[:8]

    def get_corpus_name(self):
        return "maxfv_corpus"

    def executor(self, G):
        if len(G.nodes()) < 2:
            return 0  # Return 0 for graphs with less than 2 nodes
        # Sort nodes by degree in descending order
        sorted_nodes = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True)
        # Select the node with the highest degree as the source
        s = sorted_nodes[0]
        # Select the node with the second highest degree as the target
        t = sorted_nodes[1]
        return nx.maximum_flow_value(G, s, t, capacity='weight')

    def get_tester(self):
        return MAXFVTester(self.corpus_path, self.uuid)

    def create_single_graph(self):
        return [create_single_node_graph()]

    def create_multiple_graphs(self):
        print("Creating multiple graphs")
        generator = SmokeGenerator(self.executor, n=30, m=2, directed=True, weighted=True,
                                   negative_weights=False)
        generated_graphs = generator.generate_n_graphs(10)
        save_graphs(generated_graphs, "maxfv_corpus")
        return load_graphs("maxfv_corpus")

    def process_test_results(self, mutated_graph, tester, first_occurrence_times, total_bug_counts, timestamp):
        discrepancies = tester.test_single_graph(mutated_graph)
        if discrepancies:
            for discrepancy_message, graph in discrepancies.items():
                if discrepancy_message not in first_occurrence_times:
                    save_discrepancy((discrepancy_message, graph, timestamp), f"maxfv_discrepancy_{self.uuid}.pkl")
                    first_occurrence_times[discrepancy_message] = timestamp
                    print(f"Recorded first occurrence of '{discrepancy_message}' at {first_occurrence_times[discrepancy_message]} seconds since start.")
                    total_bug_counts[discrepancy_message] = total_bug_counts.get(discrepancy_message, 0) + 1


if __name__ == "__main__":
    maxfv_fuzzer = MAXFVFuzzer(num_iterations=50, use_multiple_graphs=True, feedback_check_type="regular")
    maxfv_fuzzer.run()
