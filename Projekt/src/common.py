import logging


def setup_loggers(logging_level: int):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging_level)
    log_format = '%(threadName)12s:%(levelname)8s %(message)s'
    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(stderr_handler)
    return logger
