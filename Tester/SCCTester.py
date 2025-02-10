import os
import uuid

import networkx as nx
import pickle

from Utils.FileUtils import save_discrepancies, save_discrepancy
from Utils.GraphConverter import GraphConverter


class SCCTester:

    def __init__(self, discrepancy_filename="scc_discrepancy.pkl"):
        self.corpus = []
        self.discrepancy_filename = discrepancy_filename
        self.uuid = uuid.uuid4().hex[:8]
        print(f'Bug file id: {self.uuid}')

    def test_single_graph(self, G, timestamp):
        discrepancy_msg, discrepancy_graph = self.test_scc_algorithms(G)
        if discrepancy_msg:
            save_discrepancy((discrepancy_msg, discrepancy_graph, timestamp),
                             f"scc_discrepancy_{self.uuid}.pkl")
        return discrepancy_msg, discrepancy_graph


    def test_scc_algorithms(self, G):
        """Test different SCC algorithms and check if they produce the same result."""
        algorithms = {
            'default': nx.strongly_connected_components,
            'recursive': nx.strongly_connected_components_recursive,
            'kosaraju': nx.kosaraju_strongly_connected_components,
            'igraph': lambda graph: [set(component) for component in graph.components(mode='STRONG')]
        }
        results = {}

        # Convert NetworkX graph to iGraph
        converter = GraphConverter(G)
        G_ig = converter.to_igraph_default()

        for algo_name, algo_func in algorithms.items():
            if algo_name == 'igraph':
                results[algo_name] = set(
                    frozenset(map(int, G_ig.vs[component]['_nx_name'])) for component in G_ig.components(mode='STRONG'))
                # results[algo_name] = set(
                # frozenset(map(int, G_ig.vs[component]['name'])) for component in G_ig.components(mode='STRONG'))
            else:
                scc = list(algo_func(G))
                results[algo_name] = set(map(frozenset, scc))

        discrepancy_messages = []
        algo_names = list(algorithms.keys())
        for i in range(len(algo_names)):
            for j in range(i + 1, len(algo_names)):
                algo_name1 = algo_names[i]
                algo_name2 = algo_names[j]
                result1 = results[algo_name1]
                result2 = results[algo_name2]
                if result1 != result2:
                    discrepancy_msg = f"Results of {algo_name1} and {algo_name2} are different for a graph!"
                    discrepancy_messages.append(discrepancy_msg)

        if discrepancy_messages:
            return "--".join(discrepancy_messages), G  # Return the concatenated discrepancy messages and the graph
        else:
            return None, None  # Return None if no discrepancy

    def run(self):
        """Test SCC algorithms on every graph in the corpus."""
        discrepancy_data = []
        discrepancy_counts = {}
        for G in self.corpus:
            discrepancy_msg, discrepancy_graph = self.test_scc_algorithms(G)
            if discrepancy_msg:
                # Increment the discrepancy message count
                discrepancy_counts[discrepancy_msg] = discrepancy_counts.get(discrepancy_msg, 0) + 1
                # Check the count to decide whether to save the graph
                if discrepancy_counts[discrepancy_msg] <= 5:
                    discrepancy_data.append((discrepancy_msg, discrepancy_graph))

        if discrepancy_data:
            # Save the discrepancy graphs and messages to a file
            save_discrepancies(discrepancy_data, self.discrepancy_filename)
            print(f"There are {len(discrepancy_data)} graphs with discrepancies saved.")

        # Now print all the discrepancy messages and their counts
        for msg, count in discrepancy_counts.items():
            print(f"Discrepancy message: \"{msg}\" occurred {count} times.")

        print("End of SCC testing.")
        return discrepancy_counts