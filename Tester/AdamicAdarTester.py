import os
import uuid
from itertools import permutations

import networkx as nx
import igraph as ig
import pickle

from matplotlib import pyplot as plt

from Utils.FileUtils import save_discrepancy
from Utils.GraphConverter import GraphConverter


class AdamicAdarTester:

    def __init__(self, corpus_filename="aa_corpus.pkl"):
        self.corpus = []
        self.uuid = uuid.uuid4().hex[:8]
        print(f'Bug file id: {self.uuid}')

    def test_single_graph(self, G, timestamp):
        discrepancies = self.test_adamic_adar_algorithms(G)
        if discrepancies and len(G.nodes) < 30:
            discrepancy_count = len(discrepancies)  # Count the discrepancies
            discrepancy_msg = "Results of NetworkX and iGraph are different for a graph!"
            save_discrepancy((discrepancy_msg, G, timestamp),
                             f"aa_discrepancy_{self.uuid}.pkl")
            return discrepancy_msg, G, discrepancy_count
        return None, None, None

    def test_adamic_adar_algorithms(self, G):
        """Test Adamic-Adar index between networkx and igraph."""

        discrepancies = []

        nodes = list(G.nodes())
        all_pairs = list(permutations(nodes, 2))

        # NetworkX Adamic-Adar
        nx_pairs = nx.adamic_adar_index(G, ebunch=all_pairs)

        # Convert NetworkX graph to iGraph
        converter = GraphConverter(G)
        G_ig = converter.to_igraph()

        # iGraph Adamic-Adar
        # mode = "in" if G.is_directed() else "all"
        ig_aa_matrix = G_ig.similarity_inverse_log_weighted(mode="all")

        # Create a dictionary of Adamic-Adar scores for each node pair
        nx_aa_dict = {(u, v): aa for u, v, aa in nx_pairs}

        for i, node1 in enumerate(G.nodes()):
            for j, node2 in enumerate(G.nodes()):
                if node1 != node2:
                    # Retrieve Adamic-Adar score from iGraph
                    ig_score = ig_aa_matrix[i][j]
                    nx_score = nx_aa_dict.get((node1, node2), 0)
                    # if nx_score == 0:
                    #     continue

                    if not self.approximately_equal(nx_score, ig_score):
                        # print(f'{node1} to {node2}')
                        # print(ig_score)
                        # print(nx_score)
                        # print('------')
                        discrepancies.append(((node1, node2), nx_score, ig_score))

        return discrepancies

    def calculate_adamic_adar_igraph(self, G_ig, node1, node2):
        """Calculate Adamic-Adar index for a pair of nodes in an iGraph graph."""
        # Get the neighbors of both nodes
        neighbors1 = set(G_ig.neighbors(node1))
        neighbors2 = set(G_ig.neighbors(node2))

        # Find common neighbors
        common_neighbors = neighbors1.intersection(neighbors2)

        # Calculate Adamic-Adar score
        aa_score = sum(1 / (G_ig.degree(v) - 1) for v in common_neighbors if G_ig.degree(v) > 1)
        return aa_score

    @staticmethod
    def approximately_equal(a, b, tol=1e-3):
        """Check if two centrality values are approximately equal considering a tolerance."""
        return abs(a - b) <= tol

    def run(self):
        """Test Adamic-Adar index on every graph in the corpus."""
        for G in self.corpus:
            discrepancies = self.test_adamic_adar_algorithms(G)
            if discrepancies:
                print(f"Discrepancies found in graph {G}:")
                isolated_nodes = list(nx.isolates(G))
                if isolated_nodes:
                    print(f"Graph {G} has isolated nodes:", isolated_nodes)
                for pair, nx_score, ig_score in discrepancies:
                    print(f"Node pair {pair} has different scores - NetworkX: {nx_score}, iGraph: {ig_score}")

        print("End of Adamic-Adar testing.")


if __name__ == "__main__":
    tester = AdamicAdarTester()
    tester.run()
