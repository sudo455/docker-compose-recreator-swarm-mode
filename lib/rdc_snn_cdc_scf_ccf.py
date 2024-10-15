
from re import sub
from subprocess import run, PIPE, CalledProcessError
from yaml import dump, safe_load, YAMLError
from lib.parse_docker_inspect import parse_docker_inspect

def run_docker_command(command):
    
    try:

        result = run(command, stdout=PIPE, stderr=PIPE, text=True, shell=True, check=True)

        return result.stdout
    except CalledProcessError as e:

        raise Exception(f"Docker command failed: {e.stderr}")

def sanitize_network_name(name):

    return sub(r'[^a-zA-Z0-9_-]', '_', name)


def create_docker_compose(inspect_data, services_and_stacks, network_mapping):

    compose = parse_docker_inspect(inspect_data, services_and_stacks, network_mapping)
    return dump(compose, default_flow_style=False)

def save_compose_file(content, path):

    with open(path, 'w') as f:

        f.write(content)

def check_compose_file(compose_content):

    try:

        safe_load(compose_content)
        return True

    except YAMLError:

        return False
