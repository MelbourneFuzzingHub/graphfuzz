import os
import uuid

import networkx as nx
import pickle
import igraph as ig

from Utils.FileUtils import save_discrepancies, save_discrepancy
from Utils.GraphConverter import GraphConverter


class MaxMatchingTester:

    def __init__(self, corpus_filename="max_matching_corpus.pkl"):
        self.corpus = []
        self.uuid = uuid.uuid4().hex[:8]
        print(f'Bug file id: {self.uuid}')

    def test_single_graph(self, G):
        discrepancy_msg, discrepancy_graph = self.test_max_matching_algorithms(G)
        if discrepancy_msg:
            save_discrepancy((discrepancy_msg, discrepancy_graph),
                             f"max_matching_discrepancy_{self.uuid}.pkl")
        return discrepancy_msg, discrepancy_graph

    def igraph_max_matching_size(self, nx_graph):
        if not nx.is_bipartite(nx_graph):
            raise ValueError("Provided NetworkX graph is not bipartite")

        # Get the two sets of the bipartite graph
        sets = nx.bipartite.sets(nx_graph)
        types = [node in sets[0] for node in nx_graph.nodes()]

        # Convert NetworkX graph to iGraph
        converter = GraphConverter(nx_graph)
        g = converter.to_igraph()

        # Set the 'type' attribute for each vertex in iGraph
        g.vs['type'] = types

        # Compute the maximum bipartite matching
        matching = g.maximum_bipartite_matching()
        matching_size = sum(1 for i in range(g.vcount()) if matching.is_matched(i))
        return matching_size

    def test_max_matching_algorithms(self, G):
        """Test different maximum matching algorithms and check if they produce the same result."""
        algorithms = {
            'hopcroft_karp': lambda g: nx.algorithms.bipartite.matching.hopcroft_karp_matching(g),
            'eppstein': lambda g: nx.algorithms.bipartite.matching.eppstein_matching(g),
            'igraph': lambda g: self.igraph_max_matching_size(g)
        }
        results = {}

        for algo_name, algo_func in algorithms.items():
            try:
                if algo_name == 'igraph':
                    results[algo_name] = algo_func(G)
                else:
                    results[algo_name] = len(algo_func(G))
            except Exception:
                results[algo_name] = []

        for algo_name1, result1 in results.items():
            for algo_name2, result2 in results.items():
                if algo_name1 != algo_name2 and result1 != result2:
                    discrepancy_msg = f"Results of {algo_name1} and {algo_name2} are different for a graph!"
                    return discrepancy_msg, G  # Return the graph with discrepancy

        return None, None  # Return None if no discrepancy

    def run(self):
        """Test max matching algorithms on every graph in the corpus."""
        discrepancy_data = []
        discrepancy_counts = {}
        for G in self.corpus:
            discrepancy_msg, discrepancy_graph = self.test_max_matching_algorithms(G)
            if discrepancy_msg:
                discrepancy_counts[discrepancy_msg] = discrepancy_counts.get(discrepancy_msg, 0) + 1
                if discrepancy_counts[discrepancy_msg] <= 5:
                    discrepancy_data.append((discrepancy_msg, discrepancy_graph))

        if discrepancy_data:
            save_discrepancies(discrepancy_data, "max_matching_discrepancy.pkl")
            print(f"There are {len(discrepancy_data)} graphs with discrepancies saved.")

        for msg, count in discrepancy_counts.items():
            print(f"Discrepancy message: \"{msg}\" occurred {count} times.")

        print("End of Max Matching testing.")
