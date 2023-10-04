import logging
import logging.config
import yaml
from pathlib import Path

DEFAULT_LEVEL = logging.DEBUG
package_dir = Path(__file__).parent.absolute()
DEFAULT_LOG_PATH = package_dir.joinpath('logger_config.yml')


def log_setup(log_cfg_path: Path = DEFAULT_LOG_PATH) -> None:
    """
    Initialize custom logging configuration
    """

    if log_cfg_path.exists():
        with open(log_cfg_path, 'rt') as cfg_file:
            try:
                config = yaml.safe_load(cfg_file.read())
                logging.config.dictConfig(config)
            except yaml.YAMLError as exc:
                print(exc)
            except Exception:
                print(
                    'Error loading configuration; Using default configuration'
                )
                logging.basicConfig(level=DEFAULT_LEVEL)
    else:
        logging.basicConfig(level=DEFAULT_LEVEL)
        print('==== Config file for logging not found =====')
        logging.info('Using default configuration')
