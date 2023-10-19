from datetime import datetime
from pathlib import Path
import pandas as pd
import json
import time

from loggerfactory import LoggerFactory


logger = LoggerFactory.get_logger(__name__)

reports_dir = Path('reports')
reports_dir.mkdir(parents=True, exist_ok=True)

def dump_json_to_file(data: dict, filename: str):
    """Helper to write dict to json."""
    try:
        filename = reports_dir / filename
        with open(filename, 'w') as file:
            json.dump(data, file, indent=2)
        logger.info(f'File {filename} dump success.')
    except Exception as e:
        logger.error(str(e))
        print(data)

def write_to_file(text, filename: str):
    """Helper to write any string to a file"""
    filename = reports_dir / filename
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(str(text))
            logger.info(f'File {filename} write success.')
    except Exception as e:
        logger.error(str(e))
        print(text)

def write_bytes_to_file(bytes_text: bytes, filename: str):
    """
    Helper to write bytes to a file.

    Note: The filename should contain proper extension.
    """
    try:
        filename = reports_dir / filename
        with open(filename, 'wb') as file:
            file.write(bytes_text)
            logger.info(f'File {filename} write success.')
    except Exception as e:
        logger.error(str(e))


def current_milli_time():
    """Returns epoch time in milliseconds."""
    return round(time.time() * 1000)


def save_json_data(data, report_name: str):
    try:
        dump_json_to_file(data, f'{report_name}_{datetime.now().strftime("%m_%d_%Y-%H_%M_%S")}.json')
    except Exception as e:
        logger.exception(e)
        write_to_file(data, f'{report_name}_error')


def generate_xlsx_report(dataframes: dict[str, pd.DataFrame], report_name: str):
    """
    Write the dataframes mapping to a sheet in the report file.

    Note: The filename should contain xlsx extension.
    """
    report_path = reports_dir / report_name
    try:
        with pd.ExcelWriter(report_path, 'openpyxl') as writer:
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        return report_path
    except PermissionError:
        logger.error(f"Unable to access file {report_path}")
    return Path('non_existent_file')
