from lib.get_functions import *
from lib.rdc_snn_cdc_scf_ccf import check_compose_file, create_docker_compose, save_compose_file
from os import mkdir, path

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
        
        if not path.exists("./docker_compose"):

            mkdir("./docker_compose")

        if check_compose_file(compose_content):

            save_path = f"docker_compose/to_be_tested-{stack}.yaml"
            save_compose_file(compose_content, save_path)

            print(f"Docker Compose file for {stack} saved as {save_path}")
        else:

            print(f"Generated Docker Compose file for {stack} is not valid. Please check the services and try again.")

except Exception as e:

    print(f"An error occurred: {str(e)}")
