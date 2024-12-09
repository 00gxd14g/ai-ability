import os
import yaml
import uuid
import random

def generate_unique_id(existing_ids):
    while True:
        unique_id = f"{random.randint(1000000,9999999)}-{random.randint(100000000,999999999)}-DT"
        if unique_id not in existing_ids:
            return unique_id

def update_yaml_file(file_path, existing_ids, report):
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
            error_msg = f"Error parsing YAML file {file_path}: {e}"
            print(error_msg)
            report['errors'].append(error_msg)
            return

        # Handle both list and dictionary formats
        if isinstance(data, list):
            if len(data) == 1:
                ability = data[0]
            else:
                error_msg = f"File {file_path} contains multiple abilities. Skipping."
                print(error_msg)
                report['errors'].append(error_msg)
                return
        elif isinstance(data, dict):
            ability = data
        else:
            error_msg = f"Unexpected data structure in {file_path}. Skipping."
            print(error_msg)
            report['errors'].append(error_msg)
            return

        # Ensure required fields are present
        required_fields = ['id', 'name', 'description', 'tactic', 'technique', 'platforms']
        missing_fields = [field for field in required_fields if field not in ability]
        if missing_fields:
            error_msg = f"File {file_path} is missing required fields: {', '.join(missing_fields)}. Skipping."
            print(error_msg)
            report['errors'].append(error_msg)
            return

        # Ensure 'id' and file name are unique and the same
        unique_id = generate_unique_id(existing_ids)
        existing_ids.add(unique_id)
        original_id = ability['id']
        ability['id'] = unique_id
        new_file_name = f"{unique_id}.yml"

        # Rename the file to match the new unique ID
        os.rename(file_path, os.path.join(os.path.dirname(file_path), new_file_name))

        # Include DT code in the ability 'name'
        dt_code = original_id  # Assuming the original ID contains the DT code
        if dt_code not in ability['name']:
            ability['name'] = f"{dt_code} - {ability['name']}"
            print(f"Updated ability name to include DT code: {ability['name']}")

        # Validate technique field
        if not isinstance(ability['technique'], dict) or \
           'attack_id' not in ability['technique'] or \
           'name' not in ability['technique']:
            error_msg = f"File {file_path} has invalid 'technique' field. Skipping."
            print(error_msg)
            report['errors'].append(error_msg)
            return

        # Process platforms and commands
        if 'platforms' in ability:
            for platform, executors in ability['platforms'].items():
                if not isinstance(executors, dict):
                    error_msg = f"Invalid executors format in {file_path}. Skipping."
                    print(error_msg)
                    report['errors'].append(error_msg)
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
        new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)
        with open(new_file_path, 'w', encoding='utf-8', newline='\n') as f:
            yaml.dump(ability, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=1000)

        success_msg = f"Successfully updated {new_file_path}"
        print(success_msg)
        report['updated_files'].append(new_file_name)

    except Exception as e:
        error_msg = f"Error processing file {file_path}: {e}"
        print(error_msg)
        report['errors'].append(error_msg)

def update_all_yaml_in_directory(directory):
    existing_ids = set()
    report = {
        'updated_files': [],
        'errors': []
    }
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.yml') or file.endswith('.yaml'):
                file_path = os.path.join(root, file)
                update_yaml_file(file_path, existing_ids, report)

    # Generate report
    with open('update_report.txt', 'w', encoding='utf-8') as report_file:
        report_file.write("Update Report\n")
        report_file.write("=============\n\n")
        report_file.write("Updated Files:\n")
        for updated_file in report['updated_files']:
            report_file.write(f"- {updated_file}\n")
        report_file.write("\nErrors:\n")
        for error in report['errors']:
            report_file.write(f"- {error}\n")

    # If no errors, create the adversary profile file
    if not report['errors']:
        create_adversary_profile(report['updated_files'], directory)
    else:
        print("Errors encountered during processing. Adversary profile not created.")

def create_adversary_profile(updated_files, directory):
    adversary_profile = {
        'id': '36053cb9-a393-4d26-be5d-695df164e466',
        'name': 'BARIKAT 2.0',
        'description': 'Adversary used for BARIKAT',
        'objective': '495a9828-cab1-44dd-a0ca-66e38177d8cc',
        'atomic_ordering': []
    }

    # Extract DT codes from ability names
    dt_codes = []
    for file_name in updated_files:
        ability_file_path = os.path.join(directory, file_name)
        with open(ability_file_path, 'r', encoding='utf-8') as f:
            ability_data = yaml.safe_load(f)
            # Assuming the DT code is the first part of the 'name' field
            ability_name = ability_data.get('name', '')
            dt_code = ability_name.split(' - ')[0]
            dt_codes.append(dt_code)

    # Add DT codes to atomic_ordering
    adversary_profile['atomic_ordering'] = dt_codes

    # Write the adversary profile to a YAML file
    adversary_profile_path = os.path.join(directory, 'barikat_adversary.yml')
    with open(adversary_profile_path, 'w', encoding='utf-8', newline='\n') as f:
        yaml.dump(adversary_profile, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=1000)

    print(f"Adversary profile created at {adversary_profile_path}")

if __name__ == '__main__':
    directory = os.getcwd()  # Current directory or specify your path
    update_all_yaml_in_directory(directory)