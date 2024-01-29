import logging
import os
import sys
from contextlib import contextmanager


LEVELS = dict(
    CRITICAL=logging.CRITICAL,
    ERROR=logging.ERROR,
    WARNING=logging.WARNING,
    INFO=logging.INFO,
    DEBUG=logging.DEBUG,
    NOTSET=logging.NOTSET,
)


@contextmanager
def logging_context(logger, level):
    log = logging.getLogger(logger)
    lvl = log.getEffectiveLevel()
    log.setLevel(LEVELS.get(level.upper(), "WARN"))
    yield
    log.setLevel(lvl)


class Logger:
    def __init__(self, name="KVS_sagemaker_integration"):
        self.logger = _create_logger(name)

    def get(self):
        return self.logger


def _default_level():
    level = os.getenv("LOG_LEVEL", "WARN")
    return LEVELS.get(level.upper(), "WARN")


def _create_logger(name):
    logger = logging.getLogger(name)
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logger.setLevel(_default_level())
    return logger
