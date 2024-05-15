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


def recursive_find_replace(data, key, value):
    if isinstance(data, str):
        return data.replace(key, value)
    elif isinstance(data, dict):
        return {k: recursive_find_replace(v, key, value) for k, v in data.items()}
    elif isinstance(data, list):
        return [recursive_find_replace(v, key, value) for v in data]
    else:
        return data


def generate_configs(experiments_path, training_path, group_name):
    experiments = load_yaml(experiments_path)
    base_training_config = load_yaml(training_path)
    
    models_dir = (jobs_dir / "../models" / group_name).resolve()
    os.makedirs(models_dir, exist_ok=True)
    
    config_dir = jobs_dir / "config" / group_name
    os.makedirs(config_dir, exist_ok=True)

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
        run_config = recursive_find_replace(runs[run_name], '$MODEL_DIR', str(models_dir))
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
        version = len(os.listdir(jobs_dir / "config" / group_name)) + 1
        config_filename = jobs_dir / f"config/{group_name}/{version:04d}-{run_name}.yaml"
        save_yaml(training_config, config_filename)
        output_files.append(os.path.abspath(config_filename))

    return output_files



def merge_and_schedule(
    experiments_config,
    training_config,
    command,
    queue_name="" # Path to the queue group, e.g. jobs/queue/0_high_priority
):
    queue = jobs_dir / "queued" / queue_name
    # Generate config files for each experiment
    config_files = generate_configs(experiments_config, training_config, queue_name)

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
        name = os.path.basename(config).replace(".yaml", "")
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


def basename(path):
    return path.split("/")[-1].split(".")[0]

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Schedule experiments based on dependencies')
    parser.add_argument('experiments', type=str, help='Path to the experiments YAML file')
    parser.add_argument('training', type=str, help='Path to the training YAML file')
    parser.add_argument('--cmd', type=str, default="accelerate launch -m axolotl.cli.train {config_file}", help='Command that takes a single config file as argument')
    parser.add_argument('--queue', type=str, default='', help='Name of the experiment group')
    parser.add_argument('--priority', type=int, default=100, help='Priority')
    args = parser.parse_args()
    queue = args.queue if args.queue != '' else f'{basename(args.experiments)}-{basename(args.training)}'
    queue = f"{args.priority:04d}_{queue}"
    merge_and_schedule(args.experiments, args.training, args.cmd, queue)
    
if __name__ == "__main__":
    main()
    