import logging
import logging.config
import yaml
from pathlib import Path


package_dir = Path(__file__).parent.absolute()
DEFAULT_LOG_PATH = package_dir.joinpath('logger_config.yml')

class LoggerFactory(object):
    """
    Reusable logger.
    """

    _LOG = None

    @staticmethod
    def __create_logger(name: str, cfg_path: Path, log_level: str):
        """
        A private method that interacts with the python logging module.
        """
        if cfg_path.exists():
            with open(cfg_path, 'rt') as cfg_file:
                try:
                    config = yaml.safe_load(cfg_file.read())
                    logging.config.dictConfig(config)
                except yaml.YAMLError as exc:
                    logging.basicConfig(level=logging.INFO)
                    logging.warning("YAMLError happened: %s", exc)

        LoggerFactory._LOG = logging.getLogger(name)

        if log_level == "INFO":
            LoggerFactory._LOG.setLevel(logging.INFO)
        elif log_level == "ERROR":
            LoggerFactory._LOG.setLevel(logging.ERROR)
        elif log_level == "DEBUG":
            LoggerFactory._LOG.setLevel(logging.DEBUG)

        return LoggerFactory._LOG

    @staticmethod
    def get_logger(
            name: str,
            cfg_path=DEFAULT_LOG_PATH,
            log_level: str=logging.INFO
    ):
        """
        A static method called by other modules to
        initialize logger in their own module.

        Args:
            name (str): Name of the logger.
            cfg_path (Path, Optional): :obj:`Path` of the yaml
            config file for logging
            log_level (Literal['INFO', 'ERROR', 'DEBUG'], Optional):
            Log level to override
        """
        logger = LoggerFactory.__create_logger(name, cfg_path, log_level)

        # return the logger object
        return logger

