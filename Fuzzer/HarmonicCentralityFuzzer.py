import time

import networkx as nx
from BaseFuzzer import BaseFuzzer
from Generator.SmokeGenerator import SmokeGenerator
from Tester.HarmonicCentralityTester import HarmonicCentralityTester
from Utils.FileUtils import create_single_node_graph, save_graphs, load_graphs

class HarmonicCentralityFuzzer(BaseFuzzer):
    def get_corpus_name(self):
        return "hc_corpus"

    def executor(self, G):
        return nx.harmonic_centrality(G, distance='weight')

    def get_tester(self):
        return HarmonicCentralityTester(self.corpus_path)

    def create_single_graph(self):
        return [create_single_node_graph()]

    def create_multiple_graphs(self):
        generator = SmokeGenerator(self.executor, n=30, m=2, directed=True, weighted=True,
                                   negative_weights=True, negative_cycle=True, parallel_edges=False)
        generated_graphs = generator.generate()
        save_graphs(generated_graphs, "hc_corpus")
        return load_graphs("hc_corpus")

    def process_test_results(self, mutated_graph, tester, first_occurrence_times, total_bug_counts, timestamp):
        discrepancy_msg, _, discrepancy_count = tester.test_single_graph(mutated_graph)
        if discrepancy_msg:
            if discrepancy_msg not in first_occurrence_times:
                first_occurrence_times[discrepancy_msg] = time.time() - self.start_time
                print(f"Recorded first occurrence of '{discrepancy_msg}' at {first_occurrence_times[discrepancy_msg]} seconds since start.")
            total_bug_counts[discrepancy_msg] = total_bug_counts.get(discrepancy_msg, 0) + discrepancy_count


if __name__ == "__main__":
    hc_fuzzer = HarmonicCentralityFuzzer(num_iterations=60, use_multiple_graphs=False, feedback_check_type="regular")
    # Optionally, set a user-defined interesting check function
    def custom_interesting_check(result):
        min_diff = 1e-5
        most_interesting_pair = None
        nodes = list(result.keys())
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                u, v = nodes[i], nodes[j]
                diff = abs(result[u] - result[v])
                if 0 < diff <= min_diff:
                    min_diff = diff
                    most_interesting_pair = (u, v)
        return min_diff
    hc_fuzzer.set_interesting_check(custom_interesting_check)
    hc_fuzzer.run()
