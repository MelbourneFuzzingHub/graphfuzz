import os
import random

import networkx as nx
import pickle

from networkx.algorithms.flow import edmonds_karp, shortest_augmenting_path, dinitz, boykov_kolmogorov, preflow_push

from Utils.FileUtils import save_discrepancies
from Utils.GraphConverter import GraphConverter


class MAXFVTester:

    def __init__(self, discrepancy_filename="maxfv_corpus.pkl", uuid=None):
        self.corpus = []
        self.discrepancy_filename = discrepancy_filename
        self.uuid = uuid
        print(f'Bug file id: {self.uuid}')

    def test_single_graph(self, G):
        discrepancies = self.run_maxfv_tests_multiple_times(G)
        if discrepancies:
            return discrepancies
        return None

    def run_maxfv_tests_multiple_times(self, G, num_runs=5):
        """Run the test_maxfv_algorithms function multiple times with different source-target pairs."""
        discrepancies = {}

        nodes = list(G.nodes)
        if len(nodes) < 2:
            return discrepancies

        for _ in range(num_runs):
            # Randomly select source and target nodes
            source = random.choice(nodes)
            target = random.choice(nodes)
            while target == source:  # Ensure source and target are different
                target = random.choice(nodes)

            # Call the provided test function
            discrepancy, graph = self.test_maxfv_algorithms(G, source, target)

            # If a discrepancy is found, add it to the dictionary
            if discrepancy is not None:
                # discrepancy_message = f"Source: {source}, Target: {target}, Discrepancy: {discrepancy}"
                discrepancy_message = f"Discrepancy: {discrepancy}"
                discrepancies[discrepancy_message] = graph

        return discrepancies

    def test_maxfv_algorithms(self, G, source, target):
        """Test different maximum flow value algorithms and check if they produce the same result."""
        algorithms = {
            'edmonds_karp': edmonds_karp,
            'shortest_augmenting_path': shortest_augmenting_path,
            'preflow_push': preflow_push,
            'dinitz': dinitz,
            'boykov_kolmogorov': boykov_kolmogorov,
            'igraph': None
        }
        results = {}

        # Convert NetworkX graph to iGraph
        converter = GraphConverter(G)
        G_ig = converter.to_igraph()
        # Find iGraph indices for source and target
        source_ig = G_ig.vs.find(name=str(source)).index
        target_ig = G_ig.vs.find(name=str(target)).index

        for algo_name, algo_func in algorithms.items():
            try:
                if algo_name != 'igraph':
                    flow_value = nx.maximum_flow_value(G, source, target, flow_func=algo_func, capacity='weight')
                else:
                    # Compute max flow using iGraph
                    flow_value = G_ig.maxflow(source_ig, target_ig, capacity='weight').value
                results[algo_name] = flow_value
            except Exception as e:
                # print(f"Error using {algo_name}: {e}")
                results[algo_name] = None

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

        # # Check if all results are the same
        # algorithms_keys = list(algorithms.keys())
        # for i in range(len(algorithms_keys)):
        #     for j in range(i + 1, len(algorithms_keys)):
        #         if results[algorithms_keys[i]] != results[algorithms_keys[j]]:
        #             discrepancy_msg = f"Results of {algorithms_keys[i]} and {algorithms_keys[j]} are different for a graph!"
        #             return False, discrepancy_msg
        # return True, None

    def run(self):
        """Test maximum flow value algorithms on every graph in the corpus."""
        discrepancy_data = []
        discrepancy_counts = {}
        count = 0

        for G in self.corpus:
            # Ensure the graph has at least two nodes
            if len(G) < 2:
                print(f"Graph number {count + 1} has less than two nodes. Skipping...")
                continue

            # Sort nodes by degree in descending order
            sorted_nodes = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True)

            # Consider top 10 and bottom 10 nodes
            top_10_nodes = sorted_nodes[:3] if len(sorted_nodes) >= 3 else sorted_nodes
            bottom_10_nodes = sorted_nodes[-3:] if len(sorted_nodes) >= 3 else sorted_nodes

            for source in top_10_nodes:
                for target in bottom_10_nodes:
                    if source != target:
                        count += 1
                        test_result, discrepancy_msg = self.test_maxfv_algorithms(G, source, target)
                        if not test_result:
                            discrepancy_counts[discrepancy_msg] = discrepancy_counts.get(discrepancy_msg, 0) + 1

                            if discrepancy_counts[discrepancy_msg] <= 5:
                                discrepancy_data.append((discrepancy_msg, G))

        if discrepancy_data:
            # Save the discrepancy graphs and messages to a file
            save_discrepancies(discrepancy_data, self.discrepancy_filename)
            print(f"There are {len(discrepancy_data)} graphs with discrepancies saved.")

            # Print all the discrepancy messages and their counts
        for msg, count in discrepancy_counts.items():
            print(f"Discrepancy message: \"{msg}\" occurred {count} times.")

        print("End of MAXFV testing.")
        return discrepancy_counts

