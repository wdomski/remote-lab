import yaml
from . import logger

log = logger.Logger()

def read_yaml(file_path: str):
    try:
        with open(file_path) as file:
            data_config = file.read()
            config = yaml.load(data_config, Loader=yaml.FullLoader)
        log.info(f"Config loaded from '{file_path}'")
    except FileNotFoundError:
        log.error(f"Cannot load config '{file_path}'")
        return {}
    return config