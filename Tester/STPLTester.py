import os
import random
import uuid

import networkx as nx
import pickle

from Utils.FileUtils import save_discrepancies, save_discrepancy
from Utils.GraphConverter import GraphConverter


class STPLTester:

    def __init__(self, corpus_filename="stpl_corpus.pkl", discrepancy_filename="stpl_discrepancy.pkl"):
        self.corpus = []
        self.uuid = uuid.uuid4().hex[:8]
        print(f'Bug file id: {self.uuid}')

    def test_single_graph(self, G, timestamp, num_pairs=5):
        total_discrepancies = []

        for _ in range(num_pairs):
            if len(G) < 2:
                break  # Skip if the graph has less than 2 nodes

            # # Get the degrees of all nodes and sort them in descending order
            # sorted_nodes = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True)

            # # Select the top two nodes with the highest degree as source and target
            # source, target = sorted_nodes[:2]
            source, target = random.sample(G.nodes(), 2)

            discrepancy_msg, discrepancy_graph = self.test_stpl_algorithms_updated(G, source, target)

            if discrepancy_msg and len(G.nodes()) < 20:
                save_discrepancy((discrepancy_msg, discrepancy_graph, timestamp), f"stpl_discrepancy_{self.uuid}.pkl")
                total_discrepancies.append((discrepancy_msg, discrepancy_graph))

        return total_discrepancies

    def test_graph(self, G, num_pairs=10):
        total_discrepancies = []

        for _ in range(num_pairs):
            if len(G) < 2:
                break  # Skip if the graph has less than 2 nodes

            source, target = random.sample(G.nodes(), 2)
            discrepancy_msg, discrepancy_graph = self.test_stpl_algorithms_updated(G, source, target)

            if discrepancy_msg:
                # save_discrepancy((discrepancy_msg, discrepancy_graph, timestamp), "stpll_discrepancy.pkl", max_discrepancies_per_msg=10000)
                total_discrepancies.append((discrepancy_msg, discrepancy_graph))

        return total_discrepancies

    # def test_stpl_algorithms_updated(self, G, source, target):
    #     """Test different shortest path length algorithms and check if they produce the same result."""
    #     algorithms = {
    #         'bellman_ford_path_length': nx.bellman_ford_path_length,
    #         # 'johnson': None,  # Placeholder as Johnson's algorithm requires special handling
    #         'goldberg_radzik': nx.goldberg_radzik,
    #         # 'floyd_warshall': None,  # Placeholder as Floyd-Warshall requires special handling
    #         'igraph': None  # Placeholder as iGraph requires special handling
    #     }
    #     results = {}
    #
    #     # Ensure all edges have a weight; if not, assign a default weight of 1
    #     for u, v, data in G.edges(data=True):
    #         data.setdefault('weight', 1)
    #
    #     # Convert NetworkX graph to iGraph
    #     converter = GraphConverter(G)
    #     G_ig = converter.to_igraph()
    #     # Find iGraph indices for source and target
    #     source_ig = G_ig.vs.find(name=str(source)).index
    #     target_ig = G_ig.vs.find(name=str(target)).index
    #
    #     for algo_name, algo_func in algorithms.items():
    #         try:
    #             if algo_name == 'bellman_ford_path_length':
    #                 results[algo_name] = algo_func(G, source=source, target=target, weight='weight')
    #             elif algo_name == 'johnson':
    #                 paths = nx.johnson(G, weight='weight')
    #                 shortest_path = paths[source].get(target)
    #                 if shortest_path:
    #                     path_length = self.path_length(G, shortest_path)
    #                     results[algo_name] = path_length
    #                 else:
    #                     results[algo_name] = float('inf')
    #             elif algo_name == 'goldberg_radzik':
    #                 _, dist = algo_func(G, source, weight='weight')
    #                 results[algo_name] = dist.get(target, float('inf'))
    #             elif algo_name == 'floyd_warshall':
    #                 all_pairs = nx.floyd_warshall(G, weight='weight')
    #                 results[algo_name] = all_pairs[source].get(target, float('inf'))
    #             elif algo_name == 'igraph':
    #                 # Use iGraph's shortest_paths function for graphs with possibly negative weights
    #                 shortest_paths = G_ig.shortest_paths(source=source_ig, target=target_ig, weights='weight')
    #                 results[algo_name] = shortest_paths[0][0] if shortest_paths else float('inf')
    #         except Exception as e:
    #             # print(f"Error using {algo_name}: {e}")
    #             results[algo_name] = float('inf')
    #
    #     discrepancy_messages = []
    #     algo_names = list(algorithms.keys())
    #     for i in range(len(algo_names)):
    #         for j in range(i + 1, len(algo_names)):
    #             algo_name1 = algo_names[i]
    #             algo_name2 = algo_names[j]
    #             result1 = results[algo_name1]
    #             result2 = results[algo_name2]
    #             if result1 != result2:
    #                 discrepancy_msg = f"Results of {algo_name1} and {algo_name2} are different for a graph!"
    #                 discrepancy_messages.append(discrepancy_msg)
    #
    #     if discrepancy_messages:
    #         # print(f"{source_ig} to {target_ig} : {results}")
    #         return "--".join(discrepancy_messages), G  # Return the concatenated discrepancy messages and the graph
    #     else:
    #         return None, None  # Return None if no discrepancy
    def test_stpl_algorithms_updated(self, G, source, target):
        """Test different shortest path length algorithms and check if they produce the same result."""
        # Check for negative weights in the graph
        has_negative_weight = any(data.get('weight', 0) < 0 for _, _, data in G.edges(data=True))

        algorithms = {
            'bellman_ford_path_length': nx.bellman_ford_path_length,
            'goldberg_radzik': nx.goldberg_radzik,
            'igraph': None  # Placeholder as iGraph requires special handling
        }

        # Include Dijkstra's algorithm if there are no negative weights
        if not has_negative_weight:
            algorithms['dijkstra_path_length'] = nx.dijkstra_path_length

        results = {}

        # Ensure all edges have a weight; if not, assign a default weight of 1
        for u, v, data in G.edges(data=True):
            data.setdefault('weight', 1)

        # Convert NetworkX graph to iGraph, if necessary
        converter = GraphConverter(G)
        G_ig = converter.to_igraph()
        source_ig = G_ig.vs.find(name=str(source)).index
        target_ig = G_ig.vs.find(name=str(target)).index

        for algo_name, algo_func in algorithms.items():
            try:
                if algo_name in ['bellman_ford_path_length', 'dijkstra_path_length']:
                    results[algo_name] = algo_func(G, source=source, target=target, weight='weight')
                elif algo_name == 'goldberg_radzik':
                    _, dist = algo_func(G, source, weight='weight')
                    results[algo_name] = dist.get(target, float('inf'))
                elif algo_name == 'igraph' and G.number_of_edges() > 0 and not nx.negative_edge_cycle(G, weight='weight'):
                    shortest_paths = G_ig.shortest_paths(source=source_ig, target=target_ig, weights='weight')
                    results[algo_name] = shortest_paths[0][0] if shortest_paths else float('inf')
            except Exception as e:
                results[algo_name] = float('inf')

        discrepancy_messages = []
        algo_names = list(algorithms.keys())
        for i in range(len(algo_names)):
            for j in range(i + 1, len(algo_names)):
                algo_name1 = algo_names[i]
                algo_name2 = algo_names[j]
                result1 = results.get(algo_name1, float('inf'))
                result2 = results.get(algo_name2, float('inf'))
                if result1 != result2:
                    discrepancy_msg = f"Results of {algo_name1} and {algo_name2} are different for a graph!"
                    discrepancy_messages.append(discrepancy_msg)

        if discrepancy_messages:
            return "--".join(discrepancy_messages), G
        else:
            return None, None

    def get_smallest_edge_weight(self, G, u, v):
        # For multi-edges, get the smallest weight among all edges between u and v
        return min(data.get('weight', 1) for data in G[u][v].values())

    def path_length(self, graph, path, weight='weight'):
        """Compute the length of a given path in the graph."""
        if path is None or len(path) == 0:
            return float('inf')  # Return infinity if path is not available

        length = 0
        for i in range(1, len(path)):
            u, v = path[i - 1], path[i]
            if graph.is_multigraph():
                length += self.get_smallest_edge_weight(graph, u, v)
            else:
                length += graph[u][v].get(weight, 1)  # Use .get() method to provide a default weight if not present
        return length

    def test_stpl_algorithms(self, G, source, target):
        """Test different shortest path length algorithms and check if they produce the same result."""
        algorithms = ['bellman_ford_path_length', 'johnson', 'goldberg_radzik']
        results = {}

        # Ensure all edges have a weight; if not, assign a default weight of 1
        for u, v, data in G.edges(data=True):
            data.setdefault('weight', 1)

        for algo in algorithms:
            try:
                if algo == 'bellman_ford_path_length':
                    results[algo] = nx.bellman_ford_path_length(G, source=source, target=target, weight='weight')
                elif algo == 'johnson':
                    paths = nx.johnson(G, weight='weight')
                    shortest_path = paths[source].get(target)  # Get the shortest path from source to target
                    if shortest_path:
                        # Compute the length of the shortest path
                        path_length = self.path_length(G, shortest_path)
                        results[algo] = path_length
                    else:
                        results[algo] = float('inf')  # Use infinity if target is not reachable
                elif algo == 'goldberg_radzik':
                    _, dist = nx.goldberg_radzik(G, source, weight='weight')
                    results[algo] = dist.get(target, float('inf'))  # Use infinity if target is not reachable
                elif algo == 'floyd_warshall':
                    all_pairs = nx.floyd_warshall(G, weight='weight')
                    results[algo] = all_pairs[source].get(target, float('inf'))
            except (nx.NetworkXNoPath, nx.NetworkXUnbounded):
                results[algo] = float('inf')  # Use infinity to represent that the target is not reachable

        # Check if all results have the same shortest path length
        discrepancy_msg = None
        first_result = results[algorithms[0]]
        for algo in algorithms[1:]:
            if results[algo] != first_result:
                discrepancy_msg = f"Shortest path lengths computed by {algorithms[0]} and {algo} are different for a graph!"
                break

        return True if discrepancy_msg is None else False, discrepancy_msg

    def run(self):
        """Test shortest path length algorithms on every graph in the corpus."""
        discrepancy_data = []
        discrepancy_counts = {}
        count = 0
        for G in self.corpus:
            # Ensure the graph has at least two nodes
            if len(G) < 2:
                print(f"Graph number {count + 1} has less than two nodes. Skipping...")
                continue

            # Sort nodes by degree in descending order
            # sorted_nodes = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True)

            # Select the node with the highest degree as the source
            # source = sorted_nodes[0]

            # Select the node with the second highest degree as the target
            # target = sorted_nodes[1]
            # source, target = random.sample(G.nodes(), 2)

            for _ in range(10):
                if len(G) < 2:
                    break  # Skip if the graph has less than 2 nodes

                source, target = random.sample(G.nodes(), 2)

                test_result, discrepancy_msg = self.test_stpl_algorithms(G, source, target)
                if not test_result:
                    discrepancy_counts[discrepancy_msg] = discrepancy_counts.get(discrepancy_msg, 0) + 1

                    if discrepancy_counts[discrepancy_msg] <= 5:
                        discrepancy_data.append((discrepancy_msg, G))

            count += 1

        if discrepancy_data:
            # Save the discrepancy graphs and messages to a file
            save_discrepancies(discrepancy_data, "stpl_discrepancy.pkl")
            print(f"There are {len(discrepancy_data)} graphs with discrepancies saved.")

            # Print all the discrepancy messages and their counts
        for msg, count in discrepancy_counts.items():
            print(f"Discrepancy message: \"{msg}\" occurred {count} times.")

        print("End of STPL testing.")
        return discrepancy_counts
