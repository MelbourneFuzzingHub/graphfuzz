import time

import networkx as nx
from BaseFuzzer import BaseFuzzer
from Generator.CustomGenerator import CustomGenerator
from Tester.MaxMatchingTester import MaxMatchingTester
from Utils.FileUtils import create_single_node_digraph, save_graphs, load_graphs


class MaxMatchingFuzzer(BaseFuzzer):
    def get_corpus_name(self):
        return "max_matching_corpus"

    def executor(self, G):
        return nx.algorithms.bipartite.matching.hopcroft_karp_matching(G)

    def get_tester(self):
        return MaxMatchingTester(self.corpus_path)

    def create_single_graph(self):
        generator = CustomGenerator(n=1, m=1, category="Bipartite")
        return generator.create_single_graph()

    def create_multiple_graphs(self):
        generator = CustomGenerator(n=30, m=5, category="Bipartite")
        generated_graphs = generator.create_graphs()
        save_graphs(generated_graphs, "max_matching_corpus")
        return load_graphs("max_matching_corpus")

    def process_test_results(self, mutated_graph, tester, first_occurrence_times, total_bug_counts, timestamp):
        discrepancy_msg, _ = tester.test_single_graph(mutated_graph)
        if discrepancy_msg:
            if discrepancy_msg not in first_occurrence_times:
                first_occurrence_times[discrepancy_msg] = time.time() - self.start_time
                print(f"Recorded first occurrence of '{discrepancy_msg}' at {first_occurrence_times[discrepancy_msg]} seconds since start.")
            total_bug_counts[discrepancy_msg] = total_bug_counts.get(discrepancy_msg, 0) + 1


if __name__ == "__main__":
    max_matching_fuzzer = MaxMatchingFuzzer(num_iterations=50, use_multiple_graphs=True, feedback_check_type="regular")
    max_matching_fuzzer.run()
