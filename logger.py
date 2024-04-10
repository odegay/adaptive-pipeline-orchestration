# logger.py
import logging

def get_logger(name: str):
    # Create a custom logger
    logger = logging.getLogger(name)
    
    # Set the log level you want
    logger.setLevel(logging.DEBUG)

    return logger