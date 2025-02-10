import networkx as nx
from BaseFuzzer import BaseFuzzer
from Generator.SmokeGenerator import SmokeGenerator
from Tester.STPLTester import STPLTester
from Utils.FileUtils import create_single_node_digraph, save_graphs, load_graphs


class STPLFuzzer(BaseFuzzer):
    def get_corpus_name(self):
        return "stpl_corpus"

    def executor(self, G):
        if len(G.nodes()) < 2:
            return float('inf')  # Return infinity for graphs with less than 2 nodes
        # Sort nodes by degree in descending order
        sorted_nodes = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True)
        # Select the node with the highest degree as the source
        source = sorted_nodes[0]
        # Select the node with the second highest degree as the target
        target = sorted_nodes[1]
        try:
            return nx.shortest_path_length(G, source=source, target=target, weight='weight', method='bellman-ford')
        except nx.NetworkXNoPath:
            return float('inf')  # Return infinity if no path exists

    def get_tester(self):
        return STPLTester(self.corpus_path)

    def create_single_graph(self):
        return [create_single_node_digraph()]

    def create_multiple_graphs(self):
        generator = SmokeGenerator(self.executor, n=30, m=2, directed=True, weighted=True,
                                   negative_weights=True, negative_cycle=False, parallel_edges=False)
        generated_graphs = generator.generate()
        save_graphs(generated_graphs, "stpl_corpus")
        return load_graphs("stpl_corpus")

    def process_test_results(self, mutated_graph, tester, first_occurrence_times, total_bug_counts, timestamp):
        discrepancies = tester.test_single_graph(mutated_graph, timestamp, num_pairs=10)
        for discrepancy_msg, _ in discrepancies:
            if discrepancy_msg:
                if discrepancy_msg not in first_occurrence_times:
                    first_occurrence_times[discrepancy_msg] = timestamp
                    print(f"Recorded first occurrence of '{discrepancy_msg}' at {first_occurrence_times[discrepancy_msg]} seconds since start.")
                total_bug_counts[discrepancy_msg] = total_bug_counts.get(discrepancy_msg, 0) + 1


if __name__ == "__main__":
    stpl_fuzzer = STPLFuzzer(num_iterations=100, use_multiple_graphs=True, feedback_check_type="regular")
    stpl_fuzzer.run()
