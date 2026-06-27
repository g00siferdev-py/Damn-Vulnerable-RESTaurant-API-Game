import re
import shlex
import subprocess


def get_disk_usage(parameters: str):
    # Build the command as a list and execute it without a shell.
    # If user-supplied parameters are provided, split them safely with
    # shlex and validate each token against an allowlist.
    command = ["df", "-h"]

    if parameters:
        args = shlex.split(parameters)
        for arg in args:
            if not re.match(r"^[a-zA-Z0-9_/.@-]+$", arg):
                raise ValueError("Invalid disk usage parameter")
        command.extend(args)

    try:
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False
        )
        usage = result.stdout.strip().decode()
    except Exception:
        raise Exception("An unexpected error was observed")

    return usage
