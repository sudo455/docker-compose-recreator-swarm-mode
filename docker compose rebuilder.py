import json
import yaml
import subprocess
import os
from collections import defaultdict
import re

def run_docker_command(command):
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise Exception(f"Docker command failed: {e.stderr}")

def get_services_and_stacks():
    output = run_docker_command("sudo docker service ls --format '{{.Name}} {{.Mode}}'")
    services_and_stacks = {}
    for line in output.strip().split('\n'):
        full_name, mode = line.strip().split(maxsplit=1)
        stack_name, service_name = full_name.rsplit('_', 1)
        services_and_stacks[full_name] = {
            'stack': stack_name,
            'service': service_name,
            'mode': mode
        }
    return services_and_stacks

def get_service_inspects(service_names):
    inspects = {}
    for name in service_names:
        output = run_docker_command(f"sudo docker service inspect {name}")
        inspects[name] = json.loads(output)
    return inspects

def get_network_mapping():
    output = run_docker_command("sudo docker network ls --format '{{.ID}} {{.Name}}'")
    return {line.split()[0][:12]: line.split()[1] for line in output.splitlines()}

def sanitize_network_name(name):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)

def parse_docker_inspect(inspect_data, services_and_stacks, network_mapping):
    compose = {
        'version': '3.8',
        'services': {},
        'networks': {},
        'volumes': {}
    }

    for full_service_name, service in inspect_data.items():
        service_spec = service[0]['Spec']
        service_name = services_and_stacks[full_service_name]['service']
        
        service_config = {
            'image': service_spec['TaskTemplate']['ContainerSpec']['Image'].split('@')[0],
            'deploy': {
                'mode': services_and_stacks[full_service_name]['mode'],
                'update_config': {
                    'parallelism': service_spec['UpdateConfig']['Parallelism'],
                    'failure_action': service_spec['UpdateConfig']['FailureAction'],
                    'monitor': f"{service_spec['UpdateConfig']['Monitor'] // 1000000000}s",
                    'max_failure_ratio': service_spec['UpdateConfig']['MaxFailureRatio'],
                    'order': service_spec['UpdateConfig']['Order']
                },
                'rollback_config': {
                    'parallelism': service_spec['RollbackConfig']['Parallelism'],
                    'failure_action': service_spec['RollbackConfig']['FailureAction'],
                    'monitor': f"{service_spec['RollbackConfig']['Monitor'] // 1000000000}s",
                    'max_failure_ratio': service_spec['RollbackConfig']['MaxFailureRatio'],
                    'order': service_spec['RollbackConfig']['Order']
                }
            }
        }

        # Add Args as command if present
        if 'Args' in service_spec['TaskTemplate']['ContainerSpec']:
            service_config['command'] = service_spec['TaskTemplate']['ContainerSpec']['Args']

        # Add environment variables if present
        if 'Env' in service_spec['TaskTemplate']['ContainerSpec']:
            service_config['environment'] = service_spec['TaskTemplate']['ContainerSpec']['Env']

        if 'Replicas' in service_spec['Mode']:
            service_config['deploy']['replicas'] = service_spec['Mode']['Replicas']

        if 'EndpointSpec' in service_spec and 'Ports' in service_spec['EndpointSpec']:
            service_config['ports'] = [
                f"{p['PublishedPort']}:{p['TargetPort']}/{p['Protocol']}"
                for p in service_spec['EndpointSpec']['Ports']
            ]

        if 'Mounts' in service_spec['TaskTemplate']['ContainerSpec']:
            service_config['volumes'] = [
                f"{m['Source']}:{m['Target']}"
                for m in service_spec['TaskTemplate']['ContainerSpec']['Mounts']
            ]

        if 'Networks' in service_spec['TaskTemplate']:
            service_config['networks'] = []
            for net in service_spec['TaskTemplate']['Networks']:
                net_id = net['Target'][:12]
                net_name = sanitize_network_name(network_mapping.get(net_id, net['Target']))
                service_config['networks'].append(net_name)
                compose['networks'][net_name] = {'external': True}

        if 'Labels' in service_spec['TaskTemplate']['ContainerSpec']:
            service_config['labels'] = service_spec['TaskTemplate']['ContainerSpec']['Labels']

        if 'Hostname' in service_spec['TaskTemplate']['ContainerSpec']:
            service_config['hostname'] = service_spec['TaskTemplate']['ContainerSpec']['Hostname']

        if 'StopGracePeriod' in service_spec['TaskTemplate']['ContainerSpec']:
            service_config['stop_grace_period'] = f"{service_spec['TaskTemplate']['ContainerSpec']['StopGracePeriod'] // 1000000000}s"

        compose['services'][service_name] = service_config

    return compose

def create_docker_compose(inspect_data, services_and_stacks, network_mapping):
    compose = parse_docker_inspect(inspect_data, services_and_stacks, network_mapping)
    return yaml.dump(compose, default_flow_style=False)

def save_compose_file(content, path):
    with open(path, 'w') as f:
        f.write(content)

def check_compose_file(compose_content):
    try:
        yaml.safe_load(compose_content)
        return True
    except yaml.YAMLError:
        return False

def main():
    try:
        print("Fetching service and stack information...")
        services_and_stacks = get_services_and_stacks()

        print("Fetching network information...")
        network_mapping = get_network_mapping()

        stacks = set(info['stack'] for info in services_and_stacks.values())

        for stack in stacks:
            print(f"\nProcessing stack: {stack}")
            stack_services = {name: info for name, info in services_and_stacks.items() if info['stack'] == stack}
            print(f"Services in {stack}: {', '.join(info['service'] for info in stack_services.values())}")

            inspect_data = get_service_inspects(stack_services.keys())

            print("Generating Docker Compose file...")
            compose_content = create_docker_compose(inspect_data, services_and_stacks, network_mapping)

            if check_compose_file(compose_content):
                save_path = f"docker-compose-{stack}.yaml"
                save_compose_file(compose_content, save_path)
                print(f"Docker Compose file for {stack} saved as {save_path}")
            else:
                print(f"Generated Docker Compose file for {stack} is not valid. Please check the services and try again.")

        print("\nSummary:")
        for stack in stacks:
            stack_services = [info['service'] for info in services_and_stacks.values() if info['stack'] == stack]
            print(f"Stack: {stack}")
            print(f"  Services: {', '.join(stack_services)}")
            print(f"  Docker Compose file: docker-compose-{stack}.yaml")
            print()

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
