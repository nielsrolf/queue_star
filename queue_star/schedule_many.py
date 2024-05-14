import yaml
import os
from collections import deque
from xml.etree import ElementTree as ET
from xml.dom import minidom

from config import jobs_dir



def load_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def save_yaml(data, file_path):
    with open(file_path, 'w') as file:
        yaml.dump(data, file, sort_keys=False, default_flow_style=False)

def topological_sort(dependencies):
    # Calculate in-degrees of each node
    in_degree = {node: 0 for node in dependencies}
    for deps in dependencies.values():
        for d in deps:
            in_degree[d] += 1

    # Find all nodes with no incoming edges (in-degree zero)
    queue = deque([node for node in in_degree if in_degree[node] == 0])
    sorted_list = []

    while queue:
        node = queue.popleft()
        sorted_list.append(node)
        for dependent in dependencies[node]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(sorted_list) != len(dependencies):
        raise ValueError("A cycle was detected in the graph, check dependencies!")

    return sorted_list

def run_name_to_model_dir(run_name):
    os.makedirs("models", exist_ok=True)
    return f"models/{run_name}"

def generate_configs(experiments_path, training_path):
    experiments = load_yaml(experiments_path)
    base_training_config = load_yaml(training_path)

    dependencies = {}
    runs = experiments['runs']

    # Build dependency graph
    for run_name, run_config in runs.items():
        start_at = run_config.get('start-at')
        dependencies[run_name] = [start_at] if start_at in runs else []

    # Topological sort of runs based on dependencies
    sorted_run_names = topological_sort(dependencies)

    output_files = []
    for run_name in sorted_run_names:
        run_config = runs[run_name]
        training_config = base_training_config.copy()  # Deep copy of the base training config

        # Update dataset path
        dataset_key = run_config.pop('train-on')
        if dataset_key in experiments['datasets']:
            dataset_path = experiments['datasets'][dataset_key]
            training_config['datasets'][0]['path'] = dataset_path
            training_config['datasets'][0]['data_files'] = dataset_path
            
        # Set the base model and output dir and optional overrides
        training_config.update(**run_config)
        
        # Create a new file for each config
        config_filename = jobs_dir / f"config/{run_name}.yaml"
        save_yaml(training_config, config_filename)
        output_files.append(os.path.abspath(config_filename))

    return output_files



def merge_and_schedule(
    experiments_config,
    training_config,
    command="accelerate launch -m axolotl.cli.train {config_file}",
    queue=jobs_dir / "queued" # Path to the queue group, e.g. jobs/queue/0_high_priority
):
    # Generate config files for each experiment
    config_files = generate_configs(experiments_config, training_config)

    # Create the queue directory if it doesn't exist
    os.makedirs(queue, exist_ok=True)

    commands = [command.format(config_file=os.path.abspath(config_file)) for config_file in config_files]
    
    # Write the commands to the queue
    todo_file = queue / "todo.xml"
    try:
        tree = ET.parse(todo_file)
    except (FileNotFoundError, ET.ParseError):
        root = ET.Element("jobs")
        tree = ET.ElementTree(root)
    root = tree.getroot()
    # Add <job> elements to the bottom of the XML file
    for config, command in zip(config_files, commands):
        version = len(os.listdir(jobs_dir / "config")) + 1
        name = os.path.basename(config).replace(".yaml", f"-v{version}")
        job = ET.Element("job", name=name)
        job.text = command
        root.append(job)
    # Pretty print the XML
    pretty_xml_str = ET.tostring(root, encoding="utf-8").decode().replace("><", ">\n<")
    # pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="")

    # Write to file
    with open(todo_file, "w") as f:
        f.write(pretty_xml_str)
    print(f"Wrote {len(commands)} jobs to {todo_file}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Schedule experiments based on dependencies')
    parser.add_argument('experiments', type=str, help='Path to the experiments YAML file')
    parser.add_argument('training', type=str, help='Path to the training YAML file')
    args = parser.parse_args()
    merge_and_schedule(args.experiments, args.training)
    
if __name__ == "__main__":
    main()
    