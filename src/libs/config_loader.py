import json
import logging
from src.libs.shared_memory import SharedMemory

class ConfigLoader():
    def __init__(self, file_name, shmem: SharedMemory):
        self.shmem = shmem
        self.file_name = file_name

    def load(self):
        try:
            with open(self.file_name) as config_file:
                config: dict = json.load(config_file)
                for attr, value in config.items():
                    self.shmem.write_config(attr, value)
        except Exception as err:
            logging.error(f"(CONFIG) Error reading {self.file_name}: {err}")
