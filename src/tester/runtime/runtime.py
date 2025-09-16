import docker
import time
import shlex
from tester.utils.logger import logger
from tester.utils.config import config

class Runtime:
    def __init__(self, session_id : str = "1"):
        self.client = docker.from_env()
        self.container = None
        self.session_id = session_id
        self.container_name = f"{config.runtime.container_name}{self.session_id}"
        self.cookie_jar = f"/home/tester/cookie_jar.txt"

    def start_container(self):
        logger.info(f"Starting container {self.container_name}")
        try:
            self.container = self.client.containers.run(
                f"{config.runtime.image_name}:{config.runtime.image_tag}",
                name=self.container_name,
                detach=True,
                stdin_open=True,
                tty=True,
                network=config.runtime.network_name,
                mem_limit=config.runtime.mem_limit,
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