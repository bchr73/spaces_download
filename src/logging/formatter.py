import logging
import datetime

class LogFormatterForFiles(logging.Formatter):

    def formatTime(self, record, datefmt=None):
        # timestamps follow ISO 8601 UTC
        date = datetime.datetime.fromtimestamp(record.created).astimezone(datetime.timezone.utc)
        if not datefmt:
            datefmt = "%Y%m%dT%H%M%S.%fZ"
        return date.strftime(datefmt)

file_formatter = LogFormatterForFiles(fmt="%(asctime)22s | %(levelname)8s | %(name)s | %(message)s")

class LogFormatterForConsole(logging.Formatter):

    def formatTime(self, record, datefmt=None):
        # timestamps follow ISO 8601 UTC
        date = datetime.datetime.fromtimestamp(record.created).astimezone(datetime.timezone.utc)
        if not datefmt:
            datefmt = "%Y-%m-%d %H:%M:%S.%fZ"
        return date.strftime(datefmt)

console_formatter = LogFormatterForConsole(fmt="%(asctime)26s | %(levelname).1s | %(name)s | %(message)s")

