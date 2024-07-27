from . import yaml

# create a Singleton class
class Configuration:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Configuration, cls).__new__(cls)
        return cls.instance
    
    def load_config(self, config_file: str):
        self._config_file = config_file
        self._config = yaml.read_yaml(self._config_file)
        return self._config
        
    def get_config(self):
        if hasattr(self, '_config'):
            return self._config
        return None

        
