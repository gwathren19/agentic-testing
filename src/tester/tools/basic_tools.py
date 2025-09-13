import shlex
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain.agents import Tool
from tester.runtime.runtime import Runtime

class HttpRequestBase(BaseModel):
    url: str = Field(..., description="The target URL to send the request to")

class HttpGetRequest(HttpRequestBase):
    headers: Optional[Dict[str, str]] = Field(default=None, description="Headers to include in the request")
    cookies: Optional[Any] = Field(default=None, description="Cookies to include in the request")
    use_cookie_jar: Optional[bool] = Field(default=False, description="Whether to use a cookie jar for session management")

class HttpPostRequest(HttpRequestBase):
    data: str = Field(..., description="The request body to send in application/x-www-form-urlencoded format")
    headers: Optional[Dict[str, str]] = Field(default=None, description="Headers to include in the request")
    cookies: Optional[Any] = Field(default=None, description="Cookies to include in the request")
    use_cookie_jar: Optional[bool] = Field(default=False, description="Whether to use a cookie jar for session management")

def build_curl_command(method: str, 
                       url: str, 
                       headers: Optional[Dict[str, str]] = None, 
                       cookies: Optional[Any] = None, 
                       data: Optional[str] = None, 
                       use_cookie_jar: Optional[bool] = False, 
                       cookie_jar: Optional[str] = None
) -> str:
    cmd = ["curl", "-sL"]
    if method.upper() == "POST":
        cmd.append("-X POST")
    if headers:
        for key, value in headers.items():
            cmd.append(f"-H {shlex.quote(f'{key}: {value}')}")
    if cookies:
        if isinstance(cookies, dict):
            cookie_str = "; ".join(f"{key}={value}" for key, value in cookies.items())
        else:
            cookie_str = str(cookies)
        cmd.append(f"-b {shlex.quote(cookie_str)}")
    if use_cookie_jar and cookie_jar:
        cmd.append(f"--cookie-jar {shlex.quote(cookie_jar)}")
    if data is not None and data != "":
        cmd.append(f"-d {shlex.quote(data)}")
    
    cmd.append(shlex.quote(url))
    return " ".join(cmd)

def create_tools(runtime : Runtime):

    def http_get(args: HttpGetRequest) -> str:
        url = args.url.strip()
        headers = args.headers
        cookies = args.cookies
        use_cookie_jar = args.use_cookie_jar

        if not url:
            return "Error: input must be a valid URL."

        command = build_curl_command("GET", url, headers=headers, cookies=cookies, use_cookie_jar=use_cookie_jar, cookie_jar=runtime.cookie_jar)
        output = runtime.run_command(command)
        if not output.strip():
            return f"No response from {url}. Host may be unreachable."
        return output

    def http_post(args: HttpPostRequest) -> str:
        url = args.url.strip()
        headers = args.headers
        cookies = args.cookies
        data = args.data.strip()
        use_cookie_jar = args.use_cookie_jar

        if not url:
            return "Error: input must be a valid URL."
        if not data:
            return "Error: input must be a valid data."

        command = build_curl_command("POST", url, headers=headers, cookies=cookies, data=data, use_cookie_jar=use_cookie_jar, cookie_jar=runtime.cookie_jar)
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

    def run_command_wrapper(command: str):
        command = command.rstrip("\n")
        return runtime.run_command(command)

    http_get_tool = Tool(
        name="http_get",
        func=http_get,
        description=(
            "Fetch the contents of a URL using HTTP GET. "
            "Follows redirects automatically (-L). Maintains session state using cookies. "
            "Input: the URL as a string. Returns raw HTML or JSON content."
        ),
    )

    http_post_tool = Tool(
        name="http_post",
        func=http_post,
        description=(
            "Send data to a URL using HTTP POST. "
            "Follows redirects automatically (-L) and maintains session cookies. "
            "Inputs: 'url' string and 'data' string (e.g., 'username=admin&password=password'). "
            "Use this to submit login forms, APIs, or any POST request with arbitrary fields."
        ),
        args=["url", "data"]
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

    fallback_shell_tool = Tool(
        name="fallback_shell",
        func=run_command_wrapper,
        description="Execute arbitrary shell commands in the runtime container in case other tools are insufficient.",
    )

    return [http_get_tool, http_post_tool, port_scan_tool, install_tool, fallback_shell_tool]