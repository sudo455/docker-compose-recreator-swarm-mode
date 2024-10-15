# Docker Compose Rebuilder

This Python script rebuilds Docker Compose files from existing Docker Swarm services. It's particularly useful for recreating or backing up your Docker Swarm configuration in a Docker Compose format.

## How It Works

The script performs the following steps:

1. Fetches information about all running Docker services and their associated stacks.
2. Retrieves network information to map network IDs to names.
3. For each stack:
   - Inspects all services within the stack.
   - Parses the inspection data to extract relevant configuration details.
   - Generates a Docker Compose file that represents the stack's services.
   - Validates the generated Docker Compose file.
   - Saves the file if it's valid.

## Features

- Rebuilds Docker Compose files for multiple stacks.
- Includes service configurations such as image, deploy settings, ports, volumes, networks, labels, and more.
- Maps network IDs to their actual names for better readability.
- Performs validation on the generated Docker Compose files.

## Prerequisites

- Python 3.x
- Docker Swarm running on the system
- Sudo access to run Docker commands

## Required Python Libraries

- `json`
- `yaml`
- `subprocess`
- `os`
- `collections`

## Usage

1. Ensure you have the necessary permissions to run Docker commands.
2. Place the script in a directory where you have write permissions.
3. Place the script in a manager node.
4. Run the script with sudo:

   ```bash
   sudo python3 main.py
   ```

## Output

- The script will print progress information as it runs.
- For each stack, it will create a Docker Compose file named `to_be_tested--<stack_name>.yaml`.

## Error Handling

- If any errors occur during the process, they will be caught and printed to the console.
- If a generated Docker Compose file is invalid, the script will notify you and skip saving that file.

## Notes

- Network configurations are set to `external: true` in the generated files, assuming they are pre-existing networks in your Swarm.
- The script does currently include environment variables in the output YAML files. If your services rely on specific environment variables, you'll need to edit these manually to the generated Docker Compose files.

## Limitations

- The script may not capture all possible Docker Swarm configurations. Complex setups might require manual adjustments to the generated Docker Compose files.
- Secrets and configs are not currently handled by this script.

## Contributing

Feel free to fork this repository and submit pull requests for any enhancements or bug fixes.

## License

[GNU GENERAL PUBLIC LICENSE Version 3](https://github.com/sudo455/docker-compose-recreator-swarm-mode/blob/main/LICENSE)
