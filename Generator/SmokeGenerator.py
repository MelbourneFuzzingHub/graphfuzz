import itertools

import networkx as nx
import random
import os
import pickle


class SmokeGenerator:
    def __init__(self, algorithm, n, m, num_trials=5, directed=True, weighted=True, negative_weights=True,
                 negative_cycle=True, parallel_edges=True):
        self.algorithm = algorithm
        self.n = n
        self.m = m
        self.num_trials = num_trials
        self.directed = directed
        self.weighted = weighted
        self.negative_weights = negative_weights
        self.negative_cycle = negative_cycle
        self.parallel_edges = parallel_edges
        self.valid_graph_types = self._determine_valid_graph_types()

    def _generate_graph(self, directed, weighted, negative_weights, negative_cycle, allow_parallel_edges):
        num_nodes = random.randint(1, self.n)
        p = random.uniform(0.1, 0.9)

        if directed:
            G = nx.MultiDiGraph() if allow_parallel_edges else nx.DiGraph()
        else:
            G = nx.MultiGraph() if allow_parallel_edges else nx.Graph()

        # Populate the graph with edges
        edges = itertools.combinations(range(num_nodes), 2)

        for u, v in edges:
            if random.random() < p:
                G.add_edge(u, v)

        if weighted:
            for u, v, data in G.edges(data=True):
                weight = random.randint(1, 200)
                if negative_weights:
                    weight *= random.choice([-1, 1])
                    if not negative_cycle and nx.negative_edge_cycle(G):
                        # If a negative cycle is not allowed but exists, adjust the weight to be positive
                        weight = abs(weight)
                data['weight'] = weight

        return G

    def _is_valid_for_algorithm(self, G):
        try:
            _ = self.algorithm(G)
            return True
        except Exception as e:  # Catch any exception
            print(f"Error for graph: {e}")
            return False

    def _determine_valid_graph_types(self):
        valid_types = []

        directed_values = [True, False] if self.directed else [False]
        weighted_values = [True, False] if self.weighted else [False]
        negative_weights_values = [True, False] if self.negative_weights else [False]
        negative_cycle_values = [True, False] if self.negative_cycle else [False]
        parallel_edges_values = [True, False] if self.parallel_edges else [False]

        for directed in directed_values:
            for weighted in weighted_values:
                for allow_parallel_edges in parallel_edges_values:
                    if weighted:
                        for negative_weights in negative_weights_values:
                            if negative_weights:
                                for negative_cycle in negative_cycle_values:
                                    is_valid = True
                                    for _ in range(self.num_trials):
                                        G = self._generate_graph_determine(directed, weighted, negative_weights,
                                                                           negative_cycle, allow_parallel_edges)
                                        if not self._is_valid_for_algorithm(G):
                                            is_valid = False
                                            break
                                    if is_valid:
                                        valid_types.append((directed, weighted, negative_weights,
                                                            negative_cycle, allow_parallel_edges))
                            else:
                                is_valid = True
                                for _ in range(self.num_trials):
                                    G = self._generate_graph_determine(directed, weighted, negative_weights,
                                                                       False, allow_parallel_edges)
                                    if not self._is_valid_for_algorithm(G):
                                        is_valid = False
                                        break
                                if is_valid:
                                    valid_types.append((directed, weighted, negative_weights,
                                                        False, allow_parallel_edges))
                    else:
                        is_valid = True
                        for _ in range(self.num_trials):
                            G = self._generate_graph_determine(directed, weighted, False, False, allow_parallel_edges)
                            if not self._is_valid_for_algorithm(G):
                                is_valid = False
                                break
                        if is_valid:
                            valid_types.append((directed, weighted, False, False, allow_parallel_edges))
        # print(valid_types)
        return valid_types

    def _generate_graph_determine(self, directed, weighted, negative_weights, negative_cycle, allow_parallel_edges):
        num_nodes = random.randint(10, 20)
        p = random.uniform(0.1, 0.9)

        if directed:
            G = nx.MultiDiGraph() if allow_parallel_edges else nx.DiGraph()
        else:
            G = nx.MultiGraph() if allow_parallel_edges else nx.Graph()

        # Populate the graph with edges
        edges = itertools.combinations(range(num_nodes), 2)
        for u, v in edges:
            if random.random() < p:
                G.add_edge(u, v)

        if weighted:
            for u, v, data in G.edges(data=True):
                weight = random.randint(1, 100)
                if negative_weights:
                    weight *= random.choice([-1, 1])
                    if not negative_cycle and nx.negative_edge_cycle(G):
                        # If a negative cycle is not allowed but exists, adjust the weight to be positive
                        weight = abs(weight)
                data['weight'] = weight
            # Ensure at least one negative weight if negative_weights is True
            if negative_weights and all(data['weight'] >= 0 for _, _, data in G.edges(data=True)):
                u, v = random.choice(list(G.edges()))
                G[u][v]['weight'] = -random.randint(1, 100)
            # Ensure at least one negative cycle if negative_cycle is True
            # The original method to generate graph (True, True, True, True, False) has bug for some reason
            if negative_cycle and not nx.negative_edge_cycle(G) and not allow_parallel_edges:
                # Create a cycle graph with a specified number of nodes
                cycle_size = random.randint(3, min(5, len(G.nodes())))

                # Check if the graph should be directed or not
                if directed:
                    cycle_graph = nx.DiGraph()
                    nodes = list(range(cycle_size))
                    for i in range(cycle_size):
                        cycle_graph.add_edge(nodes[i], nodes[(i + 1) % cycle_size])
                else:
                    cycle_graph = nx.cycle_graph(cycle_size)

                # Assign weights to the edges of this cycle graph
                for u, v in cycle_graph.edges():
                    cycle_graph[u][v]['weight'] = random.randint(1, 10)

                # Ensure the cycle graph has a negative cycle
                u, v = random.choice(list(cycle_graph.edges()))
                cycle_graph[u][v]['weight'] = -random.randint(11, 20)

                # Add this cycle graph to the existing graph
                G = nx.compose(G, cycle_graph)

        return G

    def generate_random(self):
        # Randomly select one graph type
        random_graph_type = random.choice(self.valid_graph_types)

        # Generate one graph of this type
        G = self._generate_graph(*random_graph_type)

        return G

    def generate(self):
        graphs = []

        for graph_type in self.valid_graph_types:
            for _ in range(self.m):
                G = self._generate_graph(*graph_type)
                graphs.append(G)

        return graphs

    def generate_n_graphs(self, num_graphs):
        graphs = []
        while len(graphs) < num_graphs:
            # Randomly select a valid graph type
            random_graph_type = random.choice(self.valid_graph_types)
            # Generate a graph of this type
            G = self._generate_graph(*random_graph_type)
            # Check if the graph is valid for the algorithm
            if self._is_valid_for_algorithm(G):
                graphs.append(G)
        return graphs

    def save_graphs(self, graphs):
        # Ensure the Corpus_Data directory exists
        corpus_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Corpus_Data')
        if not os.path.exists(corpus_dir):
            os.makedirs(corpus_dir)

        # Generate a unique name for this run
        run_name = f"run_{len(os.listdir(corpus_dir)) + 1}.pkl"

        # Save the graphs using pickle
        with open(os.path.join(corpus_dir, run_name), 'wb') as f:
            pickle.dump(graphs, f)

        print(f"Saved graphs to {run_name}")


# def dummy_algorithm(G):
#     return nx.minimum_spanning_tree(G)
#
#
# generator = SmokeGenerator(dummy_algorithm, n=10, m=10)
# graphs = generator.generate()
# generator.save_graphs(graphs)
# print(f"Generated {len(graphs)} valid graphs.")
