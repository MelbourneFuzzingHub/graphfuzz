import os
import pickle
import time
import uuid

import networkx as nx
import random


class RandomDiskSchedulerUpdated:
    def __init__(self, batch_prefix, start_time, batch_size=1000, corpus_dir='../Corpus_Data'):
        self.current_file = None
        self.batch_size = batch_size
        self.batch_prefix = batch_prefix
        self.corpus_dir = corpus_dir
        self.batch_id = 1
        self.graph_counter = 0
        self.start_time = start_time
        self.ensure_corpus_dir()
        self.instance_id = uuid.uuid4().hex[:10]
        print(f'Corpus_Data id: {self.instance_id}')

    def ensure_corpus_dir(self):
        if not os.path.exists(self.corpus_dir):
            os.makedirs(self.corpus_dir)

    def add_to_corpus(self, graph):
        timestamp = time.time() - self.start_time
        self.graph_counter += 1
        # print(f'self.graph_counter{self.graph_counter}')

        # Open a new file if starting a new batch
        if self.graph_counter % self.batch_size == 1 or self.current_file is None:
            if self.current_file is not None:
                self.current_file.close()
            file_path = os.path.join(self.corpus_dir,
                                     f'{self.batch_prefix}_{self.instance_id}_batch_{self.batch_id}.pkl')
            self.current_file = open(file_path, 'wb')
            self.batch_id += 1

        # Write the graph to the file
        pickle.dump((self.graph_counter, timestamp, graph), self.current_file)
        self.current_file.flush()

        # Close the file if the batch is complete
        if self.graph_counter % self.batch_size == 0:
            self.current_file.close()
            self.current_file = None

    def close_current_file(self):
        if self.current_file is not None:
            self.current_file.close()
            self.current_file = None

    def get_graph(self):
        if self.graph_counter == 0:
            raise ValueError("No graphs available.")

        # Randomly select a batch file
        selected_batch_id = random.randint(1, self.batch_id - 1)
        file_name = f'{self.batch_prefix}_{self.instance_id}_batch_{selected_batch_id}.pkl'
        file_path = os.path.join(self.corpus_dir, file_name)

        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                # Load all graphs from the selected file
                graphs = []
                while True:
                    try:
                        _, _, graph = pickle.load(f)
                        graphs.append(graph)
                    except EOFError:
                        break

                # Randomly select a graph from the loaded graphs
                if graphs:
                    graph = random.choice(graphs)
                    return graph
                else:
                    # print(file_name)
                    raise ValueError("Selected batch file is empty.")

        else:
            raise ValueError("Selected batch file does not exist.")

    def iterate_graphs(self):
        # Iterate over all saved files and yield graphs along with their timestamps
        for batch_id in range(1, self.batch_id):
            file_name = f'{self.batch_prefix}_{self.instance_id}_batch_{batch_id}.pkl'
            file_path = os.path.join(self.corpus_dir, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    graph_count = 0
                    while True:
                        try:
                            _, timestamp, graph = pickle.load(f)
                            graph_count += 1
                            batch_graph_id = f"Batch {batch_id}, Graph {graph_count}"
                            yield timestamp, graph, batch_graph_id
                        except EOFError:
                            #  print("EOFError")
                            break

# Usage
# scheduler = RandomDiskScheduler(batch_prefix='stpl', start_time=time.time())
# for _ in range(12000):  # Adding 12000 graphs for demonstration
#     scheduler.add_to_corpus(nx.gnm_random_graph(5, 10))
# scheduler.close_current_file()  # Close the file after adding all graphs
# for timestamp, graph in scheduler.iterate_graphs():
#     print(f"Timestamp: {timestamp}, Graph: {graph}")
# Get a random graph
# timestamp, graph = scheduler.get_graph()
# print(f"Timestamp: {timestamp}, Graph: {graph}")
