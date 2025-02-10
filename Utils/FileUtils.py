import os
import pickle
import site

import networkx as nx


def save_discrepancies(discrepancy_data, file_path, max_discrepancies_per_msg=100):
    """Save the discrepancy graphs to a pickle file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    log_dir = os.path.join(parent_dir, "Log")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    discrepancy_file_path = os.path.join(log_dir, file_path)

    existing_discrepancy_data = []
    if os.path.exists(discrepancy_file_path):
        with open(discrepancy_file_path, "rb") as f:
            existing_discrepancy_data = pickle.load(f)

    for msg, graph in discrepancy_data:
        if existing_discrepancy_data.count(msg) < max_discrepancies_per_msg:
            existing_discrepancy_data.append((msg, graph))

    with open(discrepancy_file_path, "wb") as f:
        pickle.dump(existing_discrepancy_data, f)


def save_discrepancy(discrepancy_data, file_path, max_discrepancies_per_msg=100):
    """Save a single discrepancy graph to a pickle file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    log_dir = os.path.join(parent_dir, "Log")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    discrepancy_file_path = os.path.join(log_dir, file_path)

    existing_discrepancy_data = []
    if os.path.exists(discrepancy_file_path):
        try:
            with open(discrepancy_file_path, "rb") as f:
                existing_discrepancy_data = pickle.load(f)
        except EOFError:
            print(f"Warning: File {discrepancy_file_path} was empty or corrupted. Starting a new file.")

    msg, graph, timestamp = discrepancy_data
    discrepancy_messages = [msg for msg, _, _ in existing_discrepancy_data]

    if discrepancy_messages.count(msg) < max_discrepancies_per_msg:
        existing_discrepancy_data.append((msg, graph, timestamp))

    with open(discrepancy_file_path, "wb") as f:
        pickle.dump(existing_discrepancy_data, f)


def save_exception_graphs(exception_graphs, prefix):
    """Saves the exception graphs to a pickle file with a given prefix."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    log_dir = os.path.join(parent_dir, "Log")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    filename = f"{prefix}_exceptions.pkl"
    file_path = os.path.join(log_dir, filename)
    with open(file_path, 'wb') as file:
        pickle.dump(exception_graphs, file)
    print(f"Exception graphs saved to {file_path}")


# def update_coveragerc(filepaths):
#     # Convert filepaths to a list if it's a single path
#     if isinstance(filepaths, str):
#         filepaths = [filepaths]
#
#     # Find site-packages directory
#     site_packages = next((p for p in site.getsitepackages() if 'site-packages' in p), None)
#
#     # Initialize the content for .coveragerc
#     coveragerc_content = "[run]\nsource =\n    networkx\n\n[report]\ninclude =\n"
#
#     total_lines = []
#
#     # Process each file path
#     for file_path in filepaths:
#         # Path to the specified file in site-packages
#         full_file_path = os.path.join(site_packages, file_path)
#
#         # Check if the file exists
#         if not os.path.exists(full_file_path):
#             print(f"File {full_file_path} not found.")
#             continue
#
#         # Append file path to .coveragerc content
#         coveragerc_content += f"    {full_file_path}\n"
#
#         # Count lines in the current file
#         total_lines.append(count_lines_in_file(full_file_path))
#
#     # Write to .coveragerc in current directory
#     coveragerc_path = os.path.join(os.getcwd(), '.coveragerc')
#     with open(coveragerc_path, 'w') as file:
#         file.write(coveragerc_content.strip())
#     print(f".coveragerc updated and saved in {os.getcwd()}")
#
#     return total_lines

# Version in Ubuntu
# def update_coveragerc(filepaths):
#     # Convert filepaths to a list if it's a single path
#     if isinstance(filepaths, str):
#         filepaths = [filepaths]
#
#     # Get all site-packages directories including the user-specific one
#     # site_packages_dirs = site.getsitepackages()
#     site_packages_dirs = ['/home/ubuntu/.local/lib/python3.8/site-packages']
#
#     # Initialize the content for .coveragerc
#     coveragerc_content = "[run]\nsource =\n    networkx\n\n[report]\ninclude =\n"
#
#     total_lines = []
#
#     # Process each file path
#     for file_path in filepaths:
#         file_found = False
#
#         # Check each site-packages directory
#         for site_packages in site_packages_dirs:
#             # print(f'site_packages_dirs{site_packages_dirs}')
#             # Path to the specified file in site-packages
#             full_file_path = os.path.join(site_packages, file_path)
#             # print(f'full_file_path{full_file_path}')
#
#             # Check if the file exists
#             if os.path.exists(full_file_path):
#                 # Append file path to .coveragerc content
#                 coveragerc_content += f"    {full_file_path}\n"
#                 file_found = True
#
#                 # Count lines in the current file
#                 total_lines.append(count_lines_in_file(full_file_path))
#                 break
#
#         if not file_found:
#             print(f"File {file_path} not found in any site-packages directories.")
#
#     # Write to .coveragerc in current directory
#     coveragerc_path = os.path.join(os.getcwd(), '.coveragerc')
#     with open(coveragerc_path, 'w') as file:
#         file.write(coveragerc_content.strip())
#     print(f".coveragerc updated and saved in {os.getcwd()}")
#
#     return total_lines


def count_lines_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return sum(1 for line in file)


def update_coveragerc():
    # Update .coveragerc content
    coveragerc_content = f"""
        [run]
        source =
            networkx
        """

    # Write to .coveragerc in current directory
    coveragerc_path = os.path.join(os.getcwd(), '.coveragerc')
    with open(coveragerc_path, 'w') as file:
        file.write(coveragerc_content)
    print(f".coveragerc updated and saved in {os.getcwd()}")


def save_graphs(graphs, file_name):
    # Ensure the Corpus_Data directory exists
    corpus_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Corpus_Data')
    if not os.path.exists(corpus_dir):
        os.makedirs(corpus_dir)

    file_path = os.path.join(corpus_dir, file_name)

    # Check if the file already exists
    if not os.path.exists(file_path):
        # Save the graphs using pickle
        with open(file_path, 'wb') as f:
            pickle.dump(graphs, f)
        print(f"Saved graphs to {file_name}")
    else:
        print(f"File {file_name} already exists. Skipping save.")


def load_graphs(file_name):
    # The path to the Corpus_Data directory
    corpus_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Corpus_Data')

    # Load the graphs using pickle
    with open(os.path.join(corpus_dir, file_name), 'rb') as f:
        graphs = pickle.load(f)

    return graphs


def create_single_node_graph():
    # Create an empty graph
    G = nx.Graph()

    # Add a single node. 
    G.add_node(1)

    # Return the graph object
    return G

def create_single_node_digraph():
    # Create an empty graph
    G = nx.DiGraph()

    # Add a single node. 
    G.add_node(1)

    # Return the graph object
    return G