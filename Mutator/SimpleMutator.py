import random
import networkx as nx

class SimpleMutator:
    def __init__(self):
        pass

    def mutate(self, graph):
        mutation_operations = [
            self.add_node,
            self.delete_node,
            self.add_edge,
            self.delete_edge
        ]
        mutation = random.choice(mutation_operations)
        return mutation(graph)

    def nx_has_weighted_edges(self, nx_graph):
        for _, _, data in nx_graph.edges(data=True):
            if 'weight' in data:
                return True
        return False

    def add_node(self, graph):
        new_node = max(graph.nodes) + 1 if graph.nodes else 0
        graph.add_node(new_node)
        return graph

    def delete_node(self, graph):
        if graph.nodes:
            node_to_remove = random.choice(list(graph.nodes))
            graph.remove_node(node_to_remove)
        return graph

    def add_edge(self, graph):
        nodes = list(graph.nodes)
        if not nodes:
            graph.add_node(0)
            graph.add_node(1)
            node1, node2 = 0, 1
        elif len(nodes) == 1:
            graph.add_node(max(nodes) + 1)
            node1, node2 = nodes[0], max(nodes)
        else:
            attempts = 0
            max_attempts = 100
            node1, node2 = random.sample(nodes, 2)
            # Skip the edge existence check if the graph is a multigraph
            if not graph.is_multigraph():
                while graph.has_edge(node1, node2) and attempts < max_attempts:
                    node1, node2 = random.sample(nodes, 2)
                    attempts += 1
            if attempts == max_attempts:
                # Handle the case where a new edge couldn't be added after max_attempts
                new_node = max(graph.nodes) + 1
                graph.add_node(new_node)
                node1 = new_node
                node2 = random.choice(nodes)

        # If the graph has edge weights, assign a weight
        weight = random.randint(1, 500)
        if any(data.get('weight', 0) < 0 for _, _, data in graph.edges(data=True)):
            weight *= random.choice([-1, 1])
        graph.add_edge(node1, node2, weight=weight)
        return graph

    def delete_edge(self, graph):
        if graph.edges:
            edge_to_remove = random.choice(list(graph.edges))
            graph.remove_edge(*edge_to_remove)
        return graph