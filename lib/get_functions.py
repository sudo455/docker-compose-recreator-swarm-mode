
from lib.rdc_snn_cdc_scf_ccf import run_docker_command
from json import loads

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
        inspects[name] = loads(output)

    return inspects

def get_network_mapping():

    output = run_docker_command("sudo docker network ls --format '{{.ID}} {{.Name}}'")
    return {line.split()[0][:12]: line.split()[1] for line in output.splitlines()}
