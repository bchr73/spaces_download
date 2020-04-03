import logging
import platform

from handler import attach_file_handler, attach_console_handler

def logger_factory(logger_name: str) -> logging.Logger:
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    attach_file_handler(logger, logging.DEBUG)
    attach_file_handler(logger, logging.INFO)
    attach_file_handler(logger, logging.WARNING)

    attach_console_handler(logger, logging.DEBUG)

    return logger

class LoggerMeta(type):
    def __init__(cls, name, bases, attrs, **kwargs) -> None:
        super().__init__(name, bases, attrs)

        # explicit name mangling
        logger_attribute_name = '_' + cls.__name__ + '__logger'
      
        # ignore inheritance from Logger(Base) for logger name in (Derived)
        if len(cls.mro()) > 2:
            logger_name = f'[ {".".join([c.__name__ for c in cls.mro()[-3::-1]])} ]'
        else:
            logger_name = f'[ {str(cls.mro()[-2].__name__)} ]'

        setattr(cls, logger_attribute_name, logger_factory(logger_name))

class Logger(metaclass=LoggerMeta):
    pass