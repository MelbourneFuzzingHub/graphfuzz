import uuid

import networkx as nx
import pickle

import numpy as np

from Utils.FileUtils import save_discrepancies, save_discrepancy
from Utils.GraphConverter import GraphConverter


class MSTTester:

    def __init__(self, discrepancy_filename="mst_corpus.pkl"):
        self.corpus = []
        self.discrepancy_filename = discrepancy_filename
        self.uuid = uuid.uuid4().hex[:8]
        print(f'Bug file id: {self.uuid}')

    def test_single_graph(self, G):
        discrepancy_msg, discrepancy_graph = self.test_mst_algorithms(G)
        if discrepancy_msg:
            save_discrepancy((discrepancy_msg, discrepancy_graph),
                             f"mst_discrepancy_{self.uuid}.pkl")
        return discrepancy_msg, discrepancy_graph

    def test_mst_algorithms(self, G):
        """Test different MST algorithms and check if they produce the same result."""
        algorithms = {
            'kruskal': lambda graph: nx.minimum_spanning_edges(graph, algorithm='kruskal', data=True),
            'prim': lambda graph: nx.minimum_spanning_edges(graph, algorithm='prim', data=True),
            'boruvka': lambda graph: nx.minimum_spanning_edges(graph, algorithm='boruvka', data=True),
            'igraph': lambda graph: graph.spanning_tree(weights='weight')  # iGraph MST algorithm
        }
        results = {}

        # Convert NetworkX graph to iGraph
        if not nx.is_weighted(G):
            for u, v in G.edges():
                G[u][v]['weight'] = 1
        else:
            for u, v, data in G.edges(data=True):
                if np.isnan(data.get('weight', 0)):
                    G[u][v]['weight'] = 0
        converter = GraphConverter(G)
        G_ig = converter.to_igraph()
        if 'weight' not in G_ig.es.attribute_names():
            G_ig.es['weight'] = 1

        for algo_name, algo_func in algorithms.items():
            if algo_name == 'igraph':
                mst = algo_func(G_ig)  # Use iGraph graph for iGraph MST
                total_weight = sum(edge['weight'] for edge in mst.es)
            else:
                mst_edges = list(algo_func(G))
                total_weight = sum(data['weight'] if 'weight' in data else 1 for u, v, data in mst_edges)

            results[algo_name] = total_weight

        discrepancy_messages = []
        algo_names = list(algorithms.keys())
        for i in range(len(algo_names)):
            for j in range(i + 1, len(algo_names)):
                algo_name1 = algo_names[i]
                algo_name2 = algo_names[j]
                result1 = results[algo_name1]
                result2 = results[algo_name2]
                if result1 != result2:
                    discrepancy_msg = f"Total weights of MSTs produced by {algo_name1} and {algo_name2} are different for a graph!"
                    discrepancy_messages.append(discrepancy_msg)

        if discrepancy_messages:
            print(results)
            return "--".join(discrepancy_messages), G  # Return the concatenated discrepancy messages and the graph
        else:
            return None, None  # Return None if no discrepancy

    def run(self):
        """Test MST algorithms on every graph in the corpus."""
        discrepancy_data = []
        discrepancy_counts = {}
        for G in self.corpus:
            discrepancy_msg, discrepancy_graph = self.test_mst_algorithms(G)
            if discrepancy_msg:
                discrepancy_counts[discrepancy_msg] = discrepancy_counts.get(discrepancy_msg, 0) + 1
                if discrepancy_counts[discrepancy_msg] <= 5:
                    discrepancy_data.append((discrepancy_msg, discrepancy_graph))

        if discrepancy_data:
            save_discrepancies(discrepancy_data, self.discrepancy_filename)
            print(f"There are {len(discrepancy_data)} graphs with discrepancies saved.")

        for msg, count in discrepancy_counts.items():
            print(f"Discrepancy message: \"{msg}\" occurred {count} times.")

        print("End of MST testing.")
