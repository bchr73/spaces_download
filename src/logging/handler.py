import sys
import os
import datetime
import logging

from formatter import file_formatter, console_formatter

def attach_file_handler(logger: logging.Logger, logging_level: int) -> None:

        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d")
        PID = os.getpid()
        _logfile_path = f"boto3_stream_server_log_{timestamp}.{logging.getLevelName(logging_level)}.log"

        file_handler = logging.FileHandler(_logfile_path)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging_level)

        logger.addHandler(file_handler)

def attach_console_handler(logger: logging.Logger, logging_level: int) -> None:

    console_stderr_handler = logging.StreamHandler(sys.stderr)
    console_stderr_handler.setFormatter(console_formatter)
    console_stderr_handler.setLevel(logging_level)
    
    logger.addHandler(console_stderr_handler)