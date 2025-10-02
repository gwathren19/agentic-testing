import shlex
from langchain.agents import Tool
from tester.runtime.runtime import Runtime

def create_tools(runtime: Runtime):

    def run_python_script(script: str) -> str:
        runtime.activate_venv()
        script = script.rstrip("\n")
        command = f"{runtime.venv_path}/bin/python3 -c {shlex.quote(script)}"
        return runtime.run_command(command)

    def pip_install(packages : str) -> str:
        runtime.activate_venv()
        raw = [s.strip() for s in packages.split(",") if s.strip()]
        if not raw:
            return "Empty install request."

        pkgs_quoted = " ".join(shlex.quote(p) for p in raw)
        command = f"{runtime.venv_path}/bin/pip install --no-cache-dir {pkgs_quoted}"
        try:
            output = runtime.run_command(command)
            checks = []
            for pkg in raw:
                check = runtime.run_command(f"{runtime.venv_path}/bin/python3 -c {shlex.quote(f'import {pkg}; print({pkg}.__version__)')} || echo NOT_FOUND")
                checks.append(f"{pkg}: {check.strip()}")
            return f"Install output:\n{output}\n\nVerification:\n" + "\n".join(checks)
        except Exception as e:
            return f"Error installing packages: {e}"

    def apt_install(packages : str) -> str:
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

    run_python_script_tool = Tool(
        name="run_python_script",
        func=run_python_script,
        description="Run a Python script in the runtime container.",
    )

    pip_install_tool = Tool(
        name="pip_install",
        func=pip_install,
        description="Install Python packages in the runtime container using pip. Provide a comma-separated list of package names.",
    )

    apt_install_tool = Tool(
        name="apt_install",
        func=apt_install,
        description="Install packages in the runtime container using apt-get. Provide a comma-separated list of package names.",
    )

    run_shell_command_tool = Tool(
        name="run_shell_command",
        func=run_command_wrapper,
        description="Execute arbitrary shell commands in the runtime container in case other tools are insufficient.",
    )

    return [run_python_script_tool, pip_install_tool, apt_install_tool, run_shell_command_tool]