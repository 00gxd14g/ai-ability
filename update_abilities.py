import os
import yaml
import uuid

def update_yaml_file(file_path, existing_ids):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Normalize line endings
        content = content.replace('\r\n', '\n')

        # Remove '---' from the start if present
        if content.startswith('---'):
            content = content.lstrip('---\n').lstrip()

        # Load YAML content
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {file_path}: {e}")
            return

        # Handle both list and dictionary formats
        if isinstance(data, list):
            if len(data) == 1:
                ability = data[0]
            else:
                print(f"File {file_path} contains multiple abilities. Skipping.")
                return
        elif isinstance(data, dict):
            ability = data
        else:
            print(f"Unexpected data structure in {file_path}. Skipping.")
            return

        # Ensure required fields are present
        required_fields = ['id', 'name', 'description', 'tactic', 'technique', 'platforms']
        missing_fields = [field for field in required_fields if field not in ability]
        if missing_fields:
            print(f"File {file_path} is missing required fields: {', '.join(missing_fields)}. Skipping.")
            return

        # Ensure 'id' is unique
        original_id = ability['id']
        while ability['id'] in existing_ids:
            ability['id'] = str(uuid.uuid4())
            print(f"Updated ability ID from {original_id} to {ability['id']} to ensure uniqueness.")
        existing_ids.add(ability['id'])

        # Include DT code in the ability 'name'
        dt_code = os.path.splitext(os.path.basename(file_path))[0]
        if dt_code not in ability['name']:
            ability['name'] = f"{dt_code} - {ability['name']}"
            print(f"Updated ability name to include DT code: {ability['name']}")

        # Validate technique field
        if not isinstance(ability['technique'], dict) or \
           'attack_id' not in ability['technique'] or \
           'name' not in ability['technique']:
            print(f"File {file_path} has invalid 'technique' field. Skipping.")
            return

        # Process platforms and commands
        if 'platforms' in ability:
            for platform, executors in ability['platforms'].items():
                if not isinstance(executors, dict):
                    print(f"Invalid executors format in {file_path}. Skipping.")
                    return
                for executor_name, executor_data in executors.items():
                    # Remove problematic characters from 'command'
                    if 'command' in executor_data:
                        cmd = executor_data['command']
                        if isinstance(cmd, list):
                            cmd = ' && '.join(cmd)
                        cmd = cmd.strip().replace("'", "").replace('"', "")
                        executor_data['command'] = cmd

                    # Set empty cleanup if not present or convert to proper format
                    if 'cleanup' not in executor_data or not executor_data['cleanup']:
                        executor_data['cleanup'] = ''
                    else:
                        cleanup = executor_data['cleanup']
                        if isinstance(cleanup, list):
                            cleanup = ' && '.join(cleanup)
                        cleanup = cleanup.strip().replace("'", "").replace('"', "")
                        executor_data['cleanup'] = cleanup

                    # Ensure parsers are properly formatted
                    if 'parsers' in executor_data:
                        if isinstance(executor_data['parsers'], dict):
                            for parser_name, parser_list in executor_data['parsers'].items():
                                if isinstance(parser_list, list):
                                    executor_data['parsers'][parser_name] = [
                                        {'source': item['source']} if isinstance(item, dict) and 'source' in item else item
                                        for item in parser_list
                                    ]

        # Write the updated YAML without adding '---\n'
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            yaml.dump(ability, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=1000)

        print(f"Successfully updated {file_path}")

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def update_all_yaml_in_directory(directory):
    existing_ids = set()
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.yml') or file.endswith('.yaml'):
                file_path = os.path.join(root, file)
                update_yaml_file(file_path, existing_ids)

if __name__ == '__main__':
    directory = os.getcwd()  # Current directory or specify your path
    update_all_yaml_in_directory(directory)