import networkx as nx
import random

class CustomGenerator:
    def __init__(self, n=10, m=15, category="bipartite"):
        self.n = n  # Upper limit for the number of nodes
        self.m = m  # Number of graphs to generate
        self.category = category.lower()

    def create_graphs(self):
        graphs = []
        for _ in range(self.m):
            if self.category == "bipartite":
                total_nodes = random.randint(0, self.n)  # Total nodes for this graph
                graphs.append(self._create_bipartite_graph(total_nodes))
            else:
                raise ValueError("Unsupported graph type")
        return graphs

    def create_single_graph(self):
        if self.category == "bipartite":
            total_nodes = random.randint(1, self.n)  # Total nodes for this graph
            return self._create_bipartite_graph(total_nodes)
        else:
            raise ValueError("Unsupported graph type")


    def _create_bipartite_graph(self, total_nodes):
        # Randomly split total nodes into two sets
        n1 = random.randint(0, total_nodes)  # Nodes in set 1
        n2 = total_nodes - n1  # Nodes in set 2

        # Create sets of nodes
        nodes_set_1 = range(n1)
        nodes_set_2 = range(n1, n1 + n2)

        # Create a bipartite graph
        G = nx.Graph()
        G.add_nodes_from(nodes_set_1, bipartite=0)
        G.add_nodes_from(nodes_set_2, bipartite=1)

        # Determine the maximum number of possible edges
        max_edges = n1 * n2

        # Randomly decide the number of edges to add
        num_edges = random.randint(0, max_edges) if max_edges > 0 else 0

        # Add edges randomly
        for _ in range(num_edges):
            n1 = random.choice(list(nodes_set_1)) if nodes_set_1 else None
            n2 = random.choice(list(nodes_set_2)) if nodes_set_2 else None
            if n1 is not None and n2 is not None:
                G.add_edge(n1, n2)

        return G



# generator = CustomGenerator(n=10, m=5, category="Bipartite")
# graphs = generator.create_graphs()
#
# # Displaying basic information about the generated graphs
# for i, graph in enumerate(graphs):
#     num_nodes = graph.number_of_nodes()
#     num_edges = graph.number_of_edges()
#     is_bipartite = nx.is_bipartite(graph)
#     print(f"Graph {i+1}: Nodes = {num_nodes}, Edges = {num_edges}, Is Bipartite = {is_bipartite}")
