import os
import uuid

import networkx as nx
import igraph as ig
import pickle

from Utils.FileUtils import save_discrepancy
from Utils.GraphConverter import GraphConverter

class JaccardSimilarityTester:

    def __init__(self, corpus_filename="js_corpus.pkl"):
        self.corpus = []
        self.uuid = uuid.uuid4().hex[:8]
        print(f'Bug file id: {self.uuid}')

    def test_single_graph(self, G, timestamp):
        discrepancies = self.test_jaccard_similarity_algorithms(G)
        if discrepancies:
            discrepancy_count = len(discrepancies)  # Count the discrepancies
            discrepancy_msg = f"Results of NetworkX and iGraph are different for a graph!"
            save_discrepancy((discrepancy_msg, G, timestamp),
                             f"js_discrepancy_{self.uuid}.pkl")
            return discrepancy_msg, G, discrepancy_count
        return None, None, None

    def test_jaccard_similarity_algorithms(self, G):
        """Test Jaccard similarity between networkx and igraph."""
        # Compute Jaccard similarity with networkx
        nx_jaccard = list(nx.jaccard_coefficient(G))

        # Convert NetworkX graph to iGraph
        converter = GraphConverter(G)
        G_ig = converter.to_igraph()

        # Compute Jaccard similarity with igraph for each pair (u, v) in nx_jaccard
        # The similarity_jaccard function in igraph expects vertex IDs, so need to map node names to IDs
        if len(G_ig.vs) == 0:
            # print("empty")
            vertex_id_map = {}
        else:
            vertex_id_map = {str(node): idx for idx, node in enumerate(G_ig.vs['name'])}
        ig_jaccard_results = []
        for u, v, p in nx_jaccard:
            u_id, v_id = vertex_id_map[str(u)], vertex_id_map[str(v)]
            # The similarity_jaccard function returns a list of similarity values for the given pairs
            ig_jaccard_score = G_ig.similarity_jaccard(pairs=[(u_id, v_id)], loops=False)[0]

            # Get the neighbors of each vertex as sets using iGraph
            # neighbors_u = set(G_ig.neighbors(u_id))
            # neighbors_v = set(G_ig.neighbors(v_id))

            # Calculate the intersection and union of the two sets of neighbors
            # intersection = neighbors_u.intersection(neighbors_v)
            # union = neighbors_u.union(neighbors_v)

            # Manually compute the Jaccard coefficient
            # jaccard_coefficient = len(intersection) / len(union) if union else 0
            # print(f'p{p}')
            # print(f'jaccard_coefficient{jaccard_coefficient}')
            # print(f'ig_jaccard_score{ig_jaccard_score}')
            ig_jaccard_results.append((u, v, ig_jaccard_score))

        # print(ig_jaccard_results)

        # Compare the results
        discrepancies = []
        for (u, v, nx_score), (_, _, ig_score) in zip(nx_jaccard, ig_jaccard_results):
            if not self.approximately_equal(nx_score, ig_score):
                discrepancies.append((u, v, nx_score, ig_score))

        return discrepancies

    @staticmethod
    def approximately_equal(a, b, tol=1e-6):
        """Check if two similarity values are approximately equal considering a tolerance."""
        return abs(a - b) <= tol

    def run(self):
        """Test Jaccard similarity algorithms on every graph in the corpus."""
        # Initialize a list to hold graphs with discrepancies and less than 22 nodes
        small_graphs_with_discrepancies = []

        for G in self.corpus:
            discrepancies = self.test_jaccard_similarity_algorithms(G)
            if discrepancies:
                # Process and print discrepancies
                print(f"Discrepancies found in graph {G}:")
                for u, v, nx_score, ig_score in discrepancies:
                    print(f"Pair ({u}, {v}) has different scores - NetworkX: {nx_score}, iGraph: {ig_score}")
                if len(G.nodes) < 22:
                    # Add graph to the list if less than 22 nodes
                    small_graphs_with_discrepancies.append(G)
                    print(f"Graph with less than 22 nodes and discrepancies will be saved.")

        # Save any graphs with discrepancies and less than 22 nodes to a file
        if small_graphs_with_discrepancies:
            save_file_name = 'small_graph_discrepancies.pkl'
            with open(save_file_name, 'wb') as save_file:
                pickle.dump(small_graphs_with_discrepancies, save_file)
            print(f"Graphs with discrepancies and less than 22 nodes were saved to {save_file_name}")

        print("End of Jaccard similarity testing.")

if __name__ == "__main__":
    tester = JaccardSimilarityTester()
    tester.run()
