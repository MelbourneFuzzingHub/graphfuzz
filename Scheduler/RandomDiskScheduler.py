import os
import time
import random
import networkx as nx
import pickle


class RandomDiskScheduler:
    def __init__(self, folder_name):
        self.folder_name = folder_name
        os.makedirs(self.folder_name, exist_ok=True)
        self.start_time = time.time()
        self.graph_counter = 0

    def add_to_corpus(self, graphs):
        if not isinstance(graphs, list):
            graphs = [graphs]  # Ensure graphs is a list

        for graph in graphs:
            self.graph_counter += 1
            filename = f"graph_{self.graph_counter}.pkl"
            file_path = os.path.join(self.folder_name, filename)
            with open(file_path, 'wb') as f:
                pickle.dump(graph, f)

    def get_graph(self):
        if self.graph_counter == 0:
            raise ValueError("No graphs available in memory.")

        random_index = random.randint(1, self.graph_counter)
        file_path = os.path.join(self.folder_name, f"graph_{random_index}.pkl")
        with open(file_path, 'rb') as f:
            return pickle.load(f)

    def close_current_file(self):
        # This method is not required in this context
        pass

    def iterate_graphs(self):
        # Iterate over all graphs in the folder and yield them along with their filenames
        for i in range(1, self.graph_counter + 1):
            file_path = os.path.join(self.folder_name, f"graph_{i}.pkl")
            with open(file_path, 'rb') as f:
                graph = pickle.load(f)
                yield graph


# Example usage
if __name__ == "__main__":
    scheduler = RandomDiskScheduler("graphs_folder")

    # Create some example graphs
    graph1 = nx.complete_graph(5)
    graph2 = nx.cycle_graph(4)

    # Add graphs to the scheduler
    scheduler.add_to_corpus([graph1, graph2])

    # Get a random graph from the scheduler
    random_graph = scheduler.get_graph()
    print("Random Graph:", random_graph)

    # Iterate over all graphs
    for graph in scheduler.iterate_graphs():
        print("Iterated Graph:", graph)
