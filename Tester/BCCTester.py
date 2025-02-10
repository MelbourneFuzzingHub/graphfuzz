import os
import uuid

import networkx as nx
import pickle
from Utils.FileUtils import save_discrepancies, save_discrepancy
from Utils.GraphConverter import GraphConverter


class BCCTester:

    def __init__(self, corpus_filename="bcc_corpus.pkl"):
        self.corpus = []
        self.uuid = uuid.uuid4().hex[:8]
        print(f'Bug file id: {self.uuid}')

    def test_single_graph(self, G, timestamp):
        discrepancy_msg, discrepancy_graph = self.test_bcc_algorithms(G)
        if discrepancy_msg:
            save_discrepancy((discrepancy_msg, discrepancy_graph, timestamp),
                             f"bcc_discrepancy_{self.uuid}.pkl")
        return discrepancy_msg, discrepancy_graph

    def test_bcc_algorithms(self, G):
        """Test different BCC algorithms and check if they produce the same result."""
        algorithms = {
            'networkx': nx.biconnected_components,
            'igraph': lambda graph: [set(component) for component in graph.biconnected_components()]
        }
        results = {}

        # Convert NetworkX graph to iGraph
        converter = GraphConverter(G)
        G_ig = converter.to_igraph_default()

        for algo_name, algo_func in algorithms.items():
            if algo_name == 'igraph':
                results[algo_name] = set(
                    frozenset(map(int, G_ig.vs[component]['_nx_name'])) for component in G_ig.biconnected_components())
            else:
                bcc = list(algo_func(G))
                results[algo_name] = set(map(frozenset, bcc))

        for algo_name1, result1 in results.items():
            for algo_name2, result2 in results.items():
                if algo_name1 != algo_name2 and result1 != result2:
                    discrepancy_msg = f"Results of {algo_name1} and {algo_name2} are different for a graph!"
                    return discrepancy_msg, G  # Return the graph with discrepancy

        return None, None  # Return None if no discrepancy

    def run(self):
        """Test BCC algorithms on every graph in the corpus."""
        discrepancy_data = []
        discrepancy_counts = {}
        for G in self.corpus:
            discrepancy_msg, discrepancy_graph = self.test_bcc_algorithms(G)
            if discrepancy_msg:
                discrepancy_counts[discrepancy_msg] = discrepancy_counts.get(discrepancy_msg, 0) + 1
                if discrepancy_counts[discrepancy_msg] <= 5:
                    discrepancy_data.append((discrepancy_msg, discrepancy_graph))

        if discrepancy_data:
            save_discrepancies(discrepancy_data, "bcc_discrepancy.pkl")
            print(f"There are {len(discrepancy_data)} graphs with discrepancies saved.")

        for msg, count in discrepancy_counts.items():
            print(f"Discrepancy message: \"{msg}\" occurred {count} times.")

        print("End of BCC testing.")
        return discrepancy_counts


if __name__ == "__main__":
    tester = BCCTester()
    discrepancy_counts = tester.run()
    print("Discrepancy counts:", discrepancy_counts)
