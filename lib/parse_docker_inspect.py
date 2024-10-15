from lib.rdc_snn_cdc_scf_ccf import sanitize_network_name

def parse_docker_inspect(inspect_data, services_and_stacks, network_mapping):

    compose = {
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
