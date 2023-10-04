from pathlib import Path
import json
import time

from my_logging import log_setup
import logging

log_setup()
logger = logging.getLogger(__name__)

responses_dir = Path('responses')

reports_dir = Path('reports')
reports_dir.mkdir(parents=True, exist_ok=True)

def dump_json_to_file(data: dict, filename: Path):
    try:
        filename = reports_dir / filename
        with open(filename, 'w') as file:
            json.dump(data, file, indent=2)
        logger.info(f'File {filename} dump success.')
    except Exception as e:
        logger.error(str(e))
        print(data)

def write_to_file(text, filename: Path):
    filename = reports_dir / filename
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(str(text))
            logger.info(f'File {filename} write success.')
    except Exception as e:
        logger.error(str(e))
        print(text)

def write_bytes_to_file(bytes_text: bytes, filename: Path):
    try:
        filename = reports_dir / filename
        with open(filename, 'wb') as file:
            file.write(bytes_text)
            logger.info(f'File {filename} write success.')
    except Exception as e:
        logger.error(str(e))


def current_milli_time():
    return round(time.time() * 1000)
