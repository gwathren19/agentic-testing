import shlex
from langchain.agents import Tool
from tester.runtime.runtime import Runtime

def create_tools(runtime : Runtime):

    def http_get(url : str) -> str:
        command = f"curl -sL {url}"
        output = runtime.run_command(command)
        if not output.strip():
            return f"No response from {url}. Host may be unreachable."
        return output

    def port_scan(host : str) -> str:
        command = f"nmap -p- -sV {host}"
        output = runtime.run_command(command)
        if not output.strip():
            return f"No response from {host}. Host may be unreachable."
        return output

    def install_package(packages : str) -> str:
        raw = [s.strip().lower() for s in packages.split(",") if s.strip()]
        if not raw:
            return "Empty install request."

        pkgs_quoted = " ".join(shlex.quote(p) for p in raw)
        command = (
            f"export DEBIAN_FRONTEND=noninteractive && "
            f"sudo apt-get update -y && sudo apt-get install -y --no-install-recommends {pkgs_quoted}"
        )
        try:
            output = runtime.run_command(command)
            checks = []
            for pkg in raw:
                check = runtime.run_command(f"which {shlex.quote(pkg)} || echo NOT_FOUND")
                checks.append(f"{pkg}: {check.strip()}")
            return f"Install output:\n{output}\n\nVerification:\n" + "\n".join(checks)
        except Exception as e:
            return f"Error installing packages: {e}"

    http_get_tool = Tool(
        name="http_get",
        func=http_get,
        description="Fetch the contents of a URL using curl with -L option set to follow redirects.",
    )

    port_scan_tool = Tool(
        name="port_scan",
        func=port_scan,
        description="Scan a host for open ports using nmap service version scan.",
    )

    install_tool = Tool(
        name="install_package",
        func=install_package,
        description="Install packages in the runtime container using apt-get. Provide a comma-separated list of package names.",
    )

    def run_command_safe(command: str):
        command = command.rstrip("\n")  # remove only trailing newlines
        from tester.utils.logger import logger
        logger.info(f"Running command in container {runtime.container_name}: {repr(command)}")
        return runtime.run_command(command)

    fallback_shell_tool = Tool(
        name="fallback_shell",
        func=run_command_safe,
        description="Execute arbitrary shell commands in the runtime container in case other tools are insufficient.",
    )

    return [http_get_tool, port_scan_tool, install_tool, fallback_shell_tool]