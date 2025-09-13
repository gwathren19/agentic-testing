import docker
import time
import shlex
from tester.config import *
from tester.utils.logger import logger

class Runtime:
    def __init__(self):
        self.client = docker.from_env()
        self.container = None
        self.cookie_jar = f"/home/tester/cookie_jar.txt"

    def start_container(self, session_id : str = "1"):
        self.container_name = f"{RUNTIME_CONTAINER_NAME}{session_id}"
        logger.info(f"Starting container {self.container_name}")
        try:
            self.container = self.client.containers.run(
                f"{RUNTIME_IMAGE_NAME}:{RUNTIME_IMAGE_TAG}",
                name=self.container_name,
                detach=True,
                stdin_open=True,
                tty=True,
                network=RUNTIME_NETWORK_NAME,
                mem_limit=RUNTIME_MEM_LIMIT,
                remove=True,
                cap_drop=["ALL"],
                cap_add=["SETUID", "SETGID", "DAC_OVERRIDE", "CHOWN", "FOWNER", "NET_RAW"],
                user="tester",
                working_dir="/home/tester",
            )
            time.sleep(1)
            logger.info(f"Container {self.container_name} started")
        except docker.errors.APIError as e:
            logger.error(f"Error starting container {self.container_name}: {e}")

    def run_command(self, command):
        logger.info(f"Running command in container {self.container_name}: {command}")
        if not self.container:
            raise RuntimeError("Container not started")
        try:
            command = shlex.quote(command)
            exec_id = self.client.api.exec_create(self.container.id, f"bash -c {command}")
            output = self.client.api.exec_start(exec_id, detach=False, tty=False, stream=False)
            return output.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error running command in container {self.container_name}: {e}")

    def stop_container(self):
        logger.info(f"Stopping container {self.container_name}")
        if not self.container:
            raise RuntimeError("Container not started")
        try:
            self.container.stop()
            self.container = None
            logger.info(f"Container {self.container_name} stopped")
        except docker.errors.APIError as e:
            logger.error(f"Error stopping container {self.container_name}: {e}")