import shlex
from langchain.agents import Tool
from tester.runtime.runtime import Runtime

from tester.tools.basic_tools.http_requests import create_http_get_tool, create_http_post_tool

def create_tools(runtime: Runtime):

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

    def run_command_wrapper(command: str):
        command = command.rstrip("\n")
        return runtime.run_command(command)


    http_get_tool = create_http_get_tool(runtime)
    http_post_tool = create_http_post_tool(runtime)

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

    fallback_shell_tool = Tool(
        name="fallback_shell",
        func=run_command_wrapper,
        description="Execute arbitrary shell commands in the runtime container in case other tools are insufficient.",
    )

    return [http_get_tool, http_post_tool, port_scan_tool, install_tool, fallback_shell_tool]