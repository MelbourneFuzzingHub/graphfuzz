import time
import random


class RandomMemScheduler:
    def __init__(self, start_time):
        self.corpus_memory = []
        self.start_time = start_time
        self.graph_counter = 0

    def add_to_corpus(self, graphs):
        if not isinstance(graphs, list):
            graphs = [graphs]  # Ensure graphs is a list

        for graph in graphs:
            timestamp = time.time() - self.start_time  # Get current time in seconds since epoch
            self.graph_counter += 1
            self.corpus_memory.append((timestamp, graph, self.graph_counter))

    def get_graph(self):
        if not self.corpus_memory:
            raise ValueError("No graphs available in memory.")

        # Randomly select a graph from memory
        _, graph, _ = random.choice(self.corpus_memory)
        return graph

    def close_current_file(self):
        return

    def iterate_graphs(self):
        # Iterate over all graphs in memory and yield them along with their timestamps
        for timestamp, graph, counter in self.corpus_memory:
            yield timestamp, graph, counter
