import math
import os
import uuid

import networkx as nx
import igraph as ig
import pickle

from Utils.FileUtils import save_discrepancy
from Utils.GraphConverter import GraphConverter


class HarmonicCentralityTester:

    def __init__(self, corpus_filename="hc_corpus.pkl"):
        self.corpus = []
        self.uuid = uuid.uuid4().hex[:8]
        print(f'Bug file id: {self.uuid}')

    def test_single_graph(self, G):
        discrepancies = self.test_harmonic_centrality_algorithms(G)
        if discrepancies:
            discrepancy_count = len(discrepancies)  # Count the discrepancies
            discrepancy_msg = f"Results of NetworkX and iGraph are different for a graph!"
            save_discrepancy((discrepancy_msg, G),
                             f"hc_discrepancy_{self.uuid}.pkl")
            return discrepancy_msg, G, discrepancy_count
        return None, None, None

    def test_harmonic_centrality_algorithms(self, G):
        """Test harmonic centrality between networkx and igraph."""

        def contains_negative_or_nan_weight(graph):
            for u, v, data in graph.edges(data=True):
                weight = data.get('weight', 0)
                if weight <= 0 or math.isnan(weight):
                    return True
            return False

        # Compare the results
        discrepancies = []
        if contains_negative_or_nan_weight(G):
            # print("negative")
            return discrepancies
        else:
            # Compute harmonic centrality with networkx
            nx_centrality = nx.harmonic_centrality(G, distance='weight')
            # print(nx_centrality)
            # print(f"{nx.harmonic_centrality(G, distance='weight')}")

            # Convert NetworkX graph to iGraph
            converter = GraphConverter(G)
            G_ig = converter.to_igraph()

            # Determine the mode based on whether the graph is directed or not
            mode = "in" if G.is_directed() else "all"

            # Compute harmonic centrality with igraph, taking into account if the graph is directed
            # Check if the iGraph has 'weight' attribute for edges
            if 'weight' in G_ig.es.attribute_names():
                ig_centrality = G_ig.harmonic_centrality(mode=mode, weights='weight', normalized=False)
            else:
                # If no weights, compute centrality without weights
                ig_centrality = G_ig.harmonic_centrality(mode=mode, normalized=False)
            # print(f"ig_centrality{ig_centrality} ")
            # print(f"{G_ig.harmonic_centrality(mode=mode, weights='weight', normalized=False)}")

            # In igraph, the result is a list, map it to vertex ids
            ig_centrality_dict = {G_ig.vs['name'][v.index]: c for v, c in zip(G_ig.vs, ig_centrality)}
            # print(ig_centrality_dict)

            for node, nx_score in nx_centrality.items():
                ig_score = ig_centrality_dict.get(str(node))
                if ig_score is None or not self.approximately_equal(nx_score, ig_score):
                    discrepancies.append((node, nx_score, ig_score))

            return discrepancies

    @staticmethod
    def approximately_equal(a, b, tol=1e-6):
        """Check if two centrality values are approximately equal considering a tolerance."""
        return abs(a - b) <= tol

    def run(self):
        """Test harmonic centrality algorithms on every graph in the corpus."""
        for G in self.corpus:
            discrepancies = self.test_harmonic_centrality_algorithms(G)
            if discrepancies:
                # Process and print discrepancies
                print(f"Discrepancies found in graph {G}:")
                isolated_nodes = list(nx.isolates(G))
                # # Visualize the graph
                # plt.figure(figsize=(8, 6))
                # nx.draw(G, with_labels=True)
                # plt.show()
                if isolated_nodes:
                    print(f"Graph {G} has isolated nodes:", isolated_nodes)
                if len(G.nodes()) < 15:
                    # Serialize and save the exception graphs using pickle
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    parent_dir = os.path.dirname(script_dir)
                    log_dir = os.path.join(parent_dir, "Log")
                    exception_file_path = os.path.join(log_dir, 'small_discrepancies.pkl')
                    with open(exception_file_path, 'wb') as exception_file:
                        pickle.dump(G, exception_file)
                    print(f"Exceptions were encountered. Saved to {exception_file_path}")
                for node, nx_score, ig_score in discrepancies:
                    print(f"Node {node} has different scores - NetworkX: {nx_score}, iGraph: {ig_score}")

        print("End of harmonic centrality testing.")

    # Save discrepancies if needed


if __name__ == "__main__":
    tester = HarmonicCentralityTester()
    tester.run()
