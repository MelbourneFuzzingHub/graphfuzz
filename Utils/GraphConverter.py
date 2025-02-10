import random

import networkx as nx
import igraph as ig


class GraphConverter:
    def __init__(self, networkx_graph):
        self.networkx_graph = networkx_graph

    def visualize_igraph(self, igraph_graph, filename=None):
        layout = igraph_graph.layout("kk")  # Kamada-Kawai layout for graph drawing
        visual_style = {
            "vertex_size": 20,
            "vertex_label": [v['name'] for v in igraph_graph.vs] if 'name' in igraph_graph.vs.attributes() else None,
            "edge_width": [1 + 2 * (sum(w) / len(w)) if isinstance(w, list) else 1 + 2 * w for w in
                           igraph_graph.es['weight']],
            "bbox": (400, 400),
            "margin": 20
        }
        # If a filename is provided, save to that file. Otherwise, show the plot.
        if filename:
            ig.plot(igraph_graph, filename, **visual_style)
        else:
            ig.plot(igraph_graph, **visual_style)

    def to_igraph(self):
        # Create a new iGraph graph instance
        igraph_graph = ig.Graph(directed=self.networkx_graph.is_directed())

        # Add vertices
        for node in self.networkx_graph.nodes():
            igraph_graph.add_vertex(name=str(node))

        # Handle MultiGraph: consolidating multiple edges
        if isinstance(self.networkx_graph, nx.MultiGraph) or isinstance(self.networkx_graph, nx.MultiDiGraph):
            edge_attrs = {}
            for u, v, key, data in self.networkx_graph.edges(keys=True, data=True):
                # Use a tuple of nodes as a key for edge attributes
                edge_key = (u, v)

                # Initialize the list of attributes for this edge
                if edge_key not in edge_attrs:
                    edge_attrs[edge_key] = {'weight': []}

                # Append the weight of the current edge
                edge_attrs[edge_key]['weight'].append(data.get('weight', 1))

            # Add consolidated edges to iGraph
            for edge_key, attrs in edge_attrs.items():
                igraph_graph.add_edge(edge_key[0], edge_key[1])
                for attr_name, attr_list in attrs.items():
                    igraph_graph.es[-1][attr_name] = attr_list
        else:
            # Prepare a list of edges with vertex indices in iGraph
            edges_with_indices = [(igraph_graph.vs.find(name=str(u)).index, igraph_graph.vs.find(name=str(v)).index) for
                                  u, v in self.networkx_graph.edges()]

            # Add edges to iGraph by indices
            igraph_graph.add_edges(edges_with_indices)

            # Transfer edge attributes
            if self.networkx_graph.edges(data=True):
                igraph_graph.es['weight'] = [
                    self.networkx_graph[u][v]['weight'] if 'weight' in self.networkx_graph[u][v] else 1 for u, v in
                    self.networkx_graph.edges()]

        # Transfer node attributes
        for node in self.networkx_graph.nodes():
            ig_node = igraph_graph.vs.find(name=str(node))
            for attr_name, attr_value in self.networkx_graph.nodes[node].items():
                ig_node[attr_name] = attr_value

        return igraph_graph

    def to_igraph_default(self):
        return ig.Graph.from_networkx(self.networkx_graph)


if __name__ == "__main__":
    # Create a networkx MultiDiGraph
    G_nx = nx.MultiDiGraph()

    # Add nodes
    G_nx.add_nodes_from(range(10))

    # Add random edges with random weights
    for _ in range(15):
        u, v = random.sample(range(10), 2)
        for i in range(random.randint(1, 3)):  # Each pair can have between 1 to 3 edges
            G_nx.add_edge(u, v, weight=random.randint(1, 10))

    # Convert to igraph
    converter = GraphConverter(G_nx)
    G_ig = converter.to_igraph()

    # # Visualize the igraph
    # converter.visualize_igraph(G_ig, filename="graph.png")

    # Print the igraph summary
    print(G_ig.summary())


