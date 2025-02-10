import math
import random

import networkx as nx
from matplotlib import pyplot as plt

from Mutator.SimpleMutator import SimpleMutator
from Scheduler.RandomDiskScheduler import RandomDiskScheduler
from Scheduler.RandomDiskSchedulerUpdated import RandomDiskSchedulerUpdated
from Scheduler.RandomMemScheduler import RandomMemScheduler

MAX_NODES_THRESHOLD = 300
MIN_NEGATIVE_WEIGHT = -200
MAX_NEGATIVE_WEIGHT = 200
MIN_POSITIVE_WEIGHT = 0
MAX_POSITIVE_WEIGHT = 100


class ExtendedMutator(SimpleMutator):
    def __init__(self, corpus):
        super().__init__()
        self.corpus = corpus
        # Check if the corpus is an instance of RandomDiskScheduler or RandomMemScheduler
        self.is_disk_scheduler = isinstance(corpus, (RandomMemScheduler, RandomDiskSchedulerUpdated, RandomDiskScheduler))

    def stacked_mutate(self, graph):
        mutation_operations = [
            self.add_node,
            self.delete_node,
            self.add_edge,
            self.delete_edge,
            self.modify_edge_weight,
            self.trim_graph_advanced,
            self.combine_graphs  
        ]
        # Generate a random number of mutations to apply
        num_mutations = random.randint(1, 5) + 1

        # Apply each mutation in turn
        for _ in range(num_mutations):
            mutation = random.choice(mutation_operations)
            graph = mutation(graph)

        return graph


    def mutate(self, graph):
        mutation_operations = [
            self.add_node,
            self.delete_node,
            self.add_edge,
            self.delete_edge,
            self.modify_edge_weight,
            self.trim_graph_advanced,
            self.combine_graphs  
        ]
        mutation = random.choice(mutation_operations)
        return mutation(graph)

    def nx_has_weighted_edges(self, nx_graph):
        for _, _, data in nx_graph.edges(data=True):
            if 'weight' not in data:
                return False  # Found an edge without a weight
        return True  # All edges have weights

    def modify_edge_weight(self, graph):
        if graph.edges():
            # Check if the graph has weights
            if not self.nx_has_weighted_edges(graph):
                return graph

            # Check if there are negative weights in the graph
            edge_weights = nx.get_edge_attributes(graph, 'weight').values()
            has_negative_weights = any(weight < 0 for weight in edge_weights)

            # Randomly select an edge
            edge = random.choice(list(graph.edges()))

            # Randomly decide whether to assign a numerical weight or NaN
            if random.random() < 0.995:
                if has_negative_weights:
                    # If there are negative weights, assign a new weight in the range [-200, 200]
                    new_weight = random.randint(MIN_NEGATIVE_WEIGHT, MAX_NEGATIVE_WEIGHT)
                else:
                    # If there are no negative weights, assign a new weight in the range [1, 200]
                    new_weight = random.randint(MIN_POSITIVE_WEIGHT, MAX_NEGATIVE_WEIGHT)
            else:
                # 0.005% chance to assign NaN as the weight
                # new_weight = math.nan
                new_weight = random.randint(MIN_NEGATIVE_WEIGHT, MAX_NEGATIVE_WEIGHT)

            # Modify the weight of the edge
            # graph[edge[0]][edge[1]]['weight'] = new_weight
            graph.add_edge(edge[0], edge[1], weight=new_weight)
        # else:
        #     print("Graph has no edges, exiting mutation.")

        return graph

    def trim_graph_advanced(self, graph):
        if len(graph) <= 2:
            return graph

        # Calculate degree of each node
        node_degrees = dict(graph.degree())

        # Sort nodes by degree
        sorted_nodes = sorted(node_degrees.keys(), key=lambda x: node_degrees[x], reverse=True)

        # Determine the number of nodes to remove
        num_nodes_to_remove = random.randint(len(graph) // 5, 2 * len(graph) // 5)

        # Remove nodes with the lowest degree
        for node in sorted_nodes[-num_nodes_to_remove:]:
            graph.remove_node(node)

        return graph

    def trim_graph(self, graph):
        """
        Trim the graph by randomly removing nodes until its size is halved.
        """
        if len(graph.nodes()) <= 1:
            return graph  # Cannot trim further if graph has 1 or 0 nodes

        # Calculate the target number of nodes after trimming
        target_num_nodes = len(graph.nodes()) // 2

        while len(graph.nodes()) > target_num_nodes:
            # Randomly select a node to remove
            node_to_remove = random.choice(list(graph.nodes()))
            graph.remove_node(node_to_remove)

        return graph

    def combine_graphs(self, graph):
        # TODO: Connecting using 0-10 nodes?
        # Fetch a graph based on the type of corpus
        if self.is_disk_scheduler:
            other_graph = self.corpus.get_graph()
        else:
            other_graph = random.choice(self.corpus)

        # Skip combination if one is a (Di)Graph and the other is a Multi(Di)Graph
        if ((isinstance(graph, nx.Graph) or isinstance(graph, nx.DiGraph)) and
            (isinstance(other_graph, nx.MultiGraph) or isinstance(other_graph, nx.MultiDiGraph))) or \
                ((isinstance(graph, nx.MultiGraph) or isinstance(graph, nx.MultiDiGraph)) and
                 (isinstance(other_graph, nx.Graph) or isinstance(other_graph, nx.DiGraph))):
            return graph

        if not graph.nodes():
            graph.add_node(0)

        if not other_graph.nodes():
            other_graph.add_node(0)

        while len(graph.nodes()) + len(other_graph.nodes()) > MAX_NODES_THRESHOLD:
            graph = self.trim_graph_advanced(graph)
            other_graph = self.trim_graph_advanced(other_graph)

        combined_graph = nx.disjoint_union(graph, other_graph)

        # Check if either graph has weighted edges
        has_weights = self.nx_has_weighted_edges(graph) or self.nx_has_weighted_edges(other_graph)
        has_negative_weights = False

        # If weights are present, check for negative weights
        if has_weights:
            for _, _, data in graph.edges(data=True):
                if data.get('weight', 0) < 0:
                    has_negative_weights = True
                    break
            if not has_negative_weights:
                for _, _, data in other_graph.edges(data=True):
                    if data.get('weight', 0) < 0:
                        has_negative_weights = True
                        break

        # Connecting nodes based on node degree
        nodes_from_graph = sorted(graph.nodes(), key=graph.degree, reverse=True)
        nodes_from_other_graph = [node + len(graph.nodes()) for node in
                                  sorted(other_graph.nodes(), key=other_graph.degree, reverse=True)]

        # Connecting top 3 nodes with highest degree from each graph with or without weights
        for i in range(min(3, len(nodes_from_graph), len(nodes_from_other_graph))):
            if graph.degree(nodes_from_graph[i]) > 0 and other_graph.degree(
                    nodes_from_other_graph[i] - len(graph.nodes())) > 0:
                if has_weights:
                    # Assign a random weight within the specified ranges
                    weight_range = (MIN_NEGATIVE_WEIGHT, MAX_NEGATIVE_WEIGHT) if has_negative_weights else (
                        MIN_POSITIVE_WEIGHT, MAX_POSITIVE_WEIGHT)
                    weight = random.randint(*weight_range)
                    combined_graph.add_edge(nodes_from_graph[i], nodes_from_other_graph[i], weight=weight)
                else:
                    # Add edge without weight
                    combined_graph.add_edge(nodes_from_graph[i], nodes_from_other_graph[i])

        # Adding additional edges with or without weights
        additional_edges = random.randint(1, 5)  # add 1-5 additional edges
        for _ in range(additional_edges):
            if not graph.nodes() or not other_graph.nodes():
                # Skip edge addition if either graph has no nodes
                continue

            node_from_graph = random.choice(list(graph.nodes()))

            # Against empty sequence for other_graph nodes
            if other_graph.nodes():
                node_from_other_graph = random.choice(list(other_graph.nodes())) + len(graph.nodes())

                if has_weights:
                    # Assign a random weight within the specified ranges
                    weight_range = (MIN_NEGATIVE_WEIGHT, MAX_NEGATIVE_WEIGHT) if has_negative_weights else (
                        MIN_POSITIVE_WEIGHT, MAX_POSITIVE_WEIGHT)
                    weight = random.randint(*weight_range)
                    combined_graph.add_edge(node_from_graph, node_from_other_graph, weight=weight)
                else:
                    # Add edge without weight
                    combined_graph.add_edge(node_from_graph, node_from_other_graph)

        # Delete the original graphs
        del graph
        del other_graph

        return combined_graph

    def visualize_graph(self, graph, with_labels=True, node_size=700, font_size=12):
        """
        Visualize the graph.

        :param graph: The NetworkX graph to be visualized.
        :param with_labels: Boolean, whether to draw labels on the nodes.
        :param node_size: Size of the nodes.
        :param font_size: Size of the labels on the nodes.
        """
        pos = nx.spring_layout(graph)  # positions for all nodes
        nx.draw_networkx_nodes(graph, pos, node_size=node_size)

        # Draw edges
        nx.draw_networkx_edges(graph, pos)

        if 'weight' in nx.get_edge_attributes(graph, 'weight'):
            edge_labels = nx.get_edge_attributes(graph, 'weight')
            nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)

        if with_labels:
            nx.draw_networkx_labels(graph, pos, font_size=font_size)

        plt.show()
