from langchain.agents import Tool
from tester.runtime import Runtime

def create_tools(runtime : Runtime):

    def http_get(url : str) -> str:
        command = f"curl -s {url}"
        return runtime.run_command(command)

    def port_scan(host : str) -> str:
        command = f"nmap -p- -sV {host}"
        return runtime.run_command(command)

    http_get_tool = Tool(
        name="http_get",
        func=http_get,
        description="Fetch the contents of a URL using curl.",
    )

    port_scan_tool = Tool(
        name="port_scan",
        func=port_scan,
        description="Scan a host for open ports using nmap service version scan.",
    )

    fallback_shell_tool = Tool(
        name="fallback_shell",
        func=runtime.run_command,
        description="Execute arbitrary shell commands in the runtime container in case other tools are insufficient.",
    )

    return [http_get_tool, port_scan_tool, fallback_shell_tool]