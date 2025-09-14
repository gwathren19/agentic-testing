import shlex
from typing import Optional, Dict, Any
from langchain.agents import Tool
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
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


def create_http_get_tool(runtime: Runtime) -> Tool:
    def http_get(
            url,
            headers = None,
            cookies = None,
            use_cookie_jar = False
    ) -> str:
        if not url:
            return "Error: input must be a valid URL."

        command = build_curl_command(
            "GET", url, headers=headers, cookies=cookies,
            use_cookie_jar=use_cookie_jar, cookie_jar=runtime.cookie_jar
        )
        output = runtime.run_command(command)
        if not output.strip():
            return f"No response from {url}. Host may be unreachable."
        return output

    return StructuredTool.from_function(
        name="http_get",
        func=http_get,
        description=(
            "Perform an HTTP GET request to fetch the contents of a webpage or API.\n"
            "Automatically follows redirects (-L).\n"
            "Returns the raw HTTP response body (HTML, JSON, or text)."
            "If the host is unreachable or the response is empty, returns an error message."
        ),
        args_schema=HttpGetRequest,
    )


def create_http_post_tool(runtime: Runtime) -> Tool:
    def http_post(
        url,
        data,
        headers = None,
        cookies = None,
        use_cookie_jar = False
    ) -> str:

        if not url:
            return "Error: input must be a valid URL."
        if not data:
            return "Error: input must be a valid data."

        command = build_curl_command(
            "POST", url, headers=headers, cookies=cookies,
            data=data, use_cookie_jar=use_cookie_jar, cookie_jar=runtime.cookie_jar
        )
        output = runtime.run_command(command)
        if not output.strip():
            return f"No response from {url}. Host may be unreachable."
        return output

    return StructuredTool.from_function(
        name="http_post",
        func=http_post,
        description=(
            "Perform an HTTP POST request to send form data or API requests.\n"
            "Automatically follows redirects (-L).\n"
            "Returns the raw HTTP response body (HTML, JSON, or text)."
            "If the host is unreachable or the response is empty, returns an error message."
        ),
        args_schema=HttpPostRequest,
    )