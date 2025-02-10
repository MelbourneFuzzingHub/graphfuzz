import networkx as nx

from BaseFuzzer import BaseFuzzer
from Generator.SmokeGenerator import SmokeGenerator
from Tester.SCCTester import SCCTester
from Utils.FileUtils import create_single_node_digraph, create_single_node_graph, save_graphs, load_graphs


class SCCFuzzer(BaseFuzzer):
    def get_corpus_name(self):
        return "scc_corpus"

    def executor(self, G):
        return list(nx.strongly_connected_components(G))

    def get_tester(self):
        return SCCTester(self.corpus_path)

    def create_single_graph(self):
        return [create_single_node_digraph()]

    def create_multiple_graphs(self):
        generator = SmokeGenerator(self.executor, n=30, m=2, directed=True, weighted=True,
                                   negative_weights=False,
                                   negative_cycle=False, parallel_edges=False)
        generated_graphs = generator.generate_n_graphs(10)
        save_graphs(generated_graphs, "scc_corpus")
        return load_graphs("scc_corpus")

    def process_test_results(self, mutated_graph, tester, first_occurrence_times, total_bug_counts, timestamp):
        discrepancy_msg, _ = tester.test_single_graph(mutated_graph, timestamp)
        if discrepancy_msg:
            if discrepancy_msg not in first_occurrence_times:
                first_occurrence_times[discrepancy_msg] = timestamp
                print(
                    f"Recorded first occurrence of '{discrepancy_msg}' at {first_occurrence_times[discrepancy_msg]} seconds since start.")
            total_bug_counts[discrepancy_msg] = total_bug_counts.get(discrepancy_msg, 0) + 1


if __name__ == "__main__":
    scc_fuzzer = SCCFuzzer(num_iterations=100, use_multiple_graphs=True,
                           feedback_check_type="regular")
    scc_fuzzer.run()
