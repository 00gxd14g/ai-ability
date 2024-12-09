import os
import yaml

def update_yaml_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # Remove '---' from the start if present
    if content.startswith('---'):
        content = content.lstrip('---\n').lstrip()

    # Load the YAML content
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {file_path}: {e}")
        return

    # If data is a list, convert it to a dict (unwrap list)
    if isinstance(data, list):
        if len(data) == 1:
            data = data[0]
        else:
            print(f"File {file_path} contains multiple documents. Skipping.")
            return

    # Ensure required fields are present
    required_fields = ['id', 'name', 'description', 'tactic', 'technique', 'platforms']
    for field in required_fields:
        if field not in data:
            print(f"File {file_path} is missing required field '{field}'. Skipping.")
            return

    # Ensure 'technique' contains 'attack_id' and 'name'
    if 'attack_id' not in data['technique'] or 'name' not in data['technique']:
        print(f"File {file_path} has incomplete 'technique' field. Skipping.")
        return

    # Write back the corrected YAML
    with open(file_path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, width=1000)

def update_all_yaml_in_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.yml'):
                file_path = os.path.join(root, file)
                update_yaml_file(file_path)
                print(f"Updated {file_path}")

if __name__ == '__main__':
    # Use the current working directory
    directory = os.getcwd()
    update_all_yaml_in_directory(directory) 